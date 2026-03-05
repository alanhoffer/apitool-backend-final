"""
Health check endpoints for monitoring and load balancers.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.database import get_db
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/health", tags=["health"])

@router.get("")
async def health_check() -> Dict[str, str]:
    """
    Basic health check endpoint.
    Returns 200 if the API is running.
    """
    return {
        "status": "healthy",
        "service": "apitool-api"
    }

@router.get("/ready")
async def readiness_check(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Readiness check endpoint.
    Verifies that the API can connect to the database.
    Returns 200 if ready, 503 if not ready.
    """
    try:
        # Try to execute a simple query
        db.execute(text("SELECT 1"))
        return {
            "status": "ready",
            "database": "connected"
        }
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return {
            "status": "not_ready",
            "database": "disconnected",
            "error": str(e)
        }

@router.get("/live")
async def liveness_check() -> Dict[str, str]:
    """
    Liveness check endpoint.
    Returns 200 if the service is alive.
    """
    return {
        "status": "alive"
    }

@router.post("/setup-fede-user-internal-temp")
async def setup_fede_user(db: Session = Depends(get_db)):
    """
    TEMPORARY ENDPOINT to create Fede Guzman's account.
    To be removed immediately after use.
    """
    from passlib.context import CryptContext
    from app.models.user import User, Role
    
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    email = "fedeguzman_vet@hotmail.com"
    password = "15533786"
    name = "Fede"
    surname = "Guzman"
    
    # Check if exists
    existing = db.query(User).filter(User.email == email).first()
    if existing:
        return {"message": f"User {email} already exists", "user_id": existing.id}
    
    hashed_password = pwd_context.hash(password)
    
    new_user = User(
        name=name,
        surname=surname,
        email=email,
        password=hashed_password,
        role=Role.APICULTOR
    )
    
    db.add(new_user)
    try:
        db.commit()
        db.refresh(new_user)
        return {
            "message": "User created successfully",
            "email": email,
            "id": new_user.id
        }
    except Exception as e:
        db.rollback()
        return {"error": str(e)}


