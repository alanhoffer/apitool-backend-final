from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.dependencies import get_current_user_payload
from app.services.auth_service import AuthService
from app.services.user_service import UserService
from app.schemas.user import CreateUser, LoginUser
from app.schemas.auth import AuthData
from app.models.user import User

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/login", response_model=AuthData, status_code=status.HTTP_200_OK)
async def sign_in(login_data: LoginUser, db: Session = Depends(get_db)):
    auth_service = AuthService(db)
    return await auth_service.sign_in(login_data)

@router.post("/register", response_model=AuthData)
async def sign_up(signup_data: CreateUser, db: Session = Depends(get_db)):
    auth_service = AuthService(db)
    return await auth_service.sign_up(signup_data)

@router.post("/logout")
async def sign_out(payload: dict = Depends(get_current_user_payload)):
    # Logout is handled client-side by removing the token
    return {"message": "Logged out successfully"}

@router.get("/profile")
async def profile(payload: dict = Depends(get_current_user_payload)):
    return payload

