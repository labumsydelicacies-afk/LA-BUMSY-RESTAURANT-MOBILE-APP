#==================================#
#         PAYMENT ROUTES            #
#==================================#

"""
Payment endpoints for Flutterwave integration.

Routes:
  POST /payments/initialize  \u2500 Authenticated. Creates a Flutterwave payment session.
  POST /payments/webhook     \u2500 Public (no JWT). Receives Flutterwave events.
  GET  /payments/verify/{tx} \u2500 Authenticated. Manual fallback verification on return.

Security notes:
  - The webhook endpoint has NO JWT auth. It is secured exclusively via the
    verif-hash header (FLUTTERWAVE_SECRET_HASH). Never add JWT to webhooks.
  - Payment confirmation is ALWAYS server-validated via Flutterwave's verify
    API before any order state is updated.
"""

import logging

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db import get_db
from app.db.models import Order
from app.services.payment_service import handle_webhook, initialize_payment, verify_payment
from app.utils.security import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/payments", tags=["Payments"])


# ─── Request / Response schemas ──────────────────────────────────────────────

class InitializePaymentRequest(BaseModel):
    order_id: int
    payment_options: str = "card,banktransfer"


class InitializePaymentResponse(BaseModel):
    payment_link: str
    tx_ref: str
    order_id: int


class VerifyPaymentResponse(BaseModel):
    paid: bool
    order_id: int | None = None
    amount: float | None = None


# ─── POST /payments/initialize ───────────────────────────────────────────────

@router.post(
    "/initialize",
    response_model=InitializePaymentResponse,
    status_code=status.HTTP_200_OK,
)
def initialize(
    body: InitializePaymentRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Creates a Flutterwave hosted payment session for an existing order.

    Validation:
      - The order must exist and belong to the calling user.
      - The order must not already be paid (payment_status != 'paid').

    Returns:
      payment_link \u2014 redirect the user to this URL immediately.
      tx_ref       \u2014 stored on the order for webhook reconciliation.
    """
    order = db.query(Order).filter(Order.id == body.order_id).first()

    if order is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order #{body.order_id} not found",
        )

    if order.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to pay for this order",
        )

    if order.payment_status == "paid":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This order has already been paid for",
        )

    try:
        result = initialize_payment(order, current_user, body.payment_options)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc

    # Persist the tx_ref on the order so the webhook can find it later.
    order.payment_reference = result["tx_ref"]
    if result.get("charge_id"):
        order.external_transaction_id = str(result["charge_id"])
    db.commit()

    logger.info(
        "Payment initialized for order #%s by user #%s | tx_ref=%s",
        order.id, current_user.id, result["tx_ref"],
    )

    return InitializePaymentResponse(
        payment_link=result["payment_link"],
        tx_ref=result["tx_ref"],
        order_id=order.id,
    )


# ─── POST /payments/webhook ──────────────────────────────────────────────────

@router.post("/webhook", status_code=status.HTTP_200_OK)
async def webhook(
    request: Request,
    db: Session = Depends(get_db),
    verif_hash: str | None = Header(None, alias="verif-hash"),
):
    """
    Receives Flutterwave webhook events.

    Security:
      - No JWT auth \u2014 this endpoint is called by Flutterwave's servers, not users.
      - Secured via verif-hash header matching FLUTTERWAVE_SECRET_HASH.
      - Always returns HTTP 200 so Flutterwave does not retry valid events.

    Processing:
      - Validates signature first.
      - Only processes 'charge.completed' events.
      - Idempotency: if order.payment_status == 'paid', silently ignores.
      - Server-verifies via Flutterwave API before updating any state.
    """
    try:
        payload = await request.json()
    except Exception:
        # Malformed body \u2014 still return 200 to avoid Flutterwave retry storms.
        logger.warning("Webhook received non-JSON body")
        return {"status": "ignored", "reason": "invalid_body"}

    result = handle_webhook(payload, verif_hash, db)
    return {"status": "received", "detail": result}


# ─── GET /payments/verify/{transaction_id} ───────────────────────────────────

@router.get(
    "/verify/{transaction_id}",
    response_model=VerifyPaymentResponse,
    status_code=status.HTTP_200_OK,
)
def verify(
    transaction_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Manual payment verification fallback.

    Called by the frontend on the /payment/callback page after the user
    returns from Flutterwave. The webhook is the primary confirmation path,
    but this covers cases where the webhook hasn't fired yet or was delayed.

    Flow:
      1. Find the order that has this transaction_id as external_transaction_id,
         OR find via the tx_ref stored in payment_reference.
      2. If already marked paid \u2014 return success immediately (idempotent).
      3. Otherwise call Flutterwave verify API.
      4. If confirmed: update order state and trigger notifications.
    """
    # First check if we already have this confirmed in the database.
    order = db.query(Order).filter(
        Order.external_transaction_id == transaction_id,
        Order.user_id == current_user.id,
    ).first()

    if order is None:
        # Also check by payment_reference (tx_ref), which may match when
        # the webhook hasn't fired yet but the user returned from payment page.
        order = db.query(Order).filter(
            Order.payment_reference.like(f"order_%"),
            Order.user_id == current_user.id,
            Order.payment_status != "paid",
        ).order_by(Order.created_at.desc()).first()

    if order is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No order found for this transaction",
        )

    # Idempotency: already confirmed
    if order.payment_status == "paid":
        return VerifyPaymentResponse(paid=True, order_id=order.id)

    # Server-side verification
    tx_data = verify_payment(transaction_id, order.total_price)

    if tx_data is None:
        return VerifyPaymentResponse(paid=False, order_id=order.id)

    # Confirm payment
    from datetime import datetime, timezone
    order.payment_status = "paid"
    order.paid_at = datetime.now(timezone.utc)
    order.external_transaction_id = transaction_id
    order.status = "pending"
    db.commit()
    db.refresh(order)

    # We rely entirely on the webhook to send notifications and emails
    # to avoid duplicate receipts and premature emails.

    return VerifyPaymentResponse(
        paid=True,
        order_id=order.id,
        amount=tx_data.get("amount"),
    )
