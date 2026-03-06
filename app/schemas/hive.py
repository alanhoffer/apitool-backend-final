from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from decimal import Decimal


class HiveBase(BaseModel):
    apiaryId: int = Field(..., gt=0)
    name: str = Field(..., min_length=1, max_length=255)
    image: str = ""
    status: str = "normal"
    honey: Decimal = Field(default=Decimal("0"), ge=0)
    levudex: Decimal = Field(default=Decimal("0"), ge=0)
    sugar: Decimal = Field(default=Decimal("0"), ge=0)
    tOxalic: int = Field(default=0, ge=0)
    tAmitraz: int = Field(default=0, ge=0)
    tFlumetrine: int = Field(default=0, ge=0)
    disease: str = ""
    box: int = Field(default=0, ge=0)
    boxMedium: int = Field(default=0, ge=0)
    boxSmall: int = Field(default=0, ge=0)
    production: Decimal = Field(default=Decimal("0"), ge=0)
    queenStatus: str = "unknown"
    population: int = Field(default=0, ge=0)
    broodFrames: int = Field(default=0, ge=0)
    honeyFrames: int = Field(default=0, ge=0)
    pollenFrames: int = Field(default=0, ge=0)
    hiveStrength: str = "medium"
    swarming: bool = False
    lastInspection: str = ""
    tComment: str = ""


class HiveCreate(HiveBase):
    pass


class HiveUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    image: Optional[str] = None
    status: Optional[str] = None
    honey: Optional[Decimal] = Field(None, ge=0)
    levudex: Optional[Decimal] = Field(None, ge=0)
    sugar: Optional[Decimal] = Field(None, ge=0)
    tOxalic: Optional[int] = Field(None, ge=0)
    tAmitraz: Optional[int] = Field(None, ge=0)
    tFlumetrine: Optional[int] = Field(None, ge=0)
    disease: Optional[str] = None
    box: Optional[int] = Field(None, ge=0)
    boxMedium: Optional[int] = Field(None, ge=0)
    boxSmall: Optional[int] = Field(None, ge=0)
    production: Optional[Decimal] = Field(None, ge=0)
    queenStatus: Optional[str] = None
    population: Optional[int] = Field(None, ge=0)
    broodFrames: Optional[int] = Field(None, ge=0)
    honeyFrames: Optional[int] = Field(None, ge=0)
    pollenFrames: Optional[int] = Field(None, ge=0)
    hiveStrength: Optional[str] = None
    swarming: Optional[bool] = None
    lastInspection: Optional[str] = None
    tComment: Optional[str] = None


class HiveResponse(HiveBase):
    id: int
    userId: int
    createdAt: datetime
    updatedAt: datetime

    class Config:
        from_attributes = True


class HivesListResponse(BaseModel):
    data: List[HiveResponse]
