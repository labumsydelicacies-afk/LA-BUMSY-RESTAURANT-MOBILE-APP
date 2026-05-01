#=================================#
#    NOTIFICATION SERVICE          #
#=================================#

"""
Handles all transactional emails triggered by delivery lifecycle events.
Reuses the existing SMTP send_email infrastructure from email_verification_service.
All functions are fire-and-forget: run them via BackgroundTasks.
"""

import logging

from sqlalchemy.orm import Session

from app.config import SMTP_EMAIL
from app.db.models import User
from app.services.email_verification_service import send_email

logger = logging.getLogger(__name__)


# ─── helpers ────────────────────────────────────────────────────────────────

def _get_all_riders(db: Session) -> list[User]:
    return db.query(User).filter(User.is_rider.is_(True), User.is_verified.is_(True)).all()


def _get_all_admins(db: Session) -> list[User]:
    return db.query(User).filter(User.is_admin.is_(True)).all()


def _safe_send(to_email: str, subject: str, body: str) -> None:
    """Send one email; log failures without raising."""
    try:
        send_email(to_email, subject, body)
    except Exception:
        logger.exception("Notification email failed for %s", to_email)


# ─── event: order created ───────────────────────────────────────────────────

def notify_order_created(db: Session, order_id: int, user_email: str, total_price: float) -> None:
    """
    Triggered when a user places a new order.
    • Notifies all admins.
    • Notifies all verified riders that a new order is available.
    """
    subject = f"New Order #{order_id} received"
    admin_body = (
        f"A new order (#{order_id}) has been placed by {user_email}.\n"
        f"Total: ₦{total_price:,.2f}\n\n"
        "Please log in to the admin dashboard to review and confirm."
    )
    rider_body = (
        f"A new order (#{order_id}) is available for delivery.\n"
        f"Log in to the rider dashboard to accept it."
    )

    for admin in _get_all_admins(db):
        _safe_send(admin.email, subject, admin_body)

    for rider in _get_all_riders(db):
        _safe_send(rider.email, "New delivery available", rider_body)

    logger.info("Order-created notifications sent for order #%s", order_id)


# ─── event: order ready for pickup ──────────────────────────────────────────

def notify_ready_for_pickup(db: Session, order_id: int) -> None:
    """
    Triggered when admin moves order to ready_for_pickup.
    Sends a reminder to all verified riders.
    """
    subject = f"Order #{order_id} is ready for pickup"
    body = (
        f"Order #{order_id} has been prepared and is ready for pickup.\n"
        "Log in to the rider dashboard to accept and collect."
    )
    for rider in _get_all_riders(db):
        _safe_send(rider.email, subject, body)

    logger.info("Ready-for-pickup notifications sent for order #%s", order_id)


# ─── event: order assigned to rider ─────────────────────────────────────────

def notify_order_assigned(
    db: Session,
    order_id: int,
    rider_nickname: str,
    user_email: str,
) -> None:
    """
    Triggered when a rider accepts an order.
    • Notifies all admins.
    • Notifies the customer that a rider has been assigned.
    """
    subject = f"Order #{order_id} assigned to a rider"

    admin_body = (
        f"Order #{order_id} has been accepted by rider '{rider_nickname}'.\n"
        "The order is now out for collection."
    )
    user_body = (
        f"Good news! Your order #{order_id} has been assigned to a rider ({rider_nickname}).\n"
        "They will collect it shortly and head your way."
    )

    for admin in _get_all_admins(db):
        _safe_send(admin.email, subject, admin_body)

    _safe_send(user_email, subject, user_body)
    logger.info("Order-assigned notifications sent for order #%s", order_id)


# ─── event: picked up — OTP sent to user ────────────────────────────────────

def notify_picked_up_otp(user_email: str, order_id: int, otp: str) -> None:
    """
    Triggered when rider marks the order as picked up.
    Sends the delivery OTP to the CUSTOMER ONLY.
    The rider NEVER receives or sees this OTP.
    OTP expires in 24 hours.
    """
    subject = f"Your delivery code for Order #{order_id}"
    body = (
        f"Your order #{order_id} has been picked up and is on the way!\n\n"
        f"Your delivery verification code is: {otp}\n\n"
        "Give this code to the rider when they arrive to confirm delivery.\n"
        "This code expires in 24 hours and can only be used once."
    )
    _safe_send(user_email, subject, body)
    logger.info("Delivery OTP sent to user for order #%s", order_id)


# ─── event: order delivered ─────────────────────────────────────────────────

def notify_order_delivered(db: Session, order_id: int, user_email: str) -> None:
    """
    Triggered when OTP is verified and delivery is confirmed.
    Notifies admin and customer.
    """
    subject = f"Order #{order_id} delivered successfully"

    user_body = (
        f"Your order #{order_id} has been delivered. Enjoy your meal!\n"
        "Thank you for ordering from La Bumsy Delicacies."
    )
    admin_body = f"Order #{order_id} has been delivered and confirmed via OTP."

    _safe_send(user_email, subject, user_body)
    for admin in _get_all_admins(db):
        _safe_send(admin.email, subject, admin_body)

    logger.info("Delivery-complete notifications sent for order #%s", order_id)
