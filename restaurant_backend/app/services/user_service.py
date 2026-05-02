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


def get_user_display_name(user: User) -> str:
    if user.is_rider:
        full_name = " ".join(part for part in [user.first_name, user.last_name] if part).strip()
        if full_name:
            return full_name
    if user.nickname:
        return user.nickname
    if user.first_name or user.last_name:
        return " ".join(part for part in [user.first_name, user.last_name] if part).strip()
    return user.email


def is_profile_complete_for_user(
    user: User,
    *,
    nickname: str | None = None,
    first_name: str | None = None,
    last_name: str | None = None,
    phone: str | None = None,
    address: str | None = None,
) -> bool:
    nickname = user.nickname if nickname is None else nickname
    first_name = user.first_name if first_name is None else first_name
    last_name = user.last_name if last_name is None else last_name
    phone = user.phone if phone is None else phone
    address = user.address if address is None else address

    if user.is_admin:
        return True
    if user.is_rider:
        return bool(first_name and last_name and phone and address)
    return bool(nickname and phone and address)


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

    try:
        hashed_password = hash_password(user_data.password)
        new_user = User(
            email=user_data.email,
            hashed_password=hashed_password,
            is_admin=False,
            is_rider=(user_data.role == "rider"),
            is_email_verified=False,
            is_profile_complete=False,
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        logger.info(f"New user created successfully: {new_user.email}")
        return new_user
    except IntegrityError as e:
        db.rollback()
        # Covers race conditions on unique constraints (email).
        error_text = str(getattr(e, "orig", e)).lower()
        if "email" in error_text:
            raise ValueError(f"User with email {user_data.email} already exists") from e
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
