from sqlalchemy.orm import Session
from app.models.user import User
from app.models.device import Device
from app.schemas.user import CreateUser, UpdateProfileRequest, ChangePasswordRequest
from app.schemas.device import CreateDevice, UpdateDevice
from typing import Optional
from datetime import datetime
from fastapi import HTTPException, status

class UserService:
    def __init__(self, db: Session):
        self.db = db
    
    def get_user(self, user_id: int) -> Optional[User]:
        return self.db.query(User).filter(User.id == user_id).first()
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        return self.db.query(User).filter(User.email == email).first()
    
    def create_user(self, user_data: CreateUser) -> Optional[User]:
        existing_user = self.db.query(User).filter(User.email == user_data.email).first()
        if existing_user:
            return None
        
        new_user = User(
            name=user_data.name,
            surname=user_data.surname,
            email=user_data.email,
            password=user_data.password
        )
        self.db.add(new_user)
        try:
            self.db.commit()
            self.db.refresh(new_user)
        except Exception:
            self.db.rollback()
            raise
        return new_user
    
    def delete_user(self, user_id: int) -> bool:
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return False
        self.db.delete(user)
        try:
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise
        return True

    def update_push_token(self, user_id: int, token: str) -> bool:
        """
        Método legacy: Actualiza el token en el campo expoPushToken del usuario.
        Se mantiene para compatibilidad, pero se recomienda usar register_device_token.
        """
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return False
        user.expoPushToken = token
        self.db.commit()
        self.db.refresh(user)
        return True
    
    def register_device_token(self, user_id: int, token: str, device_name: str = None, platform: str = None) -> bool:
        """
        Registra o actualiza un token de dispositivo para un usuario.
        Si el token ya existe, actualiza la fecha de último uso.
        Si no existe, crea un nuevo registro de dispositivo.
        
        Args:
            user_id: ID del usuario
            token: Token de Expo Push Notification
            device_name: Nombre del dispositivo (opcional)
            platform: Plataforma del dispositivo: "ios" o "android" (opcional)
        
        Returns:
            True si se registró exitosamente, False si el usuario no existe
        """
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return False
        
        # Buscar si el token ya existe
        existing_device = self.db.query(Device).filter(
            Device.expoPushToken == token
        ).first()
        
        if existing_device:
            # Si el token existe pero pertenece a otro usuario, actualizar
            if existing_device.userId != user_id:
                existing_device.userId = user_id
                existing_device.deviceName = device_name or existing_device.deviceName
                existing_device.platform = platform or existing_device.platform
            else:
                # Solo actualizar fecha de último uso
                existing_device.lastActive = datetime.now()
                if device_name:
                    existing_device.deviceName = device_name
                if platform:
                    existing_device.platform = platform
            try:
                self.db.commit()
            except Exception:
                self.db.rollback()
                raise
            return True
        
        # Crear nuevo dispositivo
        new_device = Device(
            userId=user_id,
            expoPushToken=token,
            deviceName=device_name,
            platform=platform
        )
        self.db.add(new_device)
        try:
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise
        return True
    
    def get_user_devices(self, user_id: int) -> list[Device]:
        """Obtiene todos los dispositivos registrados de un usuario."""
        return self.db.query(Device).filter(Device.userId == user_id).all()
    
    def remove_device(self, user_id: int, device_id: int) -> bool:
        """Elimina un dispositivo de un usuario."""
        device = self.db.query(Device).filter(
            Device.id == device_id,
            Device.userId == user_id
        ).first()
        
        if not device:
            return False
        
        self.db.delete(device)
        try:
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise
        return True
    
    def update_profile(self, user_id: int, profile_data: UpdateProfileRequest) -> Optional[User]:
        """
        Actualiza el perfil del usuario (nombre y/o email).
        """
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return None
        
        # Verificar si el nuevo email ya está en uso
        if profile_data.email and profile_data.email != user.email:
            existing_user = self.db.query(User).filter(User.email == profile_data.email).first()
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Email already in use"
                )
            user.email = profile_data.email
        
        if profile_data.name:
            user.name = profile_data.name
        
        try:
            self.db.commit()
            self.db.refresh(user)
        except Exception:
            self.db.rollback()
            raise
        
        return user
    
    def change_password(self, user_id: int, password_data: ChangePasswordRequest, auth_service) -> bool:
        """
        Cambia la contraseña del usuario.
        Requiere la contraseña actual.
        """
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return False
        
        # Verificar contraseña actual
        if not auth_service.verify_password(password_data.currentPassword, user.password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect"
            )
        
        # Actualizar contraseña
        user.password = auth_service.hash_password(password_data.newPassword)
        
        try:
            self.db.commit()
            self.db.refresh(user)
            return True
        except Exception:
            self.db.rollback()
            raise
    
    def register_or_update_device(self, user_id: int, device_data: CreateDevice) -> Device:
        """
        Registra o actualiza un dispositivo basado en deviceName + platform.
        Si el dispositivo existe, actualiza toda la información.
        Si no existe, crea uno nuevo.
        
        Args:
            user_id: ID del usuario
            device_data: Datos del dispositivo
            
        Returns:
            Device: El dispositivo registrado o actualizado
        """
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Buscar dispositivo por deviceName + platform + userId
        existing_device = self.db.query(Device).filter(
            Device.userId == user_id,
            Device.deviceName == device_data.deviceName,
            Device.platform == device_data.platform
        ).first()
        
        if existing_device:
            # Actualizar dispositivo existente
            existing_device.modelName = device_data.modelName or existing_device.modelName
            existing_device.brand = device_data.brand or existing_device.brand
            existing_device.manufacturer = device_data.manufacturer or existing_device.manufacturer
            existing_device.osVersion = device_data.osVersion or existing_device.osVersion
            existing_device.deviceType = device_data.deviceType or existing_device.deviceType
            existing_device.appVersion = device_data.appVersion or existing_device.appVersion
            existing_device.buildVersion = device_data.buildVersion or existing_device.buildVersion
            if device_data.pushToken:
                existing_device.expoPushToken = device_data.pushToken
            existing_device.lastActive = datetime.now()
            
            try:
                self.db.commit()
                self.db.refresh(existing_device)
                return existing_device
            except Exception:
                self.db.rollback()
                raise
        
        # Crear nuevo dispositivo
        new_device = Device(
            userId=user_id,
            deviceName=device_data.deviceName,
            modelName=device_data.modelName,
            brand=device_data.brand,
            manufacturer=device_data.manufacturer,
            platform=device_data.platform,
            osVersion=device_data.osVersion,
            deviceType=device_data.deviceType,
            appVersion=device_data.appVersion,
            buildVersion=device_data.buildVersion,
            expoPushToken=device_data.pushToken
        )
        self.db.add(new_device)
        try:
            self.db.commit()
            self.db.refresh(new_device)
            return new_device
        except Exception:
            self.db.rollback()
            raise
    
    def update_device(self, user_id: int, device_id: int, device_data: UpdateDevice) -> Optional[Device]:
        """
        Actualiza un dispositivo específico del usuario.
        
        Args:
            user_id: ID del usuario
            device_id: ID del dispositivo
            device_data: Datos a actualizar
            
        Returns:
            Device actualizado o None si no existe
        """
        device = self.db.query(Device).filter(
            Device.id == device_id,
            Device.userId == user_id
        ).first()
        
        if not device:
            return None
        
        # Actualizar solo los campos proporcionados
        update_data = device_data.model_dump(exclude_unset=True, exclude_none=True)
        if 'pushToken' in update_data:
            update_data['expoPushToken'] = update_data.pop('pushToken')
        
        for key, value in update_data.items():
            if hasattr(device, key):
                setattr(device, key, value)
        
        device.lastActive = datetime.now()
        
        try:
            self.db.commit()
            self.db.refresh(device)
            return device
        except Exception:
            self.db.rollback()
            raise

