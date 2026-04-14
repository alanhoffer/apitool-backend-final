from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Request
from fastapi.responses import FileResponse, RedirectResponse, StreamingResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.dependencies import get_current_user_payload
from app.services.apiary_service import ApiaryService
from app.services.user_service import UserService
from app.services.settings_service import SettingsService
from app.services.subscription_service import SubscriptionService
from app.schemas.apiary import CreateApiary, UpdateApiary, ApiaryResponse, ApiaryDetail, BoxStats, HarvestedCounts, HarvestedTodayCounts
from app.schemas.settings import UpdateSettings
from app.schemas.history import HistoryResponse
from app.models.apiary import Apiary
from app.runtime import get_upload_dir
from app.services.blob_storage_service import BlobStorageService, is_blob_path
from app.utils.helpers import verify_apiary_ownership, build_apiary_detail, safe_int_convert, safe_float_convert
from typing import List
import uuid
import os
from pathlib import Path
import re

router = APIRouter(prefix="/apiarys", tags=["apiarys"])

UPLOAD_DIR = get_upload_dir()
UPLOAD_DIR.mkdir(exist_ok=True)
IMAGE_REF_RE = re.compile(r"^(?!/)(?!.*//)(?!.*\.\.)[A-Za-z0-9/_-]{1,255}\.(jpg|jpeg|png|gif|webp)$")

@router.get("/{id}", response_model=ApiaryDetail)
async def get_apiary(
    id: int,
    payload: dict = Depends(get_current_user_payload),
    db: Session = Depends(get_db)
):
    apiary_service = ApiaryService(db)
    apiary = apiary_service.get_apiary(id)
    user_id = int(payload.get("sub"))
    
    verify_apiary_ownership(apiary, user_id)
    
    return build_apiary_detail(apiary)

@router.get("/{id}/harvested", response_model=BoxStats)
async def get_apiary_harvested_totals(
    id: int,
    payload: dict = Depends(get_current_user_payload),
    db: Session = Depends(get_db)
):
    """Obtiene alzas cosechadas acumuladas por apiario."""
    apiary_service = ApiaryService(db)
    apiary = apiary_service.get_apiary(id)
    user_id = int(payload.get("sub"))
    
    verify_apiary_ownership(apiary, user_id)

    return apiary_service.get_harvested_totals_by_apiary(id)

@router.get("/all/count")
async def get_apiary_and_hive_counts(
    payload: dict = Depends(get_current_user_payload),
    db: Session = Depends(get_db)
):
    apiary_service = ApiaryService(db)
    user_id = int(payload.get("sub"))
    
    apiary_count = apiary_service.count_apiaries_by_user_id(user_id)
    hive_count = apiary_service.count_hives_by_user_id(user_id)
    
    return {
        "apiaryCount": apiary_count,
        "hiveCount": hive_count
    }

@router.get("/stats/boxes", response_model=BoxStats)
async def get_box_stats(
    payload: dict = Depends(get_current_user_payload),
    db: Session = Depends(get_db)
):
    """Obtiene estadísticas de alzas cosechadas del usuario."""
    apiary_service = ApiaryService(db)
    user_id = int(payload.get("sub"))
    
    return apiary_service.get_box_stats(user_id)

@router.get("/harvested/stats", response_model=BoxStats)
async def get_harvested_stats(
    payload: dict = Depends(get_current_user_payload),
    db: Session = Depends(get_db)
):
    """Obtiene totales de alzas cosechadas (box, boxMedium, boxSmall)."""
    apiary_service = ApiaryService(db)
    user_id = int(payload.get("sub"))
    
    return apiary_service.get_box_stats(user_id)

@router.get("/harvesting/count")
async def get_harvesting_count(
    payload: dict = Depends(get_current_user_payload),
    db: Session = Depends(get_db)
):
    """Obtiene la cantidad de apiarios en cosecha (harvesting = True)."""
    apiary_service = ApiaryService(db)
    user_id = int(payload.get("sub"))
    
    count = apiary_service.count_harvesting_apiaries(user_id)
    
    return {
        "harvestingCount": count
    }

@router.get("/harvested/count")
async def get_harvested_count(
    payload: dict = Depends(get_current_user_payload),
    db: Session = Depends(get_db)
):
    """Obtiene la cantidad de apiarios con alzas cosechadas."""
    apiary_service = ApiaryService(db)
    user_id = int(payload.get("sub"))
    
    count = apiary_service.count_harvested_apiaries(user_id)
    
    # Devuelve directamente el número (forma más simple)
    return count

