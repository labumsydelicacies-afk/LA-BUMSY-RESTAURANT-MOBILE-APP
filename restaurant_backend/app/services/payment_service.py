#=================================#
#      PAYMENT SERVICE             #
#=================================#

"""
Handles all Flutterwave payment operations:
  - Payment initialisation (returns hosted payment link)
  - Payment verification (server-side API call — NEVER trust frontend)
  - Webhook signature validation (HMAC SHA-512)
  - Webhook event dispatching with full idempotency guard

Payment methods enabled: Bank Transfer, Opay only.
Card payments are explicitly excluded via payment_options.
"""

import logging
from datetime import datetime, timezone

import httpx

from app.config import (
    FLUTTERWAVE_BASE_URL,
    FLUTTERWAVE_SECRET_HASH,
    FLUTTERWAVE_SECRET_KEY,
    FRONTEND_URL,
)
from app.db.models import Order, User
from app.services.notification_service import notify_order_created

logger = logging.getLogger(__name__)


# ─── Reference generation ───────────────────────────────────────────────────

def generate_tx_ref(order_id: int) -> str:
    """
    Produces a unique, deterministic transaction reference for a given order.
    Format: order_{order_id}_{unix_milliseconds}
    This is stored on the Order row and used to look up the order on webhook receipt.
    """
    ts = int(datetime.now(timezone.utc).timestamp() * 1000)
    return f"order_{order_id}_{ts}"


# ─── Payment initialisation ─────────────────────────────────────────────────

def initialize_payment(order: Order, user: User, payment_method: str = "banktransfer,opay") -> dict:
    """
    Calls Flutterwave's POST /payments endpoint to create a hosted payment link.

    Payment methods are restricted to:
      - banktransfer  (standard Nigerian bank transfer)
      - opay          (OPay mobile money / wallet)

    Card payments are deliberately NOT listed in payment_options.

    Returns:
        {
            "payment_link": str,  # redirect the user here
            "tx_ref":       str,  # stored on the order for reconciliation
        }

    Raises:
        ValueError: if the Flutterwave API responds with a failure status.
        httpx.HTTPError: on network-level failures.
    """
    tx_ref = generate_tx_ref(order.id)
    callback_url = f"{FRONTEND_URL}/payment/callback"

    payload = {
        "tx_ref": tx_ref,
        "amount": order.total_price,
        "currency": "NGN",
        "redirect_url": callback_url,
        # ── Restrict to selected method only ──────────────────────
        "payment_options": payment_method,
        # ───────────────────────────────────────────────────────────
        "customer": {
            "email": user.email,
        },
        "customizations": {
            "title": "La Bumsy Delicacies",
            "description": f"Payment for Order #{order.id}",
        },
        "meta": {
            "order_id": order.id,
        },
    }

    headers = {
        "Authorization": f"Bearer {FLUTTERWAVE_SECRET_KEY}",
        "Content-Type": "application/json",
    }

    with httpx.Client(timeout=30) as client:
        response = client.post(
            f"{FLUTTERWAVE_BASE_URL}/payments",
            json=payload,
            headers=headers,
        )

    data = response.json()

    if data.get("status") != "success":
        message = data.get("message", "Unknown Flutterwave error")
        logger.error("Flutterwave initialization failed for order #%s: %s", order.id, message)
        raise ValueError(f"Payment initialization failed: {message}")

    payment_link = data["data"]["link"]
    logger.info("Payment initialized for order #%s | tx_ref=%s", order.id, tx_ref)

    return {"payment_link": payment_link, "tx_ref": tx_ref}


# ─── Server-side verification ────────────────────────────────────────────────

def verify_payment(transaction_id: str | int, expected_amount: float) -> dict | None:
    """
    Independently verifies a Flutterwave transaction via their server API.

    IMPORTANT: This is ALWAYS called before accepting a payment — we never
    trust what the frontend or webhook payload claims without server confirmation.

    Checks:
      - data.status == "successful"
      - data.amount >= expected_amount  (in Naira, not kobo)
      - data.currency == "NGN"

    Returns:
        The full Flutterwave transaction data dict on success, or None on failure.
    """
    headers = {
        "Authorization": f"Bearer {FLUTTERWAVE_SECRET_KEY}",
    }

    with httpx.Client(timeout=30) as client:
        response = client.get(
            f"{FLUTTERWAVE_BASE_URL}/transactions/{transaction_id}/verify",
            headers=headers,
        )

    data = response.json()

    if data.get("status") != "success":
        logger.warning("Flutterwave verify returned non-success for tx %s: %s", transaction_id, data)
        return None

    tx_data = data.get("data", {})
    tx_status = tx_data.get("status", "")
    tx_amount = float(tx_data.get("amount", 0))
    tx_currency = tx_data.get("currency", "")

    if tx_status != "successful":
        logger.warning("Transaction %s status is '%s', not 'successful'", transaction_id, tx_status)
        return None

    if tx_currency != "NGN":
        logger.warning("Transaction %s currency mismatch: got %s", transaction_id, tx_currency)
        return None

    # Amount check: Flutterwave returns amounts in Naira (not kobo).
    # We allow a ₦1 tolerance for floating-point rounding.
    if tx_amount < (expected_amount - 1):
        logger.warning(
            "Amount mismatch for tx %s: expected ₦%.2f, got ₦%.2f",
            transaction_id, expected_amount, tx_amount,
        )
        return None

    logger.info("Transaction %s verified successfully | amount=₦%.2f", transaction_id, tx_amount)
    return tx_data


