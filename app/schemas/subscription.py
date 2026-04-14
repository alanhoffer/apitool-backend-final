from pydantic import BaseModel
from typing import Optional
from datetime import datetime


TIER_APIARY_LIMITS = {
    "aprendiz": 5,
    "apicultor": 20,
    "maestro": None,  # ilimitado
}

TIER_AI_ACCESS = {
    "aprendiz": False,
    "apicultor": True,
    "maestro": True,
}

TIER_AI_MONTHLY_LIMIT = {
    "aprendiz": 0,
    "apicultor": 20,
    "maestro": None,  # ilimitado
}


class SubscriptionResponse(BaseModel):
    id: int
    userId: int
    tier: str
    status: str
    expiresAt: Optional[datetime] = None
    createdAt: datetime
    apiaryLimit: Optional[int]
    aiAccess: bool
    aiMonthlyLimit: Optional[int]

    class Config:
        from_attributes = True


class SubscriptionUpdate(BaseModel):
    tier: str
    status: str
    revenuecatCustomerId: Optional[str] = None
    expiresAt: Optional[datetime] = None


class RevenueCatWebhookEvent(BaseModel):
    event: dict
