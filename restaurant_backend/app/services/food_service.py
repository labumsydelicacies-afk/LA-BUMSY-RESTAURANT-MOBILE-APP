#================================#
#    FOOD SERVICE LAYER          #
#================================#

"""THIS MODULE HANDLES ALL FOOD-RELATED DATABASE OPERATIONS SUCH AS CREATING, FETCHING, UPDATING, AND DELETING FOOD ITEMS."""

import logging

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.db.models import Food
from app.schemas.food import FoodCreate, FoodUpdate


# ------------------- Logger Setup ------------------- #
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)


# ------------------- CREATE ------------------- #

def create_food(db: Session, food_data: FoodCreate) -> Food:
    """
    Creates a new food item in the database.

    Args:
        db        : Database session
        food_data : Pydantic schema containing food details

    Returns:
        Newly created Food object

    Raises:
        ValueError      : If a food item with the same name already exists
        SQLAlchemyError : If database operation fails
    """
    if not food_data.name:
        raise ValueError("Food name is required")

    if food_data.price <= 0:
        raise ValueError("Food price must be greater than 0")

    existing_food = get_food_by_name(db, food_data.name)
    if existing_food:
        raise ValueError(f"Food item '{food_data.name}' already exists")

    try:
        new_food = Food(**food_data.model_dump())
        db.add(new_food)
        db.commit()
        db.refresh(new_food)
        logger.info(f"Food item created : {new_food.name} | Price : ${new_food.price}")
        return new_food
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error while creating food item : {e}")
        raise


# ------------------- READ ------------------- #

def get_all_foods(db: Session, skip: int = 0, limit: int = 100) -> list[Food]:
    """Fetches all available food items with pagination."""
    try:
        return db.query(Food).filter(
            Food.is_available == True
        ).offset(skip).limit(limit).all()
    except SQLAlchemyError as e:
        logger.error(f"Database error while fetching all foods : {e}")
        raise


def get_all_foods_admin(db: Session, skip: int = 0, limit: int = 100) -> list[Food]:
    """Fetches all food items including unavailable ones."""
    try:
        return db.query(Food).offset(skip).limit(limit).all()
    except SQLAlchemyError as e:
        logger.error(f"Database error while fetching all foods (admin) : {e}")
        raise


def get_food_by_id(db: Session, food_id: int) -> Food | None:
    """Fetches a single food item by its ID."""
    try:
        return db.query(Food).filter(Food.id == food_id).first()
    except SQLAlchemyError as e:
        logger.error(f"Database error while fetching food by ID : {e}")
        raise


def get_food_by_name(db: Session, name: str) -> Food | None:
    """Fetches a single food item by its name."""
    try:
        return db.query(Food).filter(Food.name == name).first()
    except SQLAlchemyError as e:
        logger.error(f"Database error while fetching food by name : {e}")
        raise


# ------------------- UPDATE ------------------- #

def update_food(db: Session, food_id: int, food_data: FoodUpdate) -> Food:
    """Updates an existing food item."""
    food = get_food_by_id(db, food_id)

    if not food:
        raise ValueError(f"Food item with ID {food_id} not found")

    if food_data.price is not None and food_data.price <= 0:
        raise ValueError("Food price must be greater than 0")

    try:
        update_data = food_data.model_dump(exclude_unset=True)

        for key, value in update_data.items():
            setattr(food, key, value)

        db.commit()
        db.refresh(food)
        logger.info(f"Food item updated : ID {food_id} | {update_data}")
        return food
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error while updating food item : {e}")
        raise


def toggle_availability(db: Session, food_id: int) -> Food:
    """Toggles the availability of a food item on or off."""
    food = get_food_by_id(db, food_id)

    if not food:
        raise ValueError(f"Food item with ID {food_id} not found")

    try:
        food.is_available = not food.is_available
        db.commit()
        db.refresh(food)
        logger.info(f"Food availability toggled : {food.name} | Available : {food.is_available}")
        return food
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error while toggling food availability : {e}")
        raise


# ------------------- DELETE ------------------- #

def delete_food(db: Session, food_id: int) -> bool:
    """Deletes a food item from the database."""
    food = get_food_by_id(db, food_id)

    if not food:
        raise ValueError(f"Food item with ID {food_id} not found")

    try:
        db.delete(food)
        db.commit()
        logger.info(f"Food item deleted : ID {food_id} | {food.name}")
        return True
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error while deleting food item : {e}")
        raise
