"""
Helper functions to reduce code duplication.
"""
from decimal import Decimal
from fastapi import HTTPException, status
from app.models.apiary import Apiary
from app.models.settings import Settings
from app.schemas.apiary import ApiaryDetail
from app.schemas.settings import SettingsResponse
from app.services.blob_storage_service import BlobStorageService
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

def safe_bool(value: Optional[bool], default: bool = False) -> bool:
    if value is None:
        return default
    return bool(value)

def build_settings_response(settings: Optional[Settings]) -> Optional[SettingsResponse]:
    if not settings:
        return None

    return SettingsResponse(
        id=settings.id,
        apiaryId=settings.apiaryId,
        apiaryUserId=settings.apiaryUserId,
        honey=safe_bool(settings.honey),
        levudex=safe_bool(settings.levudex),
        sugar=safe_bool(settings.sugar),
        box=safe_bool(settings.box),
        boxMedium=safe_bool(settings.boxMedium),
        boxSmall=safe_bool(settings.boxSmall),
        tOxalic=safe_bool(settings.tOxalic),
        tAmitraz=safe_bool(settings.tAmitraz),
        tFlumetrine=safe_bool(settings.tFlumetrine),
        tFence=safe_bool(settings.tFence),
        transhumance=safe_bool(settings.transhumance),
        queenStatus=safe_bool(settings.queenStatus),
        population=safe_bool(settings.population),
        broodFrames=safe_bool(settings.broodFrames),
        honeyFrames=safe_bool(settings.honeyFrames),
        pollenFrames=safe_bool(settings.pollenFrames),
        lastInspection=safe_bool(settings.lastInspection),
        hiveStrength=safe_bool(settings.hiveStrength),
        swarming=safe_bool(settings.swarming),
        disease=safe_bool(settings.disease),
        production=safe_bool(settings.production),
        tasks=safe_bool(settings.tasks),
    )

def build_apiary_detail(apiary: Apiary) -> ApiaryDetail:
    """
    Construye un ApiaryDetail desde un modelo Apiary.
    Elimina código duplicado en endpoints.
    
    Args:
        apiary: Modelo Apiary
        
    Returns:
        ApiaryDetail schema
    """
    image_url = BlobStorageService().resolve_public_url(apiary.image)

    return ApiaryDetail(
        id=apiary.id,
        name=apiary.name or "",
        userId=apiary.userId,
        image=apiary.image,
        imageUrl=image_url,
        hives=apiary.hives or 0,
        status=apiary.status or "normal",
        honey=apiary.honey if apiary.honey is not None else Decimal(0),
        levudex=apiary.levudex if apiary.levudex is not None else Decimal(0),
        sugar=apiary.sugar if apiary.sugar is not None else Decimal(0),
        box=apiary.box or 0,
        boxMedium=apiary.boxMedium or 0,
        boxSmall=apiary.boxSmall or 0,
        tOxalic=apiary.tOxalic or 0,
        tAmitraz=apiary.tAmitraz or 0,
        tFlumetrine=apiary.tFlumetrine or 0,
        tFence=apiary.tFence or 0,
        transhumance=apiary.transhumance,
        managementType=apiary.managementType or "apiary",
        latitude=apiary.latitude,
        longitude=apiary.longitude,
        createdAt=apiary.createdAt,
        updatedAt=apiary.updatedAt,
        settings=build_settings_response(apiary.settings)
    )