# ─── Webhook signature validation ───────────────────────────────────────────

def validate_webhook_signature(secret_hash_header: str | None) -> bool:
    """
    Flutterwave webhook security uses a shared secret hash, NOT HMAC.

    The value of the 'verif-hash' header sent by Flutterwave must exactly
    equal the FLUTTERWAVE_SECRET_HASH you configured on the dashboard.

    Returns True if valid, False otherwise.
    """
    if not FLUTTERWAVE_SECRET_HASH:
        logger.error("FLUTTERWAVE_SECRET_HASH is not configured — all webhooks will be rejected")
        return False

    if secret_hash_header is None:
        logger.warning("Webhook received without verif-hash header")
        return False

    is_valid = secret_hash_header == FLUTTERWAVE_SECRET_HASH
    if not is_valid:
        logger.warning("Webhook signature mismatch — possible forgery attempt")
    return is_valid


# ─── Webhook event dispatcher ────────────────────────────────────────────────

def handle_webhook(payload: dict, verif_hash: str | None, db) -> dict:
    """
    Processes an incoming Flutterwave webhook event.

    Full processing pipeline:
      1. Validate signature (verif-hash header)
      2. Only handle 'charge.completed' events
      3. Extract transaction_id and tx_ref
      4. Look up the order via payment_reference (tx_ref)
      5. IDEMPOTENCY CHECK — if already paid, return early (no side effects)
      6. Server-side verify the transaction via Flutterwave API
      7. On success: mark payment_status='paid', status='pending', set paid_at
      8. Fire notify_order_created() in the background
      9. On failure: mark payment_status='failed', status='payment_failed'

    Returns a status dict for logging. The route always returns HTTP 200
    regardless of outcome (so Flutterwave does not retry valid events).
    """

    # ── Step 1: Validate signature ───────────────────────────────
    if not validate_webhook_signature(verif_hash):
        return {"processed": False, "reason": "invalid_signature"}

    # ── Step 2: Filter event type ────────────────────────────────
    event = payload.get("event", "")
    if event != "charge.completed":
        logger.info("Ignoring webhook event type: %s", event)
        return {"processed": False, "reason": "ignored_event", "event": event}

    event_data = payload.get("data", {})
    transaction_id = str(event_data.get("id", ""))
    tx_ref = event_data.get("tx_ref", "")

    if not tx_ref:
        logger.warning("Webhook payload missing tx_ref")
        return {"processed": False, "reason": "missing_tx_ref"}

    # ── Step 3: Find the order ───────────────────────────────────
    from app.db.models import Order as OrderModel  # local import avoids circulars
    order = db.query(OrderModel).filter(OrderModel.payment_reference == tx_ref).first()

    if order is None:
        logger.warning("Webhook received for unknown tx_ref: %s", tx_ref)
        return {"processed": False, "reason": "order_not_found", "tx_ref": tx_ref}

    # ── Step 4: IDEMPOTENCY — never double-process ───────────────
    if order.payment_status == "paid":
        logger.info(
            "Duplicate webhook ignored for order #%s (already paid) tx_ref=%s",
            order.id, tx_ref,
        )
        return {"processed": False, "reason": "already_paid", "order_id": order.id}

    # ── Step 5: Server-side verification (DO NOT trust webhook) ──
    tx_data = verify_payment(transaction_id, order.total_price)

    if tx_data is None:
        # Payment failed or amount/currency mismatch
        order.payment_status = "failed"
        order.status = "payment_failed"
        db.commit()
        logger.warning(
            "Payment verification failed for order #%s | tx=%s", order.id, transaction_id
        )
        return {
            "processed": False,
            "reason": "verification_failed",
            "order_id": order.id,
        }

    # ── Step 6: Mark as paid and activate the order ──────────────
    order.payment_status = "paid"
    order.paid_at = datetime.now(timezone.utc)
    order.external_transaction_id = transaction_id
    order.status = "pending"  # now visible to admins for kitchen processing

    db.commit()
    db.refresh(order)

    logger.info(
        "Payment confirmed for order #%s | tx=%s | tx_ref=%s",
        order.id, transaction_id, tx_ref,
    )

    # ── Step 7: Notify admins NOW (payment confirmed) ────────────
    # This is the point where notify_order_created should fire — not at
    # order creation, because admins should only see paid orders.
    user = order.user
    if user:
        try:
            notify_order_created(db, order.id, user.email, order.total_price)
        except Exception:
            # Notification failure must never break the payment confirmation.
            logger.exception(
                "Failed to send order-created notification for order #%s", order.id
            )

    return {
        "processed": True,
        "order_id": order.id,
        "tx_ref": tx_ref,
        "amount_paid": tx_data.get("amount"),
    }
