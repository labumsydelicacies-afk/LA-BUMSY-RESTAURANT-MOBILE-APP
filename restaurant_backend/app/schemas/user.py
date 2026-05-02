#================================#
#        USER SCHEMAS            #
#================================#

from pydantic import BaseModel, EmailStr, field_validator
from datetime import datetime
from typing import Literal




class UserBase(BaseModel):
    email: EmailStr




class UserCreate(UserBase):
    password: str
    role: Literal["customer", "rider"] = "customer"

class ProfileCompleteRequest(BaseModel):
    nickname: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    phone: str | None = None
    address: str | None = None

class ProfileUpdateRequest(BaseModel):
    nickname: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    phone: str | None = None
    address: str | None = None


class RoleUpdateRequest(BaseModel):
    is_admin: bool = False
    is_rider: bool = False


class UserResponse(UserBase):
    id: int
    is_admin: bool
    is_rider: bool
    is_email_verified: bool
    is_profile_complete: bool
    created_at: datetime
    nickname: str | None
    first_name: str | None
    last_name: str | None
    display_name: str
    phone: str | None
    address: str | None
    class Config:
        from_attributes = True
