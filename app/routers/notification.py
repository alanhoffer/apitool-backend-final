from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.dependencies import get_current_user
from app.schemas.notification import (
    NotificationMarkAllReadResponse,
    NotificationResponse,
    NotificationSummaryResponse,
)
from app.models.user import User
from app.services.notification_service import NotificationService
from typing import List

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("/summary", response_model=NotificationSummaryResponse)
async def get_my_notifications_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    service = NotificationService(db)
    return service.get_user_notification_counts(current_user.id)


@router.get("", response_model=List[NotificationResponse])
async def get_my_notifications(
    unread_only: bool = False,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    service = NotificationService(db)
    return service.get_user_notifications(current_user.id, unread_only)


@router.put("/read-all", response_model=NotificationMarkAllReadResponse)
async def mark_all_as_read(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    service = NotificationService(db)
    marked_count = service.mark_all_as_read(current_user.id)
    return {"markedCount": marked_count}


@router.put("/{id}/read")
async def mark_as_read(
    id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    service = NotificationService(db)
    success = service.mark_as_read(id, current_user.id)
    if not success:
        raise HTTPException(status_code=404, detail="Notification not found")
    return {"message": "Marked as read"}
