from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db import get_db
from app.schemas.user import ProfileCompleteRequest, ProfileUpdateRequest, UserResponse
from app.utils.security import get_current_user
from app.db.models import User

router = APIRouter(prefix="/profile", tags=["Profile"])

@router.post("/complete", response_model=UserResponse)
def complete_profile(payload: ProfileCompleteRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.is_profile_complete:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Profile already complete")
    
    db_user = db.query(User).filter(User.id == current_user.id).first()
    
    existing = db.query(User).filter(User.nickname == payload.nickname, User.id != current_user.id).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Nickname already taken")

    db_user.nickname = payload.nickname
    db_user.phone = payload.phone
    db_user.address = payload.address
    db_user.is_profile_complete = True
    db_user.is_phone_verified = False

    db.commit()
    db.refresh(db_user)
    return db_user

@router.post("/update", response_model=UserResponse)
def update_profile(payload: ProfileUpdateRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.id == current_user.id).first()

    if payload.nickname:
        existing = db.query(User).filter(User.nickname == payload.nickname, User.id != current_user.id).first()
        if existing:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Nickname already taken")
        db_user.nickname = payload.nickname

    if payload.address is not None:
        db_user.address = payload.address
        
    if payload.phone and payload.phone != db_user.phone:
        db_user.phone = payload.phone
        db_user.is_phone_verified = False

    db.commit()
    db.refresh(db_user)
    return db_user
