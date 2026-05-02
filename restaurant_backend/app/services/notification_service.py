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
from app.db.models import Order, User
from app.services.email_verification_service import send_email
from app.services.email_templates import (
    get_standard_notification_html,
    get_delivery_otp_html,
    get_payment_receipt_html
)

logger = logging.getLogger(__name__)


# ─── helpers ────────────────────────────────────────────────────────────────

def _get_all_riders(db: Session) -> list[User]:
    return db.query(User).filter(User.is_rider.is_(True), User.is_email_verified.is_(True)).all()


def _get_all_admins(db: Session) -> list[User]:
    return db.query(User).filter(User.is_admin.is_(True)).all()


def _safe_send(to_email: str, subject: str, body: str, html_body: str | None = None) -> None:
    """Send one email; log failures without raising."""
    try:
        send_email(to_email, subject, body, html_body=html_body)
    except Exception:
        logger.exception("Notification email failed for %s", to_email)


# ─── event: order created ───────────────────────────────────────────────────

def notify_order_created(db: Session, order_id: int, user_email: str, total_price: float) -> None:
    """
    Triggered when a user places a new order (or after payment).
    • Notifies all admins.
    • Notifies all verified riders that a new order is available.
    • Sends a beautiful payment receipt to the user.
    """
    subject = f"New Order #{order_id} received"
    admin_body = (
        f"A new order (#{order_id}) has been placed by {user_email}.\n"
        f"Total: ₦{total_price:,.2f}\n\n"
        "Please log in to the admin dashboard to review and confirm."
    )
    admin_html = get_standard_notification_html(
        f"New Order #{order_id}",
        admin_body
    )

    rider_body = (
        f"A new order (#{order_id}) is available for delivery.\n"
        f"Log in to the rider dashboard to accept it."
    )
    rider_html = get_standard_notification_html(
        "New Delivery Available",
        rider_body
    )

    for admin in _get_all_admins(db):
        _safe_send(admin.email, subject, admin_body, admin_html)

    for rider in _get_all_riders(db):
        _safe_send(rider.email, "New delivery available", rider_body, rider_html)

    # ─── User Receipt ──────────────────────────────────────────────
    order = db.query(Order).filter(Order.id == order_id).first()
    if order and order.items:
        receipt_subject = f"Payment Receipt - Order #{order_id}"
        receipt_body = f"Thank you for your order! Your payment of ₦{total_price:,.2f} has been confirmed."
        receipt_html = get_payment_receipt_html(order_id, total_price, order.items)
        _safe_send(user_email, receipt_subject, receipt_body, receipt_html)

    logger.info("Order-created notifications & receipt sent for order #%s", order_id)


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
    html_body = get_standard_notification_html("Ready for Pickup", body)
    for rider in _get_all_riders(db):
        _safe_send(rider.email, subject, body, html_body)

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
    admin_html = get_standard_notification_html("Order Assigned", admin_body)
    
    user_body = (
        f"Good news! Your order #{order_id} has been assigned to a rider ({rider_nickname}).\n"
        "They will collect it shortly and head your way."
    )
    user_html = get_standard_notification_html("Rider Assigned!", user_body)

    for admin in _get_all_admins(db):
        _safe_send(admin.email, subject, admin_body, admin_html)

    _safe_send(user_email, subject, user_body, user_html)
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
    html_body = get_delivery_otp_html(order_id, otp)
    _safe_send(user_email, subject, body, html_body)
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
    user_html = get_standard_notification_html("Order Delivered!", user_body)
    
    admin_body = f"Order #{order_id} has been delivered and confirmed via OTP."
    admin_html = get_standard_notification_html("Delivery Completed", admin_body)

    _safe_send(user_email, subject, user_body, user_html)
    for admin in _get_all_admins(db):
        _safe_send(admin.email, subject, admin_body, admin_html)

    logger.info("Delivery-complete notifications sent for order #%s", order_id)
