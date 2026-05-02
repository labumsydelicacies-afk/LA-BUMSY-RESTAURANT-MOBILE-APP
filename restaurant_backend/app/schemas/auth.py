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
    nickname: str | None
    user_state: str = "ACTIVE" # "PROFILE_INCOMPLETE" | "ACTIVE"


class VerifyOtpRequest(BaseModel):
    user_id: int
    otp: str


class RegisterResponse(BaseModel):
    success: bool
    message: str
    email_queued: bool
    user: UserResponse


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    email: EmailStr | None = None
    user_id: int | None = None
    otp_code: str
    new_password: str


class ResendOtpRequest(BaseModel):
    email: EmailStr

class SendPhoneOtpRequest(BaseModel):
    phone: str

class VerifyPhoneOtpRequest(BaseModel):
    phone: str
    otp: str
