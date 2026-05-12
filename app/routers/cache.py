"""
Endpoints para gestión y estadísticas del caché.
"""
from fastapi import APIRouter, Depends
from app.dependencies import require_role
from app.utils.cache import cache
from typing import Dict, Any

router = APIRouter(prefix="/cache", tags=["cache"])

@router.get("/stats")
async def get_cache_stats(
    payload: dict = Depends(require_role("admin"))
) -> Dict[str, Any]:
    """
    Obtiene estadísticas del caché.
    Requiere autenticación.
    """
    stats = cache.get_stats()
    return {
        "cache": stats,
        "message": "Cache statistics"
    }

@router.delete("")
async def clear_cache(
    payload: dict = Depends(require_role("admin"))
) -> Dict[str, str]:
    """
    Limpia todo el caché.
    Requiere autenticación.
    """
    cache.clear()
    return {
        "message": "Cache cleared successfully"
    }

@router.post("/cleanup")
async def cleanup_cache(
    payload: dict = Depends(require_role("admin"))
) -> Dict[str, Any]:
    """
    Limpia entradas expiradas del caché.
    Requiere autenticación.
    """
    cleaned = cache.cleanup_expired()
    return {
        "message": "Cache cleanup completed",
        "expired_entries_removed": cleaned
    }


