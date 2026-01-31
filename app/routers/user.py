from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.dependencies import get_current_user
from app.services.user_service import UserService
from app.schemas.user import UserResponse, PushTokenUpdate
from app.models.user import User
from app.models.device import Device
from typing import List

router = APIRouter(prefix="/users", tags=["users"])

@router.post("/push-token")
async def register_push_token(
    token_data: PushTokenUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Registra o actualiza un token de dispositivo para el usuario actual.
    Soporta múltiples dispositivos por usuario.
    """
    user_service = UserService(db)
    success = user_service.register_device_token(
        current_user.id,
        token_data.token,
        device_name=token_data.deviceName,
        platform=token_data.platform
    )
    if not success:
         raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return {"message": "Device token registered successfully"}

@router.get("", response_model=UserResponse)
async def get_user(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user_service = UserService(db)
    found_user = user_service.get_user(current_user.id)
    
    if not found_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if found_user.id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="This user is not yours"
        )
    
    return found_user

@router.get("/devices")
async def get_user_devices(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtiene todos los dispositivos registrados del usuario actual."""
    user_service = UserService(db)
    devices = user_service.get_user_devices(current_user.id)
    
    return {
        "devices": [
            {
                "id": device.id,
                "deviceName": device.deviceName,
                "platform": device.platform,
                "lastActive": device.lastActive,
                "createdAt": device.createdAt
            }
            for device in devices
        ]
    }

@router.delete("/devices/{device_id}")
async def remove_device(
    device_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Elimina un dispositivo del usuario actual."""
    user_service = UserService(db)
    success = user_service.remove_device(current_user.id, device_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found or does not belong to user"
        )
    
    return {"message": "Device removed successfully"}

