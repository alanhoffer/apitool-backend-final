from sqlalchemy import Column, Integer, String, Numeric, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Hive(Base):
    __tablename__ = "hive"

    id = Column(Integer, primary_key=True, index=True)
    apiaryId = Column(Integer, ForeignKey("apiary.id"), nullable=False, index=True)
    userId = Column(Integer, ForeignKey("user.id"), nullable=False, index=True)
    name = Column(String, nullable=False, index=True)
    image = Column(String, default="")
    status = Column(String, default="normal")
    honey = Column(Numeric(10, 2), default=0)
    levudex = Column(Numeric(10, 2), default=0)
    sugar = Column(Numeric(10, 2), default=0)
    tOxalic = Column(Integer, default=0)
    tAmitraz = Column(Integer, default=0)
    tFlumetrine = Column(Integer, default=0)
    disease = Column(String, default="")
    box = Column(Integer, default=0)
    boxMedium = Column(Integer, default=0)
    boxSmall = Column(Integer, default=0)
    production = Column(Numeric(10, 2), default=0)
    queenStatus = Column(String, default="unknown")
    population = Column(Integer, default=0)
    broodFrames = Column(Integer, default=0)
    honeyFrames = Column(Integer, default=0)
    pollenFrames = Column(Integer, default=0)
    hiveStrength = Column(String, default="medium")
    swarming = Column(Boolean, default=False)
    lastInspection = Column(String, default="")
    tComment = Column(String, default="")
    createdAt = Column(DateTime, server_default=func.current_timestamp())
    updatedAt = Column(DateTime, server_default=func.current_timestamp(), onupdate=func.current_timestamp())

    apiary = relationship("Apiary", back_populates="hives_rel")
    user = relationship("User", back_populates="hives")