@router.get("/harvested/counts", response_model=HarvestedCounts)
async def get_harvested_counts(
    payload: dict = Depends(get_current_user_payload),
    db: Session = Depends(get_db)
):
    """Obtiene cantidad de apiarios cosechados y total de colmenas."""
    apiary_service = ApiaryService(db)
    user_id = int(payload.get("sub"))

    apiary_count = apiary_service.count_harvested_apiaries(user_id)
    hive_count = apiary_service.count_hives_in_harvested_apiaries(user_id)

    return {
        "apiaryCount": apiary_count,
        "hiveCount": hive_count
    }

@router.get("/harvested/today/counts", response_model=HarvestedTodayCounts)
async def get_harvested_today_counts(
    payload: dict = Depends(get_current_user_payload),
    db: Session = Depends(get_db)
):
    """Obtiene cantidad de apiarios y colmenas cosechados hoy."""
    apiary_service = ApiaryService(db)
    user_id = int(payload.get("sub"))

    return apiary_service.count_harvested_today_apiaries_and_hives(user_id)

@router.get("/harvested/today/boxes", response_model=BoxStats)
async def get_harvested_today_boxes(
    payload: dict = Depends(get_current_user_payload),
    db: Session = Depends(get_db)
):
    """Obtiene cantidad de alzas cosechadas hoy (sumas por tipo)."""
    apiary_service = ApiaryService(db)
    user_id = int(payload.get("sub"))

    return apiary_service.get_harvested_today_box_stats(user_id)

@router.post("", response_model=ApiaryDetail)
async def create_apiary(
    request: Request,
    payload: dict = Depends(get_current_user_payload),
    db: Session = Depends(get_db),
    file: UploadFile = File(None)
):
    form = await request.form()
    user_id = int(payload.get("sub"))
    
    user_service = UserService(db)
    found_user = user_service.get_user(user_id)
    if not found_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    apiary_data = CreateApiary(
        name=form.get("name") or "",
        hives=safe_int_convert(form.get("hives"), 0) or 0,
        managementType=form.get("managementType") or "apiary",
        status=form.get("status", "normal"),
        honey=safe_float_convert(form.get("honey")),
        levudex=safe_float_convert(form.get("levudex")),
        sugar=safe_float_convert(form.get("sugar")),
        box=safe_int_convert(form.get("box")),
        boxMedium=safe_int_convert(form.get("boxMedium")),
        boxSmall=safe_int_convert(form.get("boxSmall")),
        tOxalic=safe_int_convert(form.get("tOxalic")),
        tAmitraz=safe_int_convert(form.get("tAmitraz")),
        tFlumetrine=safe_int_convert(form.get("tFlumetrine")),
        tFence=safe_int_convert(form.get("tFence")),
        transhumance=safe_int_convert(form.get("transhumance")),
        latitude=safe_float_convert(form.get("latitude")),
        longitude=safe_float_convert(form.get("longitude")),
        settings=form.get("settings", "{}")
    )
    
    apiary_service = ApiaryService(db)

    # Verificar límite de suscripción
    from app.models.apiary import Apiary as ApiaryModel
    current_count = db.query(ApiaryModel).filter(ApiaryModel.userId == user_id).count()
    subscription_service = SubscriptionService(db)
    if not subscription_service.check_apiary_limit(user_id, current_count):
        tier = subscription_service.get_tier(user_id)
        from app.schemas.subscription import TIER_APIARY_LIMITS
        limit = TIER_APIARY_LIMITS.get(tier)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Límite de apiarios alcanzado para tu plan ({limit} apiarios). Actualizá tu suscripción para agregar más."
        )

    apiary_created = await apiary_service.create_apiary(user_id, apiary_data, file)

    if not apiary_created:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return build_apiary_detail(apiary_created)

@router.delete("/{id}")
async def delete_apiary(
    id: int,
    payload: dict = Depends(get_current_user_payload),
    db: Session = Depends(get_db)
):
    apiary_service = ApiaryService(db)
    apiary = apiary_service.get_apiary(id)
    user_id = int(payload.get("sub"))
    
    verify_apiary_ownership(apiary, user_id)
    
    apiary_service.delete_apiary(id)
    return {"message": "Apiary deleted successfully"}

