from pydantic import BaseModel
from typing import Optional, List

class SeasonalTipBase(BaseModel):
    title: str
    content: str
    season: Optional[str] = None
    months: Optional[str] = None
    category: str = "General"
    isActive: bool = True

class SeasonalTipCreate(SeasonalTipBase):
    pass

class SeasonalTipResponse(SeasonalTipBase):
    id: int

    class Config:
        from_attributes = True

class RecommendationsResponse(BaseModel):
    current_season: str
    current_month: int
    tips: List[SeasonalTipResponse]

