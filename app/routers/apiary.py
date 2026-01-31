from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Request
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.dependencies import get_current_user_payload
from app.services.apiary_service import ApiaryService
from app.services.user_service import UserService
from app.services.settings_service import SettingsService
from app.schemas.apiary import CreateApiary, UpdateApiary, ApiaryResponse, ApiaryDetail, BoxStats, HarvestedCounts, HarvestedTodayCounts
from app.schemas.settings import UpdateSettings
from app.schemas.history import HistoryResponse
from app.models.apiary import Apiary
from typing import List
import uuid
import os
from pathlib import Path

router = APIRouter(prefix="/apiarys", tags=["apiarys"])

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

@router.get("/{id}", response_model=ApiaryDetail)
async def get_apiary(
    id: int,
    payload: dict = Depends(get_current_user_payload),
    db: Session = Depends(get_db)
):
    apiary_service = ApiaryService(db)
    apiary = apiary_service.get_apiary(id)
    
    if not apiary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Apiary not exists"
        )
    
    user_id = int(payload.get("sub"))
    if apiary.userId != user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="This apiary is not yours"
        )
    
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
        createdAt=apiary.createdAt,
        updatedAt=apiary.updatedAt
    )

@router.get("/{id}/harvested", response_model=BoxStats)
async def get_apiary_harvested_totals(
    id: int,
    payload: dict = Depends(get_current_user_payload),
    db: Session = Depends(get_db)
):
    """Obtiene alzas cosechadas acumuladas por apiario."""
    apiary_service = ApiaryService(db)
    apiary = apiary_service.get_apiary(id)

    if not apiary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Apiary not exists"
        )

    user_id = int(payload.get("sub"))
    if apiary.userId != user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="This apiary is not yours"
        )

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
        name=form.get("name"),
        hives=int(form.get("hives", 0)),
        status=form.get("status", "normal"),
        honey=float(form.get("honey", 0)) if form.get("honey") else None,
        levudex=float(form.get("levudex", 0)) if form.get("levudex") else None,
        sugar=float(form.get("sugar", 0)) if form.get("sugar") else None,
        box=int(form.get("box", 0)) if form.get("box") else None,
        boxMedium=int(form.get("boxMedium", 0)) if form.get("boxMedium") else None,
        boxSmall=int(form.get("boxSmall", 0)) if form.get("boxSmall") else None,
        tOxalic=int(form.get("tOxalic", 0)) if form.get("tOxalic") else None,
        tAmitraz=int(form.get("tAmitraz", 0)) if form.get("tAmitraz") else None,
        tFlumetrine=int(form.get("tFlumetrine", 0)) if form.get("tFlumetrine") else None,
        tFence=int(form.get("tFence", 0)) if form.get("tFence") else None,
        tComment=form.get("tComment"),
        transhumance=int(form.get("transhumance", 0)) if form.get("transhumance") else None,
        settings=form.get("settings", "{}")
    )
    
    apiary_service = ApiaryService(db)
    apiary_created = await apiary_service.create_apiary(user_id, apiary_data, file)
    
    if not apiary_created:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return ApiaryDetail(
        id=apiary_created.id,
        name=apiary_created.name,
        userId=apiary_created.userId,
        image=apiary_created.image,
        hives=apiary_created.hives,
        status=apiary_created.status,
        honey=apiary_created.honey,
        levudex=apiary_created.levudex,
        sugar=apiary_created.sugar,
        box=apiary_created.box,
        boxMedium=apiary_created.boxMedium,
        boxSmall=apiary_created.boxSmall,
        tOxalic=apiary_created.tOxalic,
        tAmitraz=apiary_created.tAmitraz,
        tFlumetrine=apiary_created.tFlumetrine,
        tFence=apiary_created.tFence,
        tComment=apiary_created.tComment,
        transhumance=apiary_created.transhumance,
        createdAt=apiary_created.createdAt,
        updatedAt=apiary_created.updatedAt
    )

@router.delete("/{id}")
async def delete_apiary(
    id: int,
    payload: dict = Depends(get_current_user_payload),
    db: Session = Depends(get_db)
):
    apiary_service = ApiaryService(db)
    apiary = apiary_service.get_apiary(id)
    
    if not apiary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Apiary not exists"
        )
    
    user_id = int(payload.get("sub"))
    if apiary.userId != user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="This apiary is not yours"
        )
    
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
    
    if not apiary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Apiary not exists"
        )
    
    user_id = int(payload.get("sub"))
    if apiary.userId != user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="This apiary is not yours"
        )
    
    form = await request.form()
    update_data = UpdateApiary(
        hives=int(form.get("hives")) if form.get("hives") else None,
        status=form.get("status"),
        honey=float(form.get("honey")) if form.get("honey") else None,
        levudex=float(form.get("levudex")) if form.get("levudex") else None,
        sugar=float(form.get("sugar")) if form.get("sugar") else None,
        box=int(form.get("box")) if form.get("box") else None,
        boxMedium=int(form.get("boxMedium")) if form.get("boxMedium") else None,
        boxSmall=int(form.get("boxSmall")) if form.get("boxSmall") else None,
        tOxalic=int(form.get("tOxalic")) if form.get("tOxalic") else None,
        tAmitraz=int(form.get("tAmitraz")) if form.get("tAmitraz") else None,
        tFlumetrine=int(form.get("tFlumetrine")) if form.get("tFlumetrine") else None,
        tFence=int(form.get("tFence")) if form.get("tFence") else None,
        tComment=form.get("tComment"),
        transhumance=int(form.get("transhumance")) if form.get("transhumance") else None
    )
    
    updated_apiary = await apiary_service.update_apiary(id, update_data, file)
    if not updated_apiary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Apiary not found"
        )
    
    return ApiaryDetail(
        id=updated_apiary.id,
        name=updated_apiary.name,
        userId=updated_apiary.userId,
        image=updated_apiary.image,
        hives=updated_apiary.hives,
        status=updated_apiary.status,
        honey=updated_apiary.honey,
        levudex=updated_apiary.levudex,
        sugar=updated_apiary.sugar,
        box=updated_apiary.box,
        boxMedium=updated_apiary.boxMedium,
        boxSmall=updated_apiary.boxSmall,
        tOxalic=updated_apiary.tOxalic,
        tAmitraz=updated_apiary.tAmitraz,
        tFlumetrine=updated_apiary.tFlumetrine,
        tFence=updated_apiary.tFence,
        tComment=updated_apiary.tComment,
        transhumance=updated_apiary.transhumance,
        createdAt=updated_apiary.createdAt,
        updatedAt=updated_apiary.updatedAt
    )

@router.get("/profile/image/{id}")
async def get_file(id: str):
    file_path = UPLOAD_DIR / id
    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )
    return FileResponse(file_path, media_type="image/jpeg")

@router.get("", response_model=List[ApiaryResponse])
async def get_apiarys(
    payload: dict = Depends(get_current_user_payload),
    db: Session = Depends(get_db)
):
    apiary_service = ApiaryService(db)
    user_id = int(payload.get("sub"))
    apiary_array = apiary_service.get_all_by_user_id(user_id)
    
    if not apiary_array:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return apiary_array

@router.get("/history/{id}", response_model=List[HistoryResponse])
async def get_apiary_history(
    id: int,
    payload: dict = Depends(get_current_user_payload),
    db: Session = Depends(get_db)
):
    apiary_service = ApiaryService(db)
    apiary = apiary_service.get_apiary(id)
    
    if not apiary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="This apiary not exists"
        )
    
    user_id = int(payload.get("sub"))
    if apiary.userId != user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="This apiary is not yours"
        )
    
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

