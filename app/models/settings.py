from sqlalchemy import Column, Integer, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database import Base

class Settings(Base):
    __tablename__ = "apiary_setting"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    apiaryId = Column(Integer, ForeignKey("apiary.id"), nullable=False)
    apiaryUserId = Column(Integer, nullable=False)
    honey = Column(Boolean, default=True)
    levudex = Column(Boolean, default=True)
    sugar = Column(Boolean, default=True)
    box = Column(Boolean, default=True)
    boxMedium = Column(Boolean, default=True)
    boxSmall = Column(Boolean, default=True)
    tOxalic = Column(Boolean, default=True)
    tAmitraz = Column(Boolean, default=True)
    tFlumetrine = Column(Boolean, default=True)
    tFence = Column(Boolean, default=True)
    tComment = Column(Boolean, default=True)
    transhumance = Column(Boolean, default=True)
    harvesting = Column(Boolean, default=False)
    tasks = Column(Text, nullable=True)
    
    apiary = relationship("Apiary", back_populates="settings")

