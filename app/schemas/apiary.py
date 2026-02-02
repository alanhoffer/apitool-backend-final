from __future__ import annotations

from pydantic import BaseModel, Field, ConfigDict, model_serializer
from typing import Optional, TYPE_CHECKING, Any
from datetime import datetime
from decimal import Decimal

# Importar SettingsResponse directamente para Pydantic v2
# Si hay importación circular, se manejará con model_rebuild()
try:
    from app.schemas.settings import SettingsResponse
except ImportError:
    # Si hay importación circular, usar TYPE_CHECKING
    if TYPE_CHECKING:
        from app.schemas.settings import SettingsResponse
    else:
        SettingsResponse = None  # Se resolverá más tarde con model_rebuild()

class CreateApiary(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description="Apiary name")
    hives: int = Field(..., ge=0, description="Number of hives (must be >= 0)")
    status: str = Field(default="normal", description="Apiary status")
    image: Optional[str] = None
    honey: Optional[Decimal] = Field(None, ge=0, description="Honey amount (must be >= 0)")
    levudex: Optional[Decimal] = Field(None, ge=0, description="Levudex amount (must be >= 0)")
    sugar: Optional[Decimal] = Field(None, ge=0, description="Sugar amount (must be >= 0)")
    box: Optional[int] = Field(None, ge=0, description="Box count (must be >= 0)")
    boxMedium: Optional[int] = Field(None, ge=0, description="Medium box count (must be >= 0)")
    boxSmall: Optional[int] = Field(None, ge=0, description="Small box count (must be >= 0)")
    tOxalic: Optional[int] = Field(None, ge=0, description="Oxalic treatment days (must be >= 0)")
    tAmitraz: Optional[int] = Field(None, ge=0, description="Amitraz treatment days (must be >= 0)")
    tFlumetrine: Optional[int] = Field(None, ge=0, description="Flumetrine treatment days (must be >= 0)")
    tFence: Optional[int] = Field(None, ge=0, description="Fence treatment days (must be >= 0)")
    tComment: Optional[str] = Field(None, max_length=1000, description="Treatment comment")
    transhumance: Optional[int] = Field(None, ge=0, description="Transhumance days (must be >= 0)")
    latitude: Optional[float] = Field(None, ge=-90, le=90, description="Latitude coordinate")
    longitude: Optional[float] = Field(None, ge=-180, le=180, description="Longitude coordinate")
    settings: str = Field(default="{}", description="Settings as JSON string")

class UpdateApiary(BaseModel):
    image: Optional[str] = None
    hives: Optional[int] = Field(None, ge=0, description="Number of hives (must be >= 0)")
    status: Optional[str] = None
    honey: Optional[Decimal] = Field(None, ge=0, description="Honey amount (must be >= 0)")
    levudex: Optional[Decimal] = Field(None, ge=0, description="Levudex amount (must be >= 0)")
    sugar: Optional[Decimal] = Field(None, ge=0, description="Sugar amount (must be >= 0)")
    box: Optional[int] = Field(None, ge=0, description="Box count (must be >= 0)")
    boxMedium: Optional[int] = Field(None, ge=0, description="Medium box count (must be >= 0)")
    boxSmall: Optional[int] = Field(None, ge=0, description="Small box count (must be >= 0)")
    tOxalic: Optional[int] = Field(None, ge=0, description="Oxalic treatment days (must be >= 0)")
    tAmitraz: Optional[int] = Field(None, ge=0, description="Amitraz treatment days (must be >= 0)")
    tFlumetrine: Optional[int] = Field(None, ge=0, description="Flumetrine treatment days (must be >= 0)")
    tFence: Optional[int] = Field(None, ge=0, description="Fence treatment days (must be >= 0)")
    tComment: Optional[str] = Field(None, max_length=1000, description="Treatment comment")
    transhumance: Optional[int] = Field(None, ge=0, description="Transhumance days (must be >= 0)")
    latitude: Optional[float] = Field(None, ge=-90, le=90, description="Latitude coordinate")
    longitude: Optional[float] = Field(None, ge=-180, le=180, description="Longitude coordinate")

class ApiaryResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
    )
    
    # Usar nombres sin _ pero con alias para mantener compatibilidad
    id: int = Field(alias="_id")
    name: str = Field(alias="_name")
    hives: int = Field(alias="_hives")
    status: str = Field(alias="_status")
    image: str = Field(alias="_image")
    honey: Decimal = Field(alias="_honey")
    levudex: Decimal = Field(alias="_levudex")
    sugar: Decimal = Field(alias="_sugar")
    box: int = Field(alias="_box")
    boxMedium: int = Field(alias="_boxMedium")
    boxSmall: int = Field(alias="_boxSmall")
    tOxalic: int = Field(alias="_tOxalic")
    tAmitraz: int = Field(alias="_tAmitraz")
    tFlumetrine: int = Field(alias="_tFlumetrine")
    tFence: int = Field(alias="_tFence")
    tComment: str = Field(alias="_tComment")
    transhumance: Optional[int] = Field(default=None, alias="_transhumance")
    settings: Optional['SettingsResponse'] = Field(default=None, alias="_settings")
    updatedAt: datetime = Field(alias="_updatedAt")

class ApiaryDetail(BaseModel):
    id: int
    name: str
    userId: int
    image: str
    hives: int
    status: str
    honey: Optional[Decimal] = None
    levudex: Optional[Decimal] = None
    sugar: Optional[Decimal] = None
    box: int
    boxMedium: int
    boxSmall: int
    tOxalic: int
    tAmitraz: int
    tFlumetrine: int
    tFence: int
    tComment: str
    transhumance: Optional[int] = None
    latitude: Optional[Decimal] = None
    longitude: Optional[Decimal] = None
    createdAt: datetime
    updatedAt: datetime
    
    class Config:
        from_attributes = True

class BoxStats(BaseModel):
    """Estadísticas de alzas cosechadas."""
    box: int
    boxMedium: int
    boxSmall: int
    total: Optional[int] = None

class HarvestedCounts(BaseModel):
    """Cantidad de apiarios cosechados y total de colmenas."""
    apiaryCount: int
    hiveCount: int

class HarvestedTodayCounts(BaseModel):
    """Cantidad de apiarios y colmenas cosechados en el día."""
    apiaryCount: int
    hiveCount: int

# Resolver forward references para Pydantic v2
# Esto debe ejecutarse después de que todos los módulos estén cargados
def _resolve_forward_refs():
    """Resuelve referencias forward después de que todos los módulos estén cargados."""
    try:
        # Asegurarse de que SettingsResponse esté importado
        from app.schemas import settings
        # Reconstruir el modelo para resolver las referencias forward
        ApiaryResponse.model_rebuild()
    except (ImportError, AttributeError):
        # Si hay un error, se intentará resolver más tarde cuando se importe el módulo
        pass

# Intentar resolver las referencias forward al cargar el módulo
try:
    _resolve_forward_refs()
except Exception:
    pass
