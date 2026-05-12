from pydantic import BaseModel, EmailStr, Field
from typing import Dict, List, Literal, Optional
from datetime import date, datetime
from app.models.user import Role

class CreateUser(BaseModel):
    name: str = Field(..., min_length=3)
    surname: str = Field(..., min_length=3)
    email: EmailStr
    password: str = Field(..., min_length=7)

class LoginUser(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=7)

class PushTokenUpdate(BaseModel):
    token: str
    deviceName: Optional[str] = None  # Nombre del dispositivo (ej: "iPhone 12", "Samsung Galaxy")
    platform: Optional[str] = None    # Plataforma: "ios" o "android"

class UserResponse(BaseModel):
    id: int
    name: str
    surname: str
    email: str
    createdAt: datetime
    authStrategy: Optional[str] = None
    role: Role
    expoPushToken: Optional[str] = None
    
    class Config:
        from_attributes = True


class DashboardSummaryResponse(BaseModel):
    id: int
    name: str
    surname: str
    role: Role
    apiaryCount: int
    hiveCount: int
    harvestedApiaryCount: int
    pendingTaskCount: int
    overdueTaskCount: int
    dueTodayTaskCount: int
    completedTaskCount: int
    completionRate: float
    unreadNotificationCount: int
    totalHoneyKg: float
    totalSugarKg: float
    totalLevudexKg: float
    totalHarvestBoxes: int
    recentHarvestBoxesToday: int
    weakHiveCount: int
    queenIssueHiveCount: int
    swarmingHiveCount: int
    staleInspectionHiveCount: int
    attentionHiveCount: int


class HarvestSeriesPointResponse(BaseModel):
    label: str
    startDate: date
    endDate: date
    box: int
    boxMedium: int
    boxSmall: int
    total: int


class StatisticsOverviewResponse(BaseModel):
    period: Literal["day", "week", "month", "year"]
    generatedAt: datetime
    apiaryCount: int
    hiveCount: int
    harvestedApiaryCount: int
    pendingTaskCount: int
    overdueTaskCount: int
    dueTodayTaskCount: int
    completedTaskCount: int
    completionRate: float
    unreadNotificationCount: int
    totalHoneyKg: float
    totalSugarKg: float
    totalLevudexKg: float
    totalHarvestBoxes: int
    periodHarvestBoxes: int
    recentHarvestBoxesToday: int
    weakHiveCount: int
    queenIssueHiveCount: int
    swarmingHiveCount: int
    staleInspectionHiveCount: int
    attentionHiveCount: int
    apiaryStatusCounts: Dict[str, int]
    hiveStrengthCounts: Dict[str, int]
    harvestSeries: List[HarvestSeriesPointResponse]
    
class UpdateProfileRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=3)
    email: Optional[EmailStr] = None

class ChangePasswordRequest(BaseModel):
    currentPassword: str = Field(..., min_length=7)
    newPassword: str = Field(..., min_length=7)

class DeleteAccountRequest(BaseModel):
    currentPassword: str = Field(..., min_length=7)
