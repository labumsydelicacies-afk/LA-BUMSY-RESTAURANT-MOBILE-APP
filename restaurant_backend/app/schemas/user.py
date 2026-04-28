#================================#
#        USER SCHEMAS            #
#================================#

from pydantic import BaseModel , EmailStr
from datetime import datetime




class UserBase(BaseModel):
    email: EmailStr
    



class UserCreate(UserBase):
    password: str
    nickname: str



class UserResponse(UserBase):
    id: int
    is_admin: bool
    created_at: datetime
    nickname: str
    class Config:
        from_attributes = True