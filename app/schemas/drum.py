from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from decimal import Decimal

class DrumCreate(BaseModel):
    code: str
    tare: Decimal
    weight: Decimal

class DrumUpdate(BaseModel):
    code: Optional[str] = None
    tare: Optional[Decimal] = None
    weight: Optional[Decimal] = None
    sold: Optional[bool] = None

class DrumSoldUpdate(BaseModel):
    sold: bool

class DrumResponse(BaseModel):
    id: int
    userId: int
    code: str
    tare: Decimal
    weight: Decimal
    sold: bool
    createdAt: datetime
    updatedAt: datetime
    
    class Config:
        from_attributes = True

class DrumStats(BaseModel):
    total: int
    sold: int
    not_sold: int
    total_tare: Decimal
    total_weight: Decimal
    net_weight: Decimal

class DrumsListResponse(BaseModel):
    data: List[DrumResponse]
    pagination: dict
