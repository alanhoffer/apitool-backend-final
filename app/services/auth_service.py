from jose import jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.services.user_service import UserService
from app.schemas.user import CreateUser, LoginUser
from app.schemas.auth import AuthData
from app.constants import JWT_SECRET, JWT_ALGORITHM, BCRYPT_SALT_ROUNDS
from datetime import datetime, timedelta

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class AuthService:
    def __init__(self, db: Session):
        self.db = db
        self.user_service = UserService(db)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return pwd_context.verify(plain_password, hashed_password)
    
    def hash_password(self, password: str) -> str:
        return pwd_context.hash(password)
    
    def create_access_token(self, data: dict) -> str:
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=365)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)
        return encoded_jwt
    
    async def sign_in(self, login_data: LoginUser) -> AuthData:
        user = self.user_service.get_user_by_email(login_data.email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
        
        if not self.verify_password(login_data.password, user.password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
        
        payload = {
            "username": user.email,
            "sub": str(user.id),
            "role": user.role.value
        }
        
        return AuthData(
            user_id=user.id,
            access_token=self.create_access_token(payload)
        )
    
    async def sign_up(self, signup_data: CreateUser) -> AuthData:
        # Store original password for verification
        original_password = signup_data.password
        encrypted_password = self.hash_password(signup_data.password)
        signup_data.password = encrypted_password
        
        created_user = self.user_service.create_user(signup_data)
        if not created_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User already exists"
            )
        
        user = self.user_service.get_user_by_email(signup_data.email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="User creation failed"
            )
        
        # Verify with original password
        if not self.verify_password(original_password, user.password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
        
        payload = {
            "username": user.email,
            "sub": str(user.id),
            "role": user.role.value
        }
        
        return AuthData(
            user_id=user.id,
            access_token=self.create_access_token(payload)
        )

