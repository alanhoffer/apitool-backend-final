from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class CreateDevice(BaseModel):
    """Schema para crear o actualizar un dispositivo."""
    model_config = {"populate_by_name": True}
    
    deviceName: str = Field(..., min_length=1, description="Nombre del dispositivo")
    modelName: Optional[str] = Field(None, description="Modelo específico del dispositivo")
    brand: Optional[str] = Field(None, description="Marca del dispositivo")
    manufacturer: Optional[str] = Field(None, description="Fabricante del dispositivo")
    platform: str = Field(..., pattern="^(ios|android)$", description="Plataforma: 'ios' o 'android'")
    osVersion: Optional[str] = Field(None, description="Versión del sistema operativo")
    deviceType: Optional[str] = Field(None, description="Tipo de dispositivo: 'PHONE', 'TABLET', 'DESKTOP', etc.")
    appVersion: Optional[str] = Field(None, description="Versión de la aplicación")
    buildVersion: Optional[str] = Field(None, description="Número de build de la aplicación")
    pushToken: Optional[str] = Field(None, description="Token de push notifications")

class UpdateDevice(BaseModel):
    """Schema para actualizar un dispositivo."""
    model_config = {"populate_by_name": True}
    
    deviceName: Optional[str] = Field(None, min_length=1)
    modelName: Optional[str] = None
    brand: Optional[str] = None
    manufacturer: Optional[str] = None
    platform: Optional[str] = Field(None, pattern="^(ios|android)$")
    osVersion: Optional[str] = None
    deviceType: Optional[str] = None
    appVersion: Optional[str] = None
    buildVersion: Optional[str] = None
    pushToken: Optional[str] = None

class DeviceResponse(BaseModel):
    """Schema de respuesta para un dispositivo."""
    model_config = {"from_attributes": True, "populate_by_name": True}
    
    id: int
    deviceName: str
    modelName: Optional[str] = None
    brand: Optional[str] = None
    manufacturer: Optional[str] = None
    platform: str
    osVersion: Optional[str] = None
    deviceType: Optional[str] = None
    appVersion: Optional[str] = None
    buildVersion: Optional[str] = None
    pushToken: Optional[str] = None  # Se mapeará desde expoPushToken
    lastActive: datetime
    createdAt: datetime
    updatedAt: Optional[datetime] = None
    
    @classmethod
    def from_device(cls, device):
        """Helper para crear DeviceResponse desde un modelo Device."""
        return cls(
            id=device.id,
            deviceName=device.deviceName,
            modelName=device.modelName,
            brand=device.brand,
            manufacturer=device.manufacturer,
            platform=device.platform,
            osVersion=device.osVersion,
            deviceType=device.deviceType,
            appVersion=device.appVersion,
            buildVersion=device.buildVersion,
            pushToken=device.expoPushToken,
            lastActive=device.lastActive,
            createdAt=device.createdAt,
            updatedAt=device.updatedAt
        )

