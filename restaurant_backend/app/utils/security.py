#================================#
#          SECURITY              #
#================================#

"""THIS MODULE CONTAINS ALL THE SECURITY-RELATED UTILITIES, SUCH AS PASSWORD HASHING AND JWT TOKEN MANAGEMENT."""

from datetime import datetime, timedelta, timezone
from enum import Enum

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.config import ALGORITHM, SECRET_KEY


#------------------- User Roles -------------------#
class UserRole(str, Enum):
    CUSTOMER = "customer"
    ADMIN = "admin"


#------------------- Token Expiry Per Role -------------------#
TOKEN_EXPIRY_MINUTES = {
    UserRole.CUSTOMER: 60,
    UserRole.ADMIN: 30,
}


#------------------- Password Hashing Setup -------------------#
pwd_context = CryptContext(
    schemes=["argon2", "bcrypt"],
    deprecated="auto",
)


def hash_password(password: str) -> str:
    """Hashes a plain text password using the preferred scheme (argon2)."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain text password against a hashed password."""
    return pwd_context.verify(plain_password, hashed_password)


def needs_password_rehash(hashed_password: str) -> bool:
    """Returns True when hash should be upgraded to preferred scheme/settings."""
    return pwd_context.needs_update(hashed_password)


#------------------- Token Creation -------------------#
def create_access_token(data: dict, role: UserRole = UserRole.CUSTOMER) -> str:
    """
    Creates a signed JWT access token.

    Args:
        data  : Payload to encode (e.g. {"sub": "user@email.com"})
        role  : UserRole.CUSTOMER (60 mins) or UserRole.ADMIN (30 mins)

    Returns:
        Signed JWT token string
    """
    if not SECRET_KEY:
        raise ValueError("SECRET_KEY is not set. Add it to your environment or .env file.")
    if not ALGORITHM:
        raise ValueError("ALGORITHM is not set. Add it to your environment or .env file.")

    to_encode = data.copy()

    expire_minutes = TOKEN_EXPIRY_MINUTES.get(role, 60)
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=expire_minutes)

    to_encode.update({
        "exp": expire,
        "role": role.value,
        "iat": now,
    })

    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


#------------------- Token Decoding -------------------#
def decode_access_token(token: str) -> dict | None:
    """
    Decodes and validates a JWT token.

    Args:
        token : JWT token string from request header

    Returns:
        Decoded payload dict, or None if token is invalid/expired
    """
    try:
        if not SECRET_KEY:
            raise ValueError("SECRET_KEY is not set. Add it to your environment or .env file.")
        if not ALGORITHM:
            raise ValueError("ALGORITHM is not set. Add it to your environment or .env file.")
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


#------------------- Role Checking Helpers -------------------#
def is_admin(token: str) -> bool:
    """Returns True if the token belongs to an admin user."""
    payload = decode_access_token(token)
    if payload is None:
        return False
    return payload.get("role") == UserRole.ADMIN.value


def get_user_email_from_token(token: str) -> str | None:
    """Extracts and returns the user email (sub) from a token string."""
    payload = decode_access_token(token)
    if payload is None:
        return None
    return payload.get("sub")


_bearer_scheme = HTTPBearer(auto_error=False)

def _get_db():
    # Lazy import so importing this module doesn't require DATABASE_URL.
    from app.db.database import get_db as real_get_db
    yield from real_get_db()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer_scheme),
    db: Session = Depends(_get_db),
):
    """
    FastAPI dependency that returns the authenticated User.

    Expects an `Authorization: Bearer <token>` header.
    """
    if credentials is None or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = decode_access_token(credentials.credentials)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Prefer stable numeric user id when present.
    user_id = payload.get("user_id")
    email = payload.get("sub")

    from app.db.models import User  # local import avoids circulars

    user = None
    if isinstance(user_id, int):
        user = db.query(User).filter(User.id == user_id).first()
    if user is None and isinstance(email, str) and email:
        user = db.query(User).filter(User.email == email).first()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


def get_current_admin_user(current_user=Depends(get_current_user)):
    """FastAPI dependency that enforces `current_user.is_admin`."""
    if not getattr(current_user, "is_admin", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
        )
    return current_user
