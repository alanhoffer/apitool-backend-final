from sqlalchemy import Column, Integer, String, DateTime, TypeDecorator
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import enum

class Role(str, enum.Enum):
    USER = "user"
    ADMIN = "admin"

class RoleType(TypeDecorator):
    """Custom type decorator to handle Role enum as string in database."""
    impl = String
    cache_ok = True
    
    def __init__(self):
        super().__init__(length=10)
    
    def process_bind_param(self, value, dialect):
        """Convert enum to string when writing to database."""
        if value is None:
            return None
        if isinstance(value, Role):
            return value.value
        if isinstance(value, str):
            return value
        return str(value)
    
    def process_result_value(self, value, dialect):
        """Convert string from database to enum when reading."""
        if value is None:
            return None
        if isinstance(value, Role):
            return value
        # Try to match by value (case-insensitive)
        value_lower = value.lower() if isinstance(value, str) else str(value).lower()
        for role in Role:
            if role.value.lower() == value_lower:
                return role
        # Fallback: return the string value
        return value

class User(Base):
    __tablename__ = "user"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    surname = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False, index=True)
    password = Column(String, nullable=False)
    createdAt = Column(DateTime, server_default=func.current_timestamp())
    authStrategy = Column(String, nullable=True)
    role = Column(RoleType(), default=Role.USER)
    expoPushToken = Column(String, nullable=True)
    
    apiarys = relationship("Apiary", back_populates="user", cascade="all, delete-orphan")
    news = relationship("News", back_populates="user")
    devices = relationship("Device", back_populates="user", cascade="all, delete-orphan")
    drums = relationship("Drum", back_populates="user", cascade="all, delete-orphan")