@router.put("/{id}", response_model=ApiaryDetail)
async def update_apiary(
    id: int,
    request: Request,
    payload: dict = Depends(get_current_user_payload),
    db: Session = Depends(get_db),
    file: UploadFile = File(None)
):
    apiary_service = ApiaryService(db)
    apiary = apiary_service.get_apiary(id)
    user_id = int(payload.get("sub"))
    
    verify_apiary_ownership(apiary, user_id)
    
    form = await request.form()
    update_data = UpdateApiary(
        managementType=form.get("managementType"),
        hives=safe_int_convert(form.get("hives")),
        status=form.get("status"),
        honey=safe_float_convert(form.get("honey")),
        levudex=safe_float_convert(form.get("levudex")),
        sugar=safe_float_convert(form.get("sugar")),
        box=safe_int_convert(form.get("box")),
        boxMedium=safe_int_convert(form.get("boxMedium")),
        boxSmall=safe_int_convert(form.get("boxSmall")),
        tOxalic=safe_int_convert(form.get("tOxalic")),
        tAmitraz=safe_int_convert(form.get("tAmitraz")),
        tFlumetrine=safe_int_convert(form.get("tFlumetrine")),
        tFence=safe_int_convert(form.get("tFence")),
        transhumance=safe_int_convert(form.get("transhumance")),
        latitude=safe_float_convert(form.get("latitude")),
        longitude=safe_float_convert(form.get("longitude"))
    )
    
    updated_apiary = await apiary_service.update_apiary(id, update_data, file)
    if not updated_apiary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Apiary not found"
        )
    
    return build_apiary_detail(updated_apiary)

@router.get("/profile/image/{id:path}")
async def get_file(id: str):
    if not IMAGE_REF_RE.match(id or ""):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file reference"
        )

    blob_url = BlobStorageService().resolve_public_url(id)
    if blob_url:
        return RedirectResponse(blob_url, status_code=status.HTTP_307_TEMPORARY_REDIRECT)

    if is_blob_path(id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )

    file_path = (UPLOAD_DIR / id).resolve()
    upload_root = UPLOAD_DIR.resolve()
    if upload_root not in file_path.parents:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file path"
        )

    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )
    
    # Detectar el tipo MIME según la extensión
    if id.endswith('.png'):
        media_type = "image/png"
    elif id.endswith('.jpg') or id.endswith('.jpeg'):
        media_type = "image/jpeg"
    elif id.endswith('.gif'):
        media_type = "image/gif"
    elif id.endswith('.webp'):
        media_type = "image/webp"
    else:
        media_type = "image/jpeg"  # Por defecto
    
    return FileResponse(file_path, media_type=media_type)

@router.get("", response_model=List[ApiaryResponse])
async def get_apiarys(
    payload: dict = Depends(get_current_user_payload),
    db: Session = Depends(get_db)
):
    """Obtiene todos los apiarios del usuario autenticado."""
    apiary_service = ApiaryService(db)
    user_id = int(payload.get("sub"))
    apiary_array = apiary_service.get_all_by_user_id(user_id)
    
    # Retornar lista vacía en lugar de error si no hay apiarios
    # Esto es más consistente con el comportamiento esperado
    return apiary_array

@router.get("/history/{id}", response_model=List[HistoryResponse])
async def get_apiary_history(
    id: int,
    payload: dict = Depends(get_current_user_payload),
    db: Session = Depends(get_db)
):
    apiary_service = ApiaryService(db)
    apiary = apiary_service.get_apiary(id)
    user_id = int(payload.get("sub"))
    
    verify_apiary_ownership(apiary, user_id)
    
    history = apiary_service.get_all_history(id)
    
    # Return empty list if no history exists - this is a valid response
    return history

@router.put("/settings/{id}")
async def update_apiary_settings(
    id: int,
    settings_data: UpdateSettings,
    payload: dict = Depends(get_current_user_payload),
    db: Session = Depends(get_db)
):
    user_id = int(payload.get("sub"))
    if settings_data.apiaryUserId != user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="This settings is not yours"
        )
    
    settings_service = SettingsService(db)
    found_settings = settings_service.get_settings(id)
    
    if not found_settings:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Settings not exists"
        )
    
    if settings_data.apiaryId != found_settings.apiaryId:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="This settings is not yours"
        )
    
    return settings_service.update_settings(id, settings_data)

@router.put("/harvest/all")
async def set_harvesting_for_all(
    body: dict,
    payload: dict = Depends(get_current_user_payload),
    db: Session = Depends(get_db)
):
    user_id = int(payload.get("sub"))
    harvesting = body.get("harvesting", False)
    
    settings_service = SettingsService(db)
    settings_service.set_harvesting_for_all_apiaries(user_id, harvesting)
    
    return {"message": "Harvesting status updated for all apiaries"}
