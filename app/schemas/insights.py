from __future__ import annotations

from pydantic import BaseModel
from typing import List, Optional


class HiveHealthSummaryResponse(BaseModel):
    score: int
    status: str
    alerts: List[str]
    recommendedActions: List[str]
    flags: List[str]
    lastInspectionDays: Optional[int] = None


class ApiaryWeatherInsightResponse(BaseModel):
    temperatureC: Optional[float] = None
    feelsLikeC: Optional[float] = None
    humidity: Optional[int] = None
    windKph: Optional[float] = None
    condition: Optional[str] = None
    inspectionWindow: Optional[str] = None


class ApiaryRecommendationResponse(BaseModel):
    priority: str
    title: str
    description: str
    affectedHives: int = 0


class ApiaryInsightsResponse(BaseModel):
    apiaryId: int
    apiaryName: str
    managementType: str
    healthScore: int
    healthStatus: str
    attentionHiveCount: int
    criticalHiveCount: int
    pendingTaskCount: int
    overdueTaskCount: int
    weather: Optional[ApiaryWeatherInsightResponse] = None
    recommendations: List[ApiaryRecommendationResponse]
