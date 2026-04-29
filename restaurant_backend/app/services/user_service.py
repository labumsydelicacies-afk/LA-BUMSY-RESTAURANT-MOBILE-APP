#================================#
#    USER SERVICE LAYER          #
#================================#

"""THIS MODULE HANDLES ALL USER-RELATED DATABASE OPERATIONS SUCH AS CREATING, FETCHING, AND DELETING USERS."""

import logging

from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.db.models import User
from app.schemas.user import UserCreate
from app.utils.security import hash_password


# ------------------- Logger Setup ------------------- #
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)


# ------------------- READ OPERATIONS ------------------- #

def get_user_by_email(db: Session, email: str) -> User | None:
    try:
        return db.query(User).filter(User.email == email).first()
    except SQLAlchemyError as e:
        logger.error(f"Database error while fetching user by email: {e}")
        raise


def get_user_by_id(db: Session, user_id: int) -> User | None:
    try:
        return db.query(User).filter(User.id == user_id).first()
    except SQLAlchemyError as e:
        logger.error(f"Database error while fetching user by ID: {e}")
        raise


def get_all_users(db: Session, skip: int = 0, limit: int = 100) -> list[User]:
    try:
        return db.query(User).offset(skip).limit(limit).all()
    except SQLAlchemyError as e:
        logger.error(f"Database error while fetching all users: {e}")
        raise


# ------------------- WRITE OPERATIONS ------------------- #

def create_user(db: Session, user_data: UserCreate) -> User:
    if not user_data.email:
        raise ValueError("Email is required")
    if not user_data.password:
        raise ValueError("Password is required")
    if len(user_data.password) < 8:
        raise ValueError("Password must be at least 8 characters")

    existing_user = get_user_by_email(db, user_data.email)
    if existing_user:
        raise ValueError(f"User with email {user_data.email} already exists")
    existing_nickname = db.query(User).filter(User.nickname == user_data.nickname).first()
    if existing_nickname:
        raise ValueError(f"User with nickname {user_data.nickname} already exists")

    try:
        hashed_password = hash_password(user_data.password)
        new_user = User(
            email=user_data.email,
            hashed_password=hashed_password,
            nickname=user_data.nickname,
            is_admin=False,
            is_verified=False,
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        logger.info(f"New user created successfully: {new_user.email}")
        return new_user
    except IntegrityError as e:
        db.rollback()
        # Covers race conditions on unique constraints (email/nickname).
        error_text = str(getattr(e, "orig", e)).lower()
        if "email" in error_text:
            raise ValueError(f"User with email {user_data.email} already exists") from e
        if "nickname" in error_text:
            raise ValueError(f"User with nickname {user_data.nickname} already exists") from e
        raise ValueError("User already exists") from e
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error while creating user: {e}")
        raise


# ------------------- DELETE OPERATIONS ------------------- #

def delete_user(db: Session, user_id: int) -> bool:
    try:
        user = get_user_by_id(db, user_id)
        if not user:
            logger.warning(f"Delete failed - user ID {user_id} not found")
            return False
        db.delete(user)
        db.commit()
        logger.info(f"User ID {user_id} deleted successfully")
        return True
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error while deleting user: {e}")
        raise
