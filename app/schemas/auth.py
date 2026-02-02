from pydantic import BaseModel, EmailStr, Field

class AuthData(BaseModel):
    user_id: int
    access_token: str

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    token: str = Field(..., min_length=1)
    newPassword: str = Field(..., min_length=7)
