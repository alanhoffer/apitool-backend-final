from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class Device(Base):
    """Modelo para almacenar información completa de dispositivos del usuario."""
    __tablename__ = "devices"
    
    id = Column(Integer, primary_key=True, index=True)
    userId = Column(Integer, ForeignKey("user.id"), nullable=False, index=True)
    
    # Información básica del dispositivo
    deviceName = Column(String, nullable=False)  # "iPhone 13 Pro", "Samsung Galaxy S21", etc.
    modelName = Column(String, nullable=True)  # "iPhone14,2", "SM-G991B", etc.
    brand = Column(String, nullable=True)  # "Apple", "Samsung", etc.
    manufacturer = Column(String, nullable=True)  # Fabricante del dispositivo
    platform = Column(String, nullable=False)  # "ios", "android"
    osVersion = Column(String, nullable=True)  # "17.0", "13", etc.
    deviceType = Column(String, nullable=True)  # "PHONE", "TABLET", "DESKTOP", etc.
    
    # Información de la aplicación
    appVersion = Column(String, nullable=True)  # "1.0.0"
    buildVersion = Column(String, nullable=True)  # "2"
    
    # Token de push notifications (opcional)
    expoPushToken = Column(String, nullable=True)  # Token de Expo Push Notification
    
    # Timestamps
    lastActive = Column(DateTime, server_default=func.current_timestamp(), onupdate=func.current_timestamp())
    createdAt = Column(DateTime, server_default=func.current_timestamp())
    updatedAt = Column(DateTime, server_default=func.current_timestamp(), onupdate=func.current_timestamp())
    
    # Índice único para identificar dispositivos por usuario, nombre y plataforma
    __table_args__ = (
        Index('idx_user_device_platform', 'userId', 'deviceName', 'platform'),
    )
    
    user = relationship("User", back_populates="devices")




























