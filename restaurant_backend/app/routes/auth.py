#===========================#
#   AUTHENTICATION ROUTE    #
#===========================#

import logging

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas.auth import (
    ForgotPasswordRequest,
    LoginRequest,
    RegisterResponse,
    ResetPasswordRequest,
    TokenResponse,
    VerifyOtpRequest,
)
from app.schemas.user import UserCreate
from app.services.auth_service import login_user
from app.services.email_verification_service import (
    consume_otp_for_user,
    create_otp,
    send_verification_email_async,
    verify_otp_for_user,
)
from app.services.user_service import get_user_by_email, get_user_by_id
from app.services.user_service import create_user
from app.utils.security import hash_password

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
)
def register(
    user_data: UserCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
    Register a new user.
    """
    try:
        user = create_user(db, user_data)
        logger.info("User creation succeeded for email=%s", user.email)
        otp = create_otp(db, user.id)
        email_queued = True
        try:
            background_tasks.add_task(send_verification_email_async, user.email, otp)
            logger.info("Verification email task queued for email=%s", user.email)
        except Exception:
            email_queued = False
            logger.exception("Failed to queue verification email task for email=%s", user.email)
        return {
            "success": True,
            "message": "User created. Email sending in progress.",
            "email_queued": email_queued,
            "user": user,
        }
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


@router.post("/forgot-password")
def forgot_password(
    payload: ForgotPasswordRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    user = get_user_by_email(db, payload.email)
    if user:
        otp = create_otp(db, user.id)
        try:
            background_tasks.add_task(
                send_verification_email_async,
                user.email,
                otp,
                subject="Your password reset code",
                purpose="password reset",
            )
        except Exception:
            logger.exception("Failed to queue password reset email for email=%s", user.email)

    return {
        "success": True,
        "message": "If an account exists, a reset code has been sent",
    }


@router.post("/reset-password")
def reset_password(payload: ResetPasswordRequest, db: Session = Depends(get_db)):
    if not payload.email and payload.user_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email or user_id is required",
        )

    user = None
    if payload.user_id is not None:
        user = get_user_by_id(db, payload.user_id)
    if user is None and payload.email:
        user = get_user_by_email(db, payload.email)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired OTP",
        )

    if not consume_otp_for_user(db, user.id, payload.otp_code):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired OTP",
        )

    if len(payload.new_password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters",
        )

    user.hashed_password = hash_password(payload.new_password)
    db.commit()

    return {
        "success": True,
        "message": "Password reset successful",
    }
