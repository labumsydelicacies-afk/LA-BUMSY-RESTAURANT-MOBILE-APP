#================================#
#     AUTHENTICATION SCHEMAS     #
#================================#



from pydantic import BaseModel, EmailStr

from app.schemas.user import UserResponse




class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    nickname: str


class VerifyOtpRequest(BaseModel):
    user_id: int
    otp: str


class RegisterResponse(BaseModel):
    success: bool
    message: str
    email_queued: bool
    user: UserResponse
