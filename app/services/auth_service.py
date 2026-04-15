from datetime import datetime, timedelta, timezone
import logging
from uuid import uuid4

from fastapi import HTTPException, status
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.config import settings
from app.constants import JWT_SECRET, JWT_ALGORITHM, BCRYPT_SALT_ROUNDS, JWT_EXPIRATION_DAYS
from app.schemas.auth import AuthData, ForgotPasswordRequest, ResetPasswordRequest
from app.schemas.user import CreateUser, LoginUser
from app.services.user_service import UserService

logger = logging.getLogger(__name__)

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=BCRYPT_SALT_ROUNDS,
)


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
        expire = datetime.now(timezone.utc) + timedelta(days=JWT_EXPIRATION_DAYS)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)
        return encoded_jwt

    async def sign_in(self, login_data: LoginUser) -> AuthData:
        user = self.user_service.get_user_by_email(login_data.email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials",
            )

        if not self.verify_password(login_data.password, user.password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials",
            )

        payload = {
            "username": user.email,
            "sub": str(user.id),
            "role": user.role.value,
        }

        return AuthData(
            user_id=user.id,
            access_token=self.create_access_token(payload),
        )

    async def sign_up(self, signup_data: CreateUser) -> AuthData:
        original_password = signup_data.password
        encrypted_password = self.hash_password(signup_data.password)
        signup_data.password = encrypted_password

        created_user = self.user_service.create_user(signup_data)
        if not created_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User already exists",
            )

        user = self.user_service.get_user_by_email(signup_data.email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="User creation failed",
            )

        if not self.verify_password(original_password, user.password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials",
            )

        payload = {
            "username": user.email,
            "sub": str(user.id),
            "role": user.role.value,
        }

        return AuthData(
            user_id=user.id,
            access_token=self.create_access_token(payload),
        )

    def create_reset_token(self, email: str) -> str:
        now = datetime.now(timezone.utc)
        payload = {
            "email": email,
            "type": "password_reset",
            "iat": now,
            "nbf": now,
            "jti": str(uuid4()),
            "exp": now + timedelta(minutes=settings.password_reset_token_ttl_minutes),
        }
        return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

    async def forgot_password(self, request: ForgotPasswordRequest) -> dict:
        if not settings.password_reset_enabled:
            logger.warning("Password reset requested while the flow is disabled")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Password reset is not available",
            )

        user = self.user_service.get_user_by_email(request.email)
        if not user:
            logger.warning(f"Password reset requested for non-existent email: {request.email}")
            return {"message": "Se ha enviado un enlace de recuperacion a tu email"}

        self.create_reset_token(request.email)
        logger.info(f"Password reset requested for user: {user.email}")

        return {"message": "Se ha enviado un enlace de recuperacion a tu email"}

    async def reset_password(self, request: ResetPasswordRequest) -> dict:
        if not settings.password_reset_enabled:
            logger.warning("Password reset completion attempted while the flow is disabled")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Password reset is not available",
            )

        try:
            payload = jwt.decode(request.token, JWT_SECRET, algorithms=[JWT_ALGORITHM])

            if payload.get("type") != "password_reset":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid token type",
                )

            email = payload.get("email")
            if not email:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid token",
                )

            user = self.user_service.get_user_by_email(email)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found",
                )

            hashed_password = self.hash_password(request.newPassword)
            user.password = hashed_password

            try:
                self.db.commit()
                self.db.refresh(user)
                logger.info(f"Password reset successful for user: {user.email}")
                return {"message": "Contrasena restablecida exitosamente"}
            except Exception:
                self.db.rollback()
                raise

        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired token",
            )
