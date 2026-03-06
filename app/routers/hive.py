from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.hive import HiveCreate, HiveResponse, HiveUpdate, HivesListResponse
from app.schemas.hive_history import HiveHistoryResponse
from app.services.hive_service import HiveService

router = APIRouter(prefix="/hives", tags=["hives"])


@router.post("", response_model=HiveResponse, status_code=status.HTTP_201_CREATED)
async def create_hive(
    hive_data: HiveCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = HiveService(db)
    hive = service.create_hive(current_user.id, hive_data)
    if not hive:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Apiary not found",
        )
    return hive


@router.get("", response_model=HivesListResponse)
async def get_hives(
    apiary_id: Optional[int] = Query(None, description="Filter by apiary ID"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = HiveService(db)
    return {"data": service.get_hives(current_user.id, apiary_id)}


@router.get("/{id}", response_model=HiveResponse)
async def get_hive(
    id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = HiveService(db)
    hive = service.get_hive_by_id(id, current_user.id)
    if not hive:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Hive not found",
        )
    return hive


@router.get("/{id}/history", response_model=list[HiveHistoryResponse])
async def get_hive_history(
    id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = HiveService(db)
    hive = service.get_hive_by_id(id, current_user.id)
    if not hive:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Hive not found",
        )
    return service.get_hive_history(id, current_user.id)


@router.put("/{id}", response_model=HiveResponse)
async def update_hive(
    id: int,
    updates: HiveUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = HiveService(db)
    hive = service.update_hive(id, current_user.id, updates)
    if not hive:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Hive not found",
        )
    return hive


@router.delete("/{id}")
async def delete_hive(
    id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = HiveService(db)
    if not service.delete_hive(id, current_user.id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Hive not found",
        )
    return {"message": "Hive deleted successfully"}
