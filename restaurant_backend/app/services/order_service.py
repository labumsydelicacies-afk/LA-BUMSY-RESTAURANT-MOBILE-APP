#================================#
#    ORDER SERVICE LAYER         #
#================================#

"""THIS MODULE HANDLES ALL ORDER-RELATED DATABASE OPERATIONS SUCH AS CREATING, FETCHING, AND UPDATING ORDERS."""

import logging

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.db.models import Food, Order, OrderItem
from app.schemas.order import OrderCreate


# ------------------- Logger Setup ------------------- #
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

# ------------------- VALID STATUSES ------------------- #
VALID_STATUSES = ["pending", "confirmed", "preparing", "ready_for_pickup", "out_for_delivery", "delivered", "cancelled"]


# ------------------- CREATE ------------------- #

def create_order(db: Session, user_id: int, order_data: OrderCreate) -> Order:
    """
    Creates a new order with all its items in a single transaction.
    """
    if not order_data.items:
        raise ValueError("Order must contain at least one item")

    total_price = 0
    order_items = []

    for item in order_data.items:
        if item.quantity <= 0:
            raise ValueError(f"Quantity for food ID {item.food_id} must be greater than 0")

        food = db.query(Food).filter(Food.id == item.food_id).first()

        if not food:
            raise ValueError(f"Food item with ID {item.food_id} not found")

        if not food.is_available:
            raise ValueError(f"Food item '{food.name}' is currently unavailable")

        item_total = food.price * item.quantity
        total_price += item_total

        order_items.append(OrderItem(
            food_id=food.id,
            quantity=item.quantity,
            price=food.price,
        ))

    try:
        new_order = Order(
            user_id=user_id,
            total_price=round(total_price, 2),
            status="pending"
        )

        db.add(new_order)
        db.flush()

        for item in order_items:
            item.order_id = new_order.id
            db.add(item)

        db.commit()
        db.refresh(new_order)

        logger.info(f"Order created : ID {new_order.id} | User {user_id} | Total : ${new_order.total_price}")
        return new_order

    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error while creating order : {e}")
        raise


# ------------------- READ ------------------- #

def get_order_by_id(db: Session, order_id: int) -> Order | None:
    """Fetches a single order by its ID."""
    try:
        return db.query(Order).filter(Order.id == order_id).first()
    except SQLAlchemyError as e:
        logger.error(f"Database error while fetching order by ID : {e}")
        raise


def get_orders_by_user(db: Session, user_id: int, skip: int = 0, limit: int = 50) -> list[Order]:
    """Fetches all orders placed by a specific user."""
    try:
        return db.query(Order).filter(
            Order.user_id == user_id
        ).order_by(Order.id.desc()).offset(skip).limit(limit).all()
    except SQLAlchemyError as e:
        logger.error(f"Database error while fetching orders for user {user_id} : {e}")
        raise


def get_all_orders(db: Session, skip: int = 0, limit: int = 50) -> list[Order]:
    """Fetches all orders. Admin use only."""
    try:
        return db.query(Order).order_by(Order.id.desc()).offset(skip).limit(limit).all()
    except SQLAlchemyError as e:
        logger.error(f"Database error while fetching all orders : {e}")
        raise


def get_orders_by_status(db: Session, status: str, skip: int = 0, limit: int = 50) -> list[Order]:
    """Fetches all orders filtered by status."""
    if status not in VALID_STATUSES:
        raise ValueError(f"Invalid status '{status}'. Must be one of: {VALID_STATUSES}")

    try:
        return db.query(Order).filter(
            Order.status == status
        ).order_by(Order.id.desc()).offset(skip).limit(limit).all()
    except SQLAlchemyError as e:
        logger.error(f"Database error while fetching orders by status : {e}")
        raise


# ------------------- UPDATE ------------------- #

def update_order_status(db: Session, order_id: int, new_status: str) -> Order:
    """Updates the status of an existing order."""
    normalized_status = new_status.lower()

    if normalized_status not in VALID_STATUSES:
        raise ValueError(f"Invalid status '{new_status}'. Must be one of: {VALID_STATUSES}")

    order = get_order_by_id(db, order_id)

    if not order:
        raise ValueError(f"Order with ID {order_id} not found")

    status_flow = ["pending", "confirmed", "preparing", "ready_for_pickup", "out_for_delivery", "delivered", "cancelled"]
    current_status = order.status.lower()
    current_index = status_flow.index(current_status)
    new_index = status_flow.index(normalized_status)

    if new_index < current_index and normalized_status != "cancelled":
        raise ValueError(
            f"Cannot move order status backwards from '{order.status}' to '{new_status}'"
        )

    if normalized_status == "cancelled" and current_status == "delivered":
        raise ValueError("Cannot cancel an order that has already been delivered")

    try:
        old_status = order.status
        order.status = normalized_status

        db.commit()
        db.refresh(order)

        logger.info(f"Order ID {order_id} status updated : {old_status} -> {new_status}")
        return order

    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error while updating order status : {e}")
        raise


# ------------------- DELETE ------------------- #

def cancel_order(db: Session, order_id: int, user_id: int) -> Order:
    """Cancels an order. Only works if order is still pending."""
    order = get_order_by_id(db, order_id)

    if not order:
        raise ValueError(f"Order with ID {order_id} not found")

    if order.user_id != user_id:
        raise ValueError("You are not authorized to cancel this order")

    if order.status in ["preparing", "delivered"]:
        raise ValueError(f"Cannot cancel order - it is already {order.status}")

    if order.status == "cancelled":
        raise ValueError("Order is already cancelled")

    return update_order_status(db, order_id, "cancelled")
