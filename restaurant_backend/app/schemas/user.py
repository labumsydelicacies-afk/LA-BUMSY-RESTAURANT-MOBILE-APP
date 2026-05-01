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
    nickname: str
    role: Literal["customer", "rider"] = "customer"


class RoleUpdateRequest(BaseModel):
    is_admin: bool = False
    is_rider: bool = False


class UserResponse(UserBase):
    id: int
    is_admin: bool
    is_rider: bool
    is_verified: bool
    created_at: datetime
    nickname: str
    class Config:
        from_attributes = True
