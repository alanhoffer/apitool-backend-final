import hashlib
import hmac
from typing import Optional

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.constants import JWT_SECRET, JWT_ALGORITHM

security = HTTPBearer()

def build_password_fingerprint(password_hash: str) -> str:
    return hmac.new(
        JWT_SECRET.encode("utf-8"),
        password_hash.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

def _credentials_exception() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

def _normalize_role(role: object) -> str:
    if hasattr(role, "value"):
        return str(role.value)
    return str(role)

def _decode_and_validate_user(
    credentials: HTTPAuthorizationCredentials,
    db: Session,
) -> tuple[User, dict]:
    credentials_exception = _credentials_exception()

    try:
        token = credentials.credentials
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id_str = payload.get("sub")
        if user_id_str is None:
            raise credentials_exception
        user_id = int(user_id_str)
    except (JWTError, ValueError, TypeError):
        raise credentials_exception

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception

    password_fingerprint = payload.get("pwd_fgp")
    if password_fingerprint is not None:
        current_fingerprint = build_password_fingerprint(user.password)
        if not hmac.compare_digest(password_fingerprint, current_fingerprint):
            raise credentials_exception

    payload["sub"] = str(user.id)
    payload["username"] = user.email
    payload["role"] = _normalize_role(user.role)
    return user, payload

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
    request: Request = None
) -> User:
    user, _ = _decode_and_validate_user(credentials, db)

    # Agregar user_id al request state para rate limiting
    if request:
        request.state.user_id = user.id

    return user

async def get_current_user_payload(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
    request: Request = None
) -> dict:
    user, payload = _decode_and_validate_user(credentials, db)

    # Agregar user_id al request state para rate limiting
    if request:
        request.state.user_id = user.id

    return payload

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
