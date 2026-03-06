from pydantic import BaseModel
from typing import Optional

class CreateSettings(BaseModel):
    honey: bool = True
    levudex: bool = True
    sugar: bool = True
    box: bool = True
    boxMedium: bool = True
    boxSmall: bool = True
    tOxalic: bool = True
    tAmitraz: bool = True
    tFlumetrine: bool = True
    tFence: bool = True
    tComment: bool = True
    transhumance: bool = True
    harvesting: bool = False
    queenStatus: bool = False
    population: bool = False
    broodFrames: bool = False
    honeyFrames: bool = False
    pollenFrames: bool = False
    lastInspection: bool = False
    hiveStrength: bool = False
    swarming: bool = False
    disease: bool = False
    production: bool = False

class UpdateSettings(BaseModel):
    apiaryId: int
    apiaryUserId: int
    honey: Optional[bool] = None
    levudex: Optional[bool] = None
    sugar: Optional[bool] = None
    box: Optional[bool] = None
    boxMedium: Optional[bool] = None
    boxSmall: Optional[bool] = None
    tOxalic: Optional[bool] = None
    tAmitraz: Optional[bool] = None
    tFlumetrine: Optional[bool] = None
    tFence: Optional[bool] = None
    tComment: Optional[bool] = None
    transhumance: Optional[bool] = None
    harvesting: Optional[bool] = None
    queenStatus: Optional[bool] = None
    population: Optional[bool] = None
    broodFrames: Optional[bool] = None
    honeyFrames: Optional[bool] = None
    pollenFrames: Optional[bool] = None
    lastInspection: Optional[bool] = None
    hiveStrength: Optional[bool] = None
    swarming: Optional[bool] = None
    disease: Optional[bool] = None
    production: Optional[bool] = None
    tasks: Optional[str] = None

class SettingsResponse(BaseModel):
    id: int
    apiaryId: int
    apiaryUserId: int
    honey: bool
    levudex: bool
    sugar: bool
    box: bool
    boxMedium: bool
    boxSmall: bool
    tOxalic: bool
    tAmitraz: bool
    tFlumetrine: bool
    tFence: bool
    tComment: bool
    transhumance: bool
    harvesting: bool
    queenStatus: bool
    population: bool
    broodFrames: bool
    honeyFrames: bool
    pollenFrames: bool
    lastInspection: bool
    hiveStrength: bool
    swarming: bool
    disease: bool
    production: bool
    tasks: Optional[str] = None
    
    class Config:
        from_attributes = True
