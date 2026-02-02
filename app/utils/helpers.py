"""
Helper functions to reduce code duplication.
"""
from fastapi import HTTPException, status
from app.models.apiary import Apiary
from app.schemas.apiary import ApiaryDetail
from typing import Optional

def verify_apiary_ownership(apiary: Optional[Apiary], user_id: int) -> None:
    """
    Verifica que el apiario pertenezca al usuario.
    Lanza HTTPException si no existe o no pertenece al usuario.
    
    Args:
        apiary: El apiario a verificar (puede ser None)
        user_id: ID del usuario que debe ser el dueño
        
    Raises:
        HTTPException: Si el apiario no existe o no pertenece al usuario
    """
    if not apiary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Apiary not found"
        )
    
    if apiary.userId != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This apiary does not belong to you"
        )

def safe_int_convert(value: Optional[str], default: Optional[int] = None) -> Optional[int]:
    """
    Convierte un string a int de forma segura.
    
    Args:
        value: String a convertir
        default: Valor por defecto si la conversión falla
        
    Returns:
        int o None
    """
    if not value:
        return default
    try:
        return int(value)
    except (ValueError, TypeError):
        return default

def safe_float_convert(value: Optional[str], default: Optional[float] = None) -> Optional[float]:
    """
    Convierte un string a float de forma segura.
    
    Args:
        value: String a convertir
        default: Valor por defecto si la conversión falla
        
    Returns:
        float o None
    """
    if not value:
        return default
    try:
        return float(value)
    except (ValueError, TypeError):
        return default

def build_apiary_detail(apiary: Apiary) -> ApiaryDetail:
    """
    Construye un ApiaryDetail desde un modelo Apiary.
    Elimina código duplicado en endpoints.
    
    Args:
        apiary: Modelo Apiary
        
    Returns:
        ApiaryDetail schema
    """
    return ApiaryDetail(
        id=apiary.id,
        name=apiary.name,
        userId=apiary.userId,
        image=apiary.image,
        hives=apiary.hives,
        status=apiary.status,
        honey=apiary.honey,
        levudex=apiary.levudex,
        sugar=apiary.sugar,
        box=apiary.box,
        boxMedium=apiary.boxMedium,
        boxSmall=apiary.boxSmall,
        tOxalic=apiary.tOxalic,
        tAmitraz=apiary.tAmitraz,
        tFlumetrine=apiary.tFlumetrine,
        tFence=apiary.tFence,
        tComment=apiary.tComment,
        transhumance=apiary.transhumance,
        latitude=apiary.latitude,
        longitude=apiary.longitude,
        createdAt=apiary.createdAt,
        updatedAt=apiary.updatedAt
    )

