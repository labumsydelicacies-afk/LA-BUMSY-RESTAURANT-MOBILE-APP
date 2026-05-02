from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db import get_db
from app.schemas.user import ProfileCompleteRequest, ProfileUpdateRequest, UserResponse
from app.utils.security import get_current_user
from app.db.models import User
from app.services.user_service import is_profile_complete_for_user

router = APIRouter(prefix="/profile", tags=["Profile"])


def _clean_optional(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    return cleaned or None


def _validate_profile_fields(
    *,
    current_user: User,
    nickname: str | None,
    first_name: str | None,
    last_name: str | None,
    phone: str | None,
    address: str | None,
) -> None:
    if current_user.is_admin:
        return

    missing_fields: list[str] = []

    if current_user.is_rider:
        if not first_name:
            missing_fields.append("first name")
        if not last_name:
            missing_fields.append("last name")
    elif not nickname:
        missing_fields.append("nickname")
    if not phone:
        missing_fields.append("phone number")
    if not address:
        missing_fields.append("home address")

    if missing_fields:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Please provide your {', '.join(missing_fields)}",
        )
@router.post("/complete", response_model=UserResponse)
def complete_profile(payload: ProfileCompleteRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.is_profile_complete:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Profile already complete")
    
    db_user = db.query(User).filter(User.id == current_user.id).first()

    nickname = _clean_optional(payload.nickname)
    first_name = _clean_optional(payload.first_name)
    last_name = _clean_optional(payload.last_name)
    phone = _clean_optional(payload.phone)
    address = _clean_optional(payload.address)

    _validate_profile_fields(
        current_user=current_user,
        nickname=nickname,
        first_name=first_name,
        last_name=last_name,
        phone=phone,
        address=address,
    )

    if nickname:
        existing = db.query(User).filter(User.nickname == nickname, User.id != current_user.id).first()
        if existing:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Nickname already taken")

    db_user.nickname = nickname
    db_user.first_name = first_name
    db_user.last_name = last_name
    db_user.phone = phone
    db_user.address = address
    db_user.is_profile_complete = is_profile_complete_for_user(
        db_user,
        nickname=nickname,
        first_name=first_name,
        last_name=last_name,
        phone=phone,
        address=address,
    )

    db.commit()
    db.refresh(db_user)
    return db_user

@router.post("/update", response_model=UserResponse)
def update_profile(payload: ProfileUpdateRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.id == current_user.id).first()

    nickname = _clean_optional(payload.nickname) if payload.nickname is not None else db_user.nickname
    first_name = _clean_optional(payload.first_name) if payload.first_name is not None else db_user.first_name
    last_name = _clean_optional(payload.last_name) if payload.last_name is not None else db_user.last_name
    phone = _clean_optional(payload.phone) if payload.phone is not None else db_user.phone
    address = _clean_optional(payload.address) if payload.address is not None else db_user.address

    _validate_profile_fields(
        current_user=current_user,
        nickname=nickname,
        first_name=first_name,
        last_name=last_name,
        phone=phone,
        address=address,
    )

    if payload.nickname is not None:
        existing = db.query(User).filter(User.nickname == nickname, User.id != current_user.id).first()
        if existing:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Nickname already taken")
        db_user.nickname = nickname
    if payload.first_name is not None:
        db_user.first_name = first_name
    if payload.last_name is not None:
        db_user.last_name = last_name

    if payload.address is not None:
        db_user.address = address
        
    if payload.phone is not None and phone != db_user.phone:
        db_user.phone = phone

    db_user.is_profile_complete = is_profile_complete_for_user(
        db_user,
        nickname=db_user.nickname,
        first_name=db_user.first_name,
        last_name=db_user.last_name,
        phone=db_user.phone,
        address=db_user.address,
    )

    db.commit()
    db.refresh(db_user)
    return db_user
