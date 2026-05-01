#=================================#
#    DELIVERY SERVICE LAYER        #
#=================================#

"""
Handles all delivery lifecycle DB operations:
  - Atomic "first rider wins" order acceptance (race-condition safe)
  - Pickup + OTP generation
  - OTP-verified delivery completion
  - Admin and rider read views

Delivery table is the source of truth for logistics.
Order table is updated in sync via update_order_status().
"""

import hashlib
import logging
import random
from datetime import datetime, timedelta

from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.db.models import Delivery, DeliveryVerification, Order, User
from app.services.order_service import update_order_status

logger = logging.getLogger(__name__)

DELIVERY_OTP_EXPIRY_HOURS = 24


# ─── helpers ────────────────────────────────────────────────────────────────

def _generate_otp(length: int = 6) -> str:
    return "".join(str(random.randint(0, 9)) for _ in range(length))


def _hash_otp(otp: str) -> str:
    return hashlib.sha256(otp.encode()).hexdigest()


# ─── ACCEPT (race-condition safe) ────────────────────────────────────────────

def accept_order(db: Session, order_id: int, rider_id: int) -> Delivery:
    """
    Atomically assigns an order to the first rider who successfully calls this.

    Strategy:
      1. Lock the Order row with SELECT FOR UPDATE.
      2. Verify it has no rider_id yet (still unassigned).
      3. Set order.rider_id and create a Delivery record in the same transaction.
      4. Any concurrent request that passes step 1 will see rider_id already set
         and raise a ValueError — handled gracefully by the route.

    Raises:
        ValueError: if order not found, wrong status, or already claimed.
    """
    try:
        # Lock the row so concurrent requests queue behind this one.
        order = (
            db.query(Order)
            .filter(Order.id == order_id)
            .with_for_update()
            .first()
        )

        if order is None:
            raise ValueError(f"Order #{order_id} not found")

        if order.status not in ("ready_for_pickup",):
            raise ValueError(
                f"Order #{order_id} is not ready for pickup (current status: {order.status})"
            )

        if order.rider_id is not None:
            raise ValueError("This order has already been claimed by another rider")

        # Claim the order
        order.rider_id = rider_id

        delivery = Delivery(
            order_id=order_id,
            rider_id=rider_id,
            assigned_at=datetime.now(),
        )
        db.add(delivery)
        db.flush()   # surface UniqueConstraint violations before commit
        db.commit()
        db.refresh(delivery)

        logger.info("Order #%s accepted by rider #%s", order_id, rider_id)
        return delivery

    except IntegrityError:
        db.rollback()
        raise ValueError("This order has already been claimed by another rider")
    except SQLAlchemyError as exc:
        db.rollback()
        logger.error("DB error accepting order #%s: %s", order_id, exc)
        raise


# ─── PICKUP (generates delivery OTP for the user) ───────────────────────────

def mark_picked_up(db: Session, order_id: int, rider_id: int) -> tuple[Delivery, str]:
    """
    Rider marks the order as picked up.
    - Advances order status to out_for_delivery.
    - Generates a single-use 24-hour OTP stored in DeliveryVerification.
    - Returns (delivery, plain_otp) — caller queues email notification.

    Raises:
        ValueError: if delivery not found, already picked up, or rider mismatch.
    """
    delivery = (
        db.query(Delivery)
        .filter(Delivery.order_id == order_id, Delivery.rider_id == rider_id)
        .first()
    )
    if delivery is None:
        raise ValueError("Delivery record not found or you are not the assigned rider")

    if delivery.picked_up_at is not None:
        raise ValueError("Order has already been marked as picked up")

    # Advance order status
    update_order_status(db, order_id, "out_for_delivery")

    # Generate OTP
    otp = _generate_otp()

    # Remove old verification if any (idempotent retry safety)
    db.query(DeliveryVerification).filter(
        DeliveryVerification.order_id == order_id
    ).delete(synchronize_session=False)

    verification = DeliveryVerification(
        order_id=order_id,
        otp_hash=otp,
        expires_at=datetime.now() + timedelta(hours=DELIVERY_OTP_EXPIRY_HOURS),
        is_used=False,
        created_at=datetime.now(),
    )
    db.add(verification)

    delivery.picked_up_at = datetime.now()
    db.commit()
    db.refresh(delivery)

    logger.info("Order #%s picked up by rider #%s; OTP generated", order_id, rider_id)
    return delivery, otp


# ─── COMPLETE (OTP verification by rider) ───────────────────────────────────

def complete_delivery(db: Session, order_id: int, rider_id: int, otp: str) -> Delivery:
    """
    Rider submits the OTP the user received to confirm delivery.
    - Verifies OTP is valid, unexpired, and unused.
    - Marks delivery as delivered and syncs order status to delivered.

    Raises:
        ValueError: for invalid OTP, wrong rider, or already delivered.
    """
    delivery = (
        db.query(Delivery)
        .filter(Delivery.order_id == order_id, Delivery.rider_id == rider_id)
        .first()
    )
    if delivery is None:
        raise ValueError("Delivery record not found or you are not the assigned rider")

    if delivery.delivered_at is not None:
        raise ValueError("This order has already been delivered")

    verification = (
        db.query(DeliveryVerification)
        .filter(DeliveryVerification.order_id == order_id)
        .first()
    )
    if verification is None:
        raise ValueError("No delivery OTP found for this order")

    if verification.is_used:
        raise ValueError("OTP has already been used")

    if verification.expires_at < datetime.now():
        raise ValueError("OTP has expired")

    if verification.otp_hash != otp:
        raise ValueError("Invalid OTP")

    # Consume OTP
    verification.is_used = True

    # Finalize delivery
    delivery.delivered_at = datetime.now()

    # Sync order status
    update_order_status(db, order_id, "delivered")

    db.commit()
    db.refresh(delivery)

    logger.info("Order #%s delivery confirmed by rider #%s via OTP", order_id, rider_id)
    return delivery


# ─── READ: rider view ────────────────────────────────────────────────────────

def get_my_deliveries(db: Session, rider_id: int) -> list[Delivery]:
    """Returns all deliveries assigned to the calling rider."""
    return (
        db.query(Delivery)
        .filter(Delivery.rider_id == rider_id)
        .order_by(Delivery.assigned_at.desc())
        .all()
    )


def get_available_orders(db: Session) -> list[Order]:
    """
    Returns orders that are ready_for_pickup and not yet claimed.
    Rider dashboard polls this to show the accept button.
    """
    return (
        db.query(Order)
        .filter(Order.status == "ready_for_pickup", Order.rider_id.is_(None))
        .order_by(Order.created_at.asc())
        .all()
    )


# ─── READ: admin view ────────────────────────────────────────────────────────

def get_all_deliveries(db: Session, skip: int = 0, limit: int = 50) -> list[Delivery]:
    """Returns all deliveries for admin visibility."""
    return (
        db.query(Delivery)
        .order_by(Delivery.assigned_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_delivery_by_order(db: Session, order_id: int) -> Delivery | None:
    return db.query(Delivery).filter(Delivery.order_id == order_id).first()
