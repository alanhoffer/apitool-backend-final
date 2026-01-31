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
    
    class Config:
        from_attributes = True

