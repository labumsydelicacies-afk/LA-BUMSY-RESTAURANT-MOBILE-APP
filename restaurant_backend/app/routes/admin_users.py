#=================================#
#         ADMIN USER ROUTES        #
#=================================#

"""
Admin-only endpoints for user management and role assignment.
All routes require is_admin=True.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.db.models import User
from app.schemas.user import RoleUpdateRequest, UserResponse
from app.services.user_service import get_all_users, get_user_by_id, is_profile_complete_for_user
from app.utils.security import get_current_admin_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin/users", tags=["Admin – Users"])


@router.get("", response_model=list[UserResponse])
def list_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    _=Depends(get_current_admin_user),
):
    """Return all registered users. Admin only."""
    return get_all_users(db, skip=skip, limit=limit)


@router.patch("/{user_id}/role", response_model=UserResponse)
def update_user_role(
    user_id: int,
    payload: RoleUpdateRequest,
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin_user),
):
    """
    Promote or demote a user's role.
    Admin can set is_admin and is_rider independently.
    An admin cannot demote themselves.
    """
    if user_id == current_admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot change your own role.",
        )

    user = get_user_by_id(db, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User #{user_id} not found.",
        )

    user.is_admin = payload.is_admin
    user.is_rider = payload.is_rider
    user.is_profile_complete = is_profile_complete_for_user(user)
    db.commit()
    db.refresh(user)

    logger.info(
        "Admin #%s updated roles for user #%s → is_admin=%s is_rider=%s",
        current_admin.id, user_id, payload.is_admin, payload.is_rider,
    )
    return user
