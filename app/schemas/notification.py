from pydantic import BaseModel
from datetime import datetime

class NotificationBase(BaseModel):
    title: str
    message: str
    type: str = "INFO"

class NotificationCreate(NotificationBase):
    userId: int

class NotificationResponse(NotificationBase):
    id: int
    isRead: bool
    createdAt: datetime

    class Config:
        from_attributes = True


