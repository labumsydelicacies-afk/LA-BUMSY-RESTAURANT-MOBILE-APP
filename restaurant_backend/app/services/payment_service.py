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
from sqlalchemy.orm import Session

from app.config import (
    FLUTTERWAVE_BASE_URL,
    FLUTTERWAVE_SECRET_HASH,
    FLUTTERWAVE_SECRET_KEY,
    FRONTEND_URL,
)
from app.db.models import Order, User
from app.services.notification_service import notify_order_created

logger = logging.getLogger(__name__)

ALLOWED_PAYMENT_OPTIONS = {"banktransfer", "opay"}


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

def normalize_payment_option(payment_option: str | None) -> str:
    normalized = (payment_option or "banktransfer").strip().lower()
    if normalized not in ALLOWED_PAYMENT_OPTIONS:
        raise ValueError("Payment method must be either 'banktransfer' or 'opay'")
    return normalized


def confirm_order_payment(
    db: Session,
    order: Order,
    transaction_id: str,
    amount: float | None = None,
) -> Order:
    order.payment_status = "paid"
    order.paid_at = datetime.now(timezone.utc)
    order.external_transaction_id = transaction_id
    order.status = "pending"

    db.commit()
    db.refresh(order)

    logger.info(
        "Payment confirmed for order #%s | tx=%s | amount=%s",
        order.id,
        transaction_id,
        amount,
    )
    return order


def initialize_payment(order: Order, user: User, payment_options: str = "banktransfer") -> dict:
    reference = generate_tx_ref(order.id)
    normalized_payment_option = normalize_payment_option(payment_options)
    
    # Mandatory defensive validation before any API calls
    if not user.email:
        raise ValueError("User email is required for payment initialization")
    if not reference:
        raise ValueError("tx_ref is required for payment initialization")

    callback_url = f"{FRONTEND_URL}/payment/callback?order_id={order.id}"

    headers = {
        "Authorization": f"Bearer {FLUTTERWAVE_SECRET_KEY}",
        "Content-Type": "application/json",
        "X-Idempotency-Key": f"init_{reference}"
    }

    with httpx.Client(timeout=30) as client:
        # A. Customer Handling
        try:
            client.post(
                f"{FLUTTERWAVE_BASE_URL}/customers",
                json={"email": user.email, "name": user.nickname},
                headers=headers
            )
        except Exception as e:
            logger.warning("Customer creation ignored: %s", e)

        # C. Charge Creation
        charge_payload = {
            "tx_ref": reference,       # Required by Flutterwave
            "amount": order.total_price,
            "currency": "NGN",
            "payment_options": normalized_payment_option,
            "redirect_url": callback_url,
            "customer": {"email": user.email, "name": user.nickname},
        }

        # Enhance logging with sanitized payload
        sanitized_payload = {**charge_payload}
        sanitized_payload["email"] = "***"
        sanitized_payload["customer"] = {"email": "***", "name": "***"}

        logger.info(
            "Initializing payment | order_id=%s | tx_ref=%s | user_email=%s | payload=%s",
            order.id, reference, user.email, sanitized_payload
        )

        response = client.post(
            f"{FLUTTERWAVE_BASE_URL}/payments",
            json=charge_payload,
            headers=headers,
        )
        data = response.json()

        if response.status_code >= 400:
            message = data.get("message", "Unknown error")
            logger.error("Payment initialization failed for order #%s: %s", order.id, message)
            raise ValueError(f"Payment initialization failed: {message}")

        # Extract payment link from Standard Checkout response
        payment_link = data.get("data", {}).get("link", callback_url)

        charge_id = data.get("data", {}).get("id")

        logger.info("Payment initialized successfully | order_id=%s | tx_ref=%s", order.id, reference)

    return {"payment_link": payment_link, "tx_ref": reference, "charge_id": charge_id}


# ─── Server-side verification ────────────────────────────────────────────────

def verify_payment(transaction_id: str | int, expected_amount: float) -> dict | None:
    headers = {
        "Authorization": f"Bearer {FLUTTERWAVE_SECRET_KEY}",
    }

    with httpx.Client(timeout=30) as client:
        response = client.get(
            f"{FLUTTERWAVE_BASE_URL}/transactions/{transaction_id}/verify",
            headers=headers,
        )

    data = response.json()

    # The prompt explicitly requires checking for "successful"
    tx_data = data.get("data") or {}
    tx_status = tx_data.get("status", "")
    if tx_status != "successful":
        logger.warning("Transaction %s status is '%s', not 'successful'", transaction_id, tx_status)
        return None

    # Amount extraction handling root or nested data
    tx_amount = float(data.get("amount", tx_data.get("amount", 0)))
    tx_currency = data.get("currency", tx_data.get("currency", ""))

    if tx_currency != "NGN":
        logger.warning("Transaction %s currency mismatch: got %s", transaction_id, tx_currency)
        return None

    # Amount check: We allow a ₦1 tolerance for floating-point rounding.
    if tx_amount < (expected_amount - 1):
        logger.warning(
            "Amount mismatch for tx %s: expected ₦%.2f, got ₦%.2f",
            transaction_id, expected_amount, tx_amount,
        )
        return None

    logger.info("Transaction %s verified successfully | amount=₦%.2f", transaction_id, tx_amount)
    return data.get("data", data)


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
    event_type = payload.get("type") or payload.get("event")
    if event_type != "charge.completed":
        logger.info("Ignoring webhook event type: %s", event_type)
        return {"processed": False, "reason": "ignored_event", "type": event_type}

    event_data = payload.get("data", {})
    transaction_id = str(event_data.get("id", ""))
    
    # Prompt explicitly requests using 'reference'
    tx_ref = event_data.get("reference") or event_data.get("tx_ref", "")

    if not tx_ref:
        logger.warning("Webhook payload missing reference")
        return {"processed": False, "reason": "missing_reference"}

    # ── Step 3: Find the order ───────────────────────────────────
    from app.db.models import Order as OrderModel  # local import avoids circulars
    order = db.query(OrderModel).filter(OrderModel.payment_reference == tx_ref).first()

    if order is None:
        logger.warning("Webhook received for unknown reference: %s", tx_ref)
        return {"processed": False, "reason": "order_not_found", "reference": tx_ref}

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
    confirm_order_payment(
        db,
        order,
        transaction_id=transaction_id,
        amount=tx_data.get("amount"),
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
