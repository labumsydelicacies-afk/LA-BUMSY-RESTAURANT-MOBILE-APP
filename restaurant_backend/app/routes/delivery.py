#=================================#
#        DELIVERY ROUTES           #
#=================================#

import logging

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas.delivery import (
    DeliveryAcceptRequest,
    DeliveryCompleteRequest,
    DeliveryResponse,
    DeliveryWithOrderResponse,
    AvailableOrderResponse,
)
from app.schemas.order import OrderResponse
from app.services.delivery_service import (
    accept_order,
    complete_delivery,
    get_all_deliveries,
    get_available_orders,
    get_delivery_by_order,
    get_my_deliveries,
    mark_picked_up,
)
from app.services.notification_service import (
    notify_order_assigned,
    notify_order_delivered,
    notify_picked_up_otp,
)
from app.utils.security import get_current_admin_user, get_current_rider_user, get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/delivery", tags=["Delivery"])


# ──────────────────────────────────────────────────────────────────────────────
# RIDER ENDPOINTS
# ──────────────────────────────────────────────────────────────────────────────

@router.get("/available", response_model=list[AvailableOrderResponse])
def list_available_orders(
    db: Session = Depends(get_db),
    current_rider=Depends(get_current_rider_user),
):
    """
    Returns all orders with status=ready_for_pickup and no assigned rider.
    Riders poll this to see what they can accept.
    """
    return get_available_orders(db)


@router.post("/accept", response_model=DeliveryResponse, status_code=status.HTTP_201_CREATED)
def accept_delivery(
    payload: DeliveryAcceptRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_rider=Depends(get_current_rider_user),
):
    """
    First-rider-wins atomic acceptance.
    Concurrent requests are safe: only one will succeed.
    """
    try:
        delivery = accept_order(db, payload.order_id, current_rider.id)

        # Notify admin + user that a rider has been assigned
        order = delivery.order
        user_email = order.user.email if order and order.user else None
        if user_email:
            background_tasks.add_task(
                notify_order_assigned,
                db,
                payload.order_id,
                current_rider.nickname,
                user_email,
            )

        return delivery
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Unexpected error accepting order #%s", payload.order_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to accept order",
        ) from exc


@router.patch("/pickup/{order_id}", response_model=DeliveryResponse)
def pickup_order(
    order_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_rider=Depends(get_current_rider_user),
):
    """
    Rider confirms they have picked up the order.
    - Advances order to out_for_delivery.
    - Generates a delivery OTP and sends it to the USER ONLY via email.
    The rider never sees the OTP.
    """
    try:
        delivery, otp = mark_picked_up(db, order_id, current_rider.id)

        # Get user email from the associated order
        order = delivery.order
        user_email = order.user.email if order and order.user else None
        if user_email:
            background_tasks.add_task(notify_picked_up_otp, user_email, order_id, otp)

        return delivery
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Unexpected error on pickup for order #%s", order_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to mark order as picked up",
        ) from exc


@router.post("/complete", response_model=DeliveryResponse)
def complete_order_delivery(
    payload: DeliveryCompleteRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_rider=Depends(get_current_rider_user),
):
    """
    Rider submits the OTP the customer received to complete the delivery.
    OTP is verified server-side; rider never sees the OTP value in any response.
    On success: order is marked DELIVERED and notifications are sent.
    """
    try:
        delivery = complete_delivery(db, payload.order_id, current_rider.id, payload.otp)

        order = delivery.order
        user_email = order.user.email if order and order.user else None
        if user_email:
            background_tasks.add_task(
                notify_order_delivered, db, payload.order_id, user_email
            )

        return delivery
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Unexpected error completing order #%s", payload.order_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to complete delivery",
        ) from exc


@router.get("/my-deliveries", response_model=list[DeliveryResponse])
def my_deliveries(
    db: Session = Depends(get_db),
    current_rider=Depends(get_current_rider_user),
):
    """Returns all deliveries assigned to the calling rider."""
    return get_my_deliveries(db, current_rider.id)


# ──────────────────────────────────────────────────────────────────────────────
# ADMIN ENDPOINTS
# ──────────────────────────────────────────────────────────────────────────────

@router.get("/all", response_model=list[DeliveryResponse])
def all_deliveries(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    _=Depends(get_current_admin_user),
):
    """Admin: view all delivery records with pagination."""
    return get_all_deliveries(db, skip=skip, limit=limit)


@router.get("/order/{order_id}", response_model=DeliveryResponse)
def delivery_for_order(
    order_id: int,
    db: Session = Depends(get_db),
    _=Depends(get_current_admin_user),
):
    """Admin: view the delivery record for a specific order."""
    delivery = get_delivery_by_order(db, order_id)
    if delivery is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No delivery record found for order #{order_id}",
        )
    return delivery
