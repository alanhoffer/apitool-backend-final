from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Dict, Any

class NotificationBase(BaseModel):
    title: str
    message: str
    type: str = "INFO"

class NotificationCreate(NotificationBase):
    userId: int

class NotificationResponse(NotificationBase):
    id: int
    isRead: bool
    data: Optional[Dict[str, Any]] = None
    createdAt: datetime

    class Config:
        from_attributes = True


class NotificationSummaryResponse(BaseModel):
    totalCount: int
    unreadCount: int


class NotificationMarkAllReadResponse(BaseModel):
    markedCount: int

