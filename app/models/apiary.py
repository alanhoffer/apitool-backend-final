from sqlalchemy import Column, Integer, String, Numeric, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class Apiary(Base):
    __tablename__ = "apiary"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    userId = Column(Integer, ForeignKey("user.id"), nullable=False)
    image = Column(String, default="apiary-default.png")
    hives = Column(Integer, default=0)
    status = Column(String, default="normal")
    honey = Column(Numeric(10, 2), default=0)
    levudex = Column(Numeric(10, 2), default=0)
    sugar = Column(Numeric(10, 2), default=0)
    box = Column(Integer, default=0)
    boxMedium = Column(Integer, default=0)
    boxSmall = Column(Integer, default=0)
    tOxalic = Column(Integer, default=0)
    tAmitraz = Column(Integer, default=0)
    tFlumetrine = Column(Integer, default=0)
    tFence = Column(Integer, default=0)
    tComment = Column(String, default="")
    transhumance = Column(Integer, nullable=True, default=0)
    latitude = Column(Numeric(10, 8), nullable=True)
    longitude = Column(Numeric(11, 8), nullable=True)
    createdAt = Column(DateTime, server_default=func.current_timestamp())
    updatedAt = Column(DateTime, server_default=func.current_timestamp(), onupdate=func.current_timestamp())
    
    user = relationship("User", back_populates="apiarys")
    settings = relationship("Settings", back_populates="apiary", uselist=False, cascade="all, delete-orphan")
    tasks = relationship("Task", back_populates="apiary")

