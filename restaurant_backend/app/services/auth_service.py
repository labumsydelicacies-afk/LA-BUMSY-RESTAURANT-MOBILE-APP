#================================#
#  AUTHENTICATION SERVICE LAYER  #
#================================#

"""THIS MODULE HANDLES USER AUTHENTICATION AND LOGIN, VERIFYING CREDENTIALS AND ISSUING JWT TOKENS."""

import logging

from sqlalchemy.orm import Session

from app.services.user_service import get_user_by_email
from app.utils.security import (
    UserRole,
    create_access_token,
    hash_password,
    needs_password_rehash,
    verify_password,
)


# ------------------- Logger Setup ------------------- #
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)


# ------------------- AUTHENTICATE ------------------- #

def authenticate_user(db: Session, email: str, password: str):
    """
    Verifies user identity by checking email and password.

    Args:
        db       : Database session
        email    : User's email address
        password : Plain text password to verify

    Returns:
        User object if credentials are valid, None otherwise
    """
    if not email:
        logger.warning("Authentication failed - no email provided")
        return None

    if not password:
        logger.warning("Authentication failed - no password provided")
        return None

    user = get_user_by_email(db, email)
    if not user:
        logger.warning(f"Authentication failed - email not found: {email}")
        return None

    if not user.is_verified:
        logger.warning(f"Authentication failed - user not verified: {email}")
        return None

    if not verify_password(password, user.hashed_password):
        logger.warning(f"Authentication failed - wrong password for: {email}")
        return None

    logger.info(f"Authentication successful : {email}")
    return user


# ------------------- LOGIN ------------------- #

def login_user(db: Session, email: str, password: str) -> dict | None:
    """
    Authenticates user and returns a JWT token response.

    Args:
        db       : Database session
        email    : User's email address
        password : Plain text password

    Returns:
        Dict with access_token and token_type, or None if auth fails
    """
    user = authenticate_user(db, email, password)

    if not user:
        logger.warning(f"Login failed for : {email}")
        return None

    if needs_password_rehash(user.hashed_password):
        user.hashed_password = hash_password(password)
        db.commit()
        db.refresh(user)
        logger.info(f"Password hash upgraded for user : {email}")

    if user.is_admin:
        role = UserRole.ADMIN
    elif user.is_rider:
        role = UserRole.RIDER
    else:
        role = UserRole.CUSTOMER

    token = create_access_token(
        data={
            "sub": user.email,
            "user_id": user.id,
            "nickname": user.nickname,
        },
        role=role,
    )

    logger.info(f"Login successful : {email} | role : {role}")

    return {
        "access_token": token,
        "token_type": "bearer",
        "role": role,
        "nickname": user.nickname,
    }
