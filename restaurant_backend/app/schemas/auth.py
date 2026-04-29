#================================#
#     AUTHENTICATION SCHEMAS     #
#================================#



from pydantic import BaseModel, EmailStr




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
