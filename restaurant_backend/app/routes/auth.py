#===========================#
#   AUTHENTICATION ROUTE    #
#===========================#

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas.auth import LoginRequest, TokenResponse, VerifyOtpRequest
from app.schemas.user import UserCreate, UserResponse
from app.services.auth_service import login_user
from app.services.email_verification_service import (
    send_verification_email,
    verify_otp_for_user,
)
from app.services.user_service import create_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """
    Register a new user.
    """
    try:
        user = create_user(db, user_data)
        send_verification_email(db, user)
        return user
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        logger.exception("Unexpected error during registration")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed",
        ) from exc


@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
)
def login(login_data: LoginRequest, db: Session = Depends(get_db)):
    """
    Authenticate user and return an access token.
    """
    try:
        token_response = login_user(db, login_data.email, login_data.password)
        if not token_response:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return token_response
    except HTTPException:
        raise
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
    except Exception as exc:
        logger.exception("Unexpected error during login")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed",
        ) from exc



@router.post("/verify-otp")
def verify_otp(payload: VerifyOtpRequest, session: Session = Depends(get_db)):
    verified = verify_otp_for_user(session, payload.user_id, payload.otp)
    if not verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired OTP",
        )
    return {"message": "Email verified successfully"}
