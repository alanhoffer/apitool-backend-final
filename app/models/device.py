from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class Device(Base):
    """Modelo para almacenar tokens de push notifications de múltiples dispositivos por usuario."""
    __tablename__ = "devices"
    
    id = Column(Integer, primary_key=True, index=True)
    userId = Column(Integer, ForeignKey("user.id"), nullable=False, index=True)
    expoPushToken = Column(String, nullable=False, unique=True)
    deviceName = Column(String, nullable=True)  # "iPhone 12", "Samsung Galaxy", etc.
    platform = Column(String, nullable=True)  # "ios", "android"
    lastActive = Column(DateTime, server_default=func.current_timestamp(), onupdate=func.current_timestamp())
    createdAt = Column(DateTime, server_default=func.current_timestamp())
    
    user = relationship("User", back_populates="devices")



























