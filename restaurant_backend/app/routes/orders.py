#==================================#
#         ORDER ROUTES             #
#==================================#

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.schemas.order import OrderCreate, OrderResponse, OrderStatusUpdate
from app.services.order_service import create_order
from app.db import get_db
from app.utils.security import get_current_admin_user, get_current_user
from app.services.order_service import get_all_orders, get_orders_by_user, update_order_status


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/orders", tags=["Orders"])


@router.post("/", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
def place_order(
    order_data: OrderCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """
    Place a new order for the currently authenticated user.

    Args:
        order_data: Order details including items and quantities
        db: Database session
        current_user: Currently authenticated user extracted from JWT
    """
    try:
        return create_order(db, current_user.id, order_data)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        logger.exception("Unexpected error placing order for user %s", current_user.id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to place order",
        ) from exc



@router.get("/", response_model=list[OrderResponse])
def get_orders(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """
    Get all orders for the currently authenticated user.
    If the user is an admin or rider, they might need different routes or parameters.
    For now, return orders belonging to current_user.
    """    
    try:
        if getattr(current_user, "is_admin", False):
            # Admins/riders might need all orders
            return get_all_orders(db)
        return get_orders_by_user(db, current_user.id)
    except Exception as exc:
        logger.exception("Failed to fetch orders for user %s", current_user.id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch orders",
        ) from exc


@router.patch("/{order_id}/status", response_model=OrderResponse)
def update_status(
    order_id: int,
    payload: OrderStatusUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user),
):
    """
    Update an order status.
    Restricted to admin users.
    """
    try:
        return update_order_status(db, order_id, payload.status)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        logger.exception(
            "Failed to update status for order %s by admin %s",
            order_id,
            current_user.id,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update order status",
        ) from exc