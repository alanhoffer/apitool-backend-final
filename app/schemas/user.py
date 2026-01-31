from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime
from app.models.user import Role

class CreateUser(BaseModel):
    name: str = Field(..., min_length=3)
    surname: str = Field(..., min_length=3)
    email: EmailStr
    password: str = Field(..., min_length=7)

class LoginUser(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=7)

class PushTokenUpdate(BaseModel):
    token: str
    deviceName: Optional[str] = None  # Nombre del dispositivo (ej: "iPhone 12", "Samsung Galaxy")
    platform: Optional[str] = None    # Plataforma: "ios" o "android"

class UserResponse(BaseModel):
    id: int
    name: str
    surname: str
    email: str
    createdAt: datetime
    authStrategy: Optional[str] = None
    role: Role
    expoPushToken: Optional[str] = None
    
    class Config:
        from_attributes = True

