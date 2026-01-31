from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.services.drum_service import DrumService
from app.schemas.drum import (
    DrumCreate, DrumUpdate, DrumResponse, 
    DrumsListResponse, DrumStats, DrumSoldUpdate
)
from typing import Optional

router = APIRouter(prefix="/drums", tags=["drums"])

@router.post("", response_model=DrumResponse, status_code=status.HTTP_201_CREATED)
async def create_drum(
    drum_data: DrumCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Crea un nuevo tambor escaneado."""
    service = DrumService(db)
    return service.create_drum(current_user.id, drum_data)

@router.get("", response_model=DrumsListResponse)
async def get_drums(
    sold: Optional[bool] = Query(None, description="Filtrar por tambores vendidos"),
    page: int = Query(1, ge=1, description="Número de página"),
    limit: int = Query(50, ge=1, le=100, description="Resultados por página"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtiene la lista de tambores del usuario autenticado con paginación."""
    service = DrumService(db)
    drums, total = service.get_drums(current_user.id, sold, page, limit)
    
    return {
        "data": drums,
        "pagination": {
            "page": page,
            "limit": limit,
            "total": total,
            "totalPages": (total + limit - 1) // limit if total > 0 else 0
        }
    }

@router.get("/stats", response_model=DrumStats)
async def get_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtiene estadísticas agregadas de los tambores del usuario."""
    service = DrumService(db)
    return service.get_stats(current_user.id)

@router.get("/{id}", response_model=DrumResponse)
async def get_drum(
    id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtiene un tambor específico por su ID."""
    service = DrumService(db)
    drum = service.get_drum_by_id(id, current_user.id)
    if not drum:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tambor no encontrado"
        )
    return drum

@router.put("/{id}", response_model=DrumResponse)
async def update_drum(
    id: int,
    updates: DrumUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Actualiza un tambor existente."""
    service = DrumService(db)
    drum = service.update_drum(id, current_user.id, updates)
    if not drum:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tambor no encontrado"
        )
    return drum

@router.patch("/{id}/sold", response_model=DrumResponse)
async def mark_as_sold(
    id: int,
    sold_data: DrumSoldUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Marca un tambor como vendido o no vendido."""
    service = DrumService(db)
    drum = service.mark_as_sold(id, current_user.id, sold_data.sold)
    if not drum:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tambor no encontrado"
        )
    return drum

@router.delete("/{id}")
async def delete_drum(
    id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Elimina un tambor específico."""
    service = DrumService(db)
    if not service.delete_drum(id, current_user.id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tambor no encontrado"
        )
    return {"message": "Tambor eliminado correctamente"}

@router.delete("")
async def delete_all_drums(
    sold: Optional[bool] = Query(None, description="Si se especifica, solo elimina tambores vendidos (true) o no vendidos (false)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Elimina todos los tambores del usuario autenticado, opcionalmente filtrados por estado de venta."""
    service = DrumService(db)
    deleted_count = service.delete_all_drums(current_user.id, sold)
    return {
        "message": f"Se eliminaron {deleted_count} tambores correctamente",
        "deleted_count": deleted_count
    }

