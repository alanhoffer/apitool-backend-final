from jose import jwt, JWTError
from passlib.context import CryptContext
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.services.user_service import UserService
from app.schemas.user import CreateUser, LoginUser
from app.schemas.auth import AuthData, ForgotPasswordRequest, ResetPasswordRequest
from app.constants import JWT_SECRET, JWT_ALGORITHM, BCRYPT_SALT_ROUNDS
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

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
    
    def create_reset_token(self, email: str) -> str:
        """
        Crea un token JWT para reset de contraseña con expiración de 1 hora.
        """
        payload = {
            "email": email,
            "type": "password_reset",
            "exp": datetime.utcnow() + timedelta(hours=1)
        }
        return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    
    async def forgot_password(self, request: ForgotPasswordRequest) -> dict:
        """
        Genera un token de reset de contraseña y lo envía por email.
        En producción, aquí se debería enviar un email real.
        """
        user = self.user_service.get_user_by_email(request.email)
        if not user:
            # Por seguridad, no revelamos si el email existe o no
            logger.warning(f"Password reset requested for non-existent email: {request.email}")
            return {"message": "Se ha enviado un enlace de recuperación a tu email"}
        
        reset_token = self.create_reset_token(request.email)
        
        # TODO: Enviar email con el token
        # En producción, aquí se enviaría un email con un enlace como:
        # https://yourapp.com/reset-password?token={reset_token}
        logger.info(f"Password reset token generated for user: {user.email}")
        # Por ahora solo logueamos el token (en producción NO hacer esto)
        logger.debug(f"Reset token: {reset_token}")
        
        return {"message": "Se ha enviado un enlace de recuperación a tu email"}
    
    async def reset_password(self, request: ResetPasswordRequest) -> dict:
        """
        Restablece la contraseña usando un token válido.
        """
        try:
            # Decodificar y validar el token
            payload = jwt.decode(request.token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            
            # Verificar que es un token de reset de contraseña
            if payload.get("type") != "password_reset":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid token type"
                )
            
            email = payload.get("email")
            if not email:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid token"
                )
            
            # Buscar usuario
            user = self.user_service.get_user_by_email(email)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            
            # Actualizar contraseña
            hashed_password = self.hash_password(request.newPassword)
            user.password = hashed_password
            
            try:
                self.db.commit()
                self.db.refresh(user)
                logger.info(f"Password reset successful for user: {user.email}")
                return {"message": "Contraseña restablecida exitosamente"}
            except Exception:
                self.db.rollback()
                raise
            
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired token"
            )
