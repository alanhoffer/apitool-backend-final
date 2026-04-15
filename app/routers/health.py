"""
Health check endpoints for monitoring and load balancers.
"""
from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.config import settings
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
        "service": "apitool-api",
        "version": settings.app_version,
        "release": settings.release_identifier,
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
            "database": "connected",
            "version": settings.app_version,
            "release": settings.release_identifier,
        }
    except Exception:
        logger.exception("Database connection failed during readiness check")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "not_ready",
                "database": "disconnected",
                "version": settings.app_version,
                "release": settings.release_identifier,
            }
        )

@router.get("/live")
async def liveness_check() -> Dict[str, str]:
    """
    Liveness check endpoint.
    Returns 200 if the service is alive.
    """
    return {
        "status": "alive",
        "version": settings.app_version,
        "release": settings.release_identifier,
    }


