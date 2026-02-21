from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.constants import JWT_SECRET, JWT_ALGORITHM
from typing import Optional

security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
    request: Request = None
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        token = credentials.credentials
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id_str = payload.get("sub")
        if user_id_str is None:
            raise credentials_exception
        user_id: int = int(user_id_str)
    except (JWTError, ValueError, TypeError):
        raise credentials_exception
    
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception
    
    # Agregar user_id al request state para rate limiting
    if request:
        request.state.user_id = user_id
    
    return user

async def get_current_user_payload(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    request: Request = None
) -> dict:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        token = credentials.credentials
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        
        # Agregar user_id al request state para rate limiting
        if request:
            user_id_str = payload.get("sub")
            if user_id_str:
                try:
                    request.state.user_id = int(user_id_str)
                except (ValueError, TypeError):
                    pass
        
        return payload
    except JWTError:
        raise credentials_exception

def require_role(required_role: Optional[str] = None):
    async def role_checker(
        payload: dict = Depends(get_current_user_payload)
    ):
        if required_role and required_role != "":
            user_role = payload.get("role")
            if user_role != required_role:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not enough permissions"
                )
        return payload
    
    return role_checker

def require_roles(allowed_roles: list[str]):
    async def role_checker(
        payload: dict = Depends(get_current_user_payload)
    ):
        if allowed_roles:
            user_role = payload.get("role")
            if user_role not in allowed_roles:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not enough permissions"
                )
        return payload
    
    return role_checker

