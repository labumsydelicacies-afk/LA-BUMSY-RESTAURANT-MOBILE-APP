#==================================#
#         FOOD ROUTES              #
#==================================#

import logging

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.schemas.food import FoodCreate, FoodResponse, FoodUpdate
from app.db import get_db
from app.services.food_service import (
    create_food,
    get_food_by_id,
    get_all_foods_admin,
    get_all_foods,
    get_food_by_name,
    update_food,
    delete_food,
    toggle_availability,
)
from app.utils.security import get_current_admin_user

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/foods",
    tags=["Foods"]
)


@router.get("/", response_model=list[FoodResponse])
def list_foods(
    skip: int = Query(0, ge=0, le=10_000),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """
    Retrieve all available food items.

    Args:
        skip: Number of items to skip (for pagination)
        limit: Maximum number of items to return (for pagination)
        db: Database session
    """
    try:
        return get_all_foods(db, skip=skip, limit=limit)
    except Exception as exc:
        logger.exception("Unexpected error fetching food items")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch food items",
        ) from exc


@router.get("/admin", response_model=list[FoodResponse])
def list_foods_admin(
    skip: int = Query(0, ge=0, le=10_000),
    limit: int = Query(100, ge=1, le=200),
    db: Session = Depends(get_db),
    _=Depends(get_current_admin_user),
):
    """
    Retrieve all food items including unavailable ones (admin only).

    Args:
        skip: Number of items to skip (for pagination)
        limit: Maximum number of items to return (for pagination)
        db: Database session
    """
    try:
        return get_all_foods_admin(db, skip=skip, limit=limit)
    except Exception as exc:
        logger.exception("Unexpected error fetching admin food items")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch food items",
        ) from exc


@router.get("/{food_id}", response_model=FoodResponse)
def get_food(food_id: int, db: Session = Depends(get_db)):
    """
    Retrieve a food item by its ID.

    Args:
        food_id: ID of the food item
        db: Database session
    """
    try:
        food = get_food_by_id(db, food_id)
        if not food:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Food item not found",
            )
        return food
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Unexpected error fetching food item %s", food_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch food item",
        ) from exc


@router.post("/", response_model=FoodResponse, status_code=status.HTTP_201_CREATED)
def create_food_item(
    food: FoodCreate,
    db: Session = Depends(get_db),
    _=Depends(get_current_admin_user),
):
    """
    Create a new food item (admin only).

    Args:
        food: Food item details including name, price, description and category
        db: Database session
    """
    try:
        existing_food = get_food_by_name(db, food.name)
        if existing_food:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Food item with this name already exists",
            )
        return create_food(db, food)
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Unexpected error creating food item")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create food item",
        ) from exc


@router.put("/{food_id}", response_model=FoodResponse, status_code=status.HTTP_200_OK)
def update_food_item(
    food_id: int,
    food: FoodUpdate,
    db: Session = Depends(get_db),
    _=Depends(get_current_admin_user),
):
    """
    Update an existing food item (admin only).

    Args:
        food_id: ID of the food item to update
        food: Updated fields including name, price, description and category
        db: Database session
    """
    try:
        existing_food = get_food_by_id(db, food_id)
        if not existing_food:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Food item not found",
            )
        return update_food(db, food_id, food)
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Unexpected error updating food item %s", food_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update food item",
        ) from exc


@router.patch("/{food_id}/toggle-availability", response_model=FoodResponse, status_code=status.HTTP_200_OK)
def toggle_food_availability(
    food_id: int,
    db: Session = Depends(get_db),
    _=Depends(get_current_admin_user),
):
    """
    Toggle the availability of a food item (admin only).

    Args:
        food_id: ID of the food item to toggle
        db: Database session
    """
    try:
        existing_food = get_food_by_id(db, food_id)
        if not existing_food:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Food item not found",
            )
        return toggle_availability(db, food_id)
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Unexpected error toggling availability for food item %s", food_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to toggle availability",
        ) from exc


@router.delete("/{food_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_food_item(
    food_id: int,
    db: Session = Depends(get_db),
    _=Depends(get_current_admin_user),
):
    """
    Delete a food item (admin only).

    Args:
        food_id: ID of the food item to delete
        db: Database session
    """
    try:
        existing_food = get_food_by_id(db, food_id)
        if not existing_food:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Food item not found",
            )
        delete_food(db, food_id)
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Unexpected error deleting food item %s", food_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete food item",
        ) from exc
