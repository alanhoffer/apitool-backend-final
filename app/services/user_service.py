from sqlalchemy.orm import Session
from app.models.user import User
from app.models.device import Device
from app.schemas.user import CreateUser
from typing import Optional
from datetime import datetime

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
        self.db.commit()
        self.db.refresh(new_user)
        return new_user
    
    def delete_user(self, user_id: int) -> bool:
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return False
        self.db.delete(user)
        self.db.commit()
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
            self.db.commit()
            return True
        
        # Crear nuevo dispositivo
        new_device = Device(
            userId=user_id,
            expoPushToken=token,
            deviceName=device_name,
            platform=platform
        )
        self.db.add(new_device)
        self.db.commit()
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
        self.db.commit()
        return True

