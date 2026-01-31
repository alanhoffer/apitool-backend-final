from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from app.database import Base

class History(Base):
    __tablename__ = "apiary_history"
    
    id = Column(Integer, primary_key=True, index=True)
    userId = Column(Integer, nullable=False)
    apiaryId = Column(Integer, nullable=False)
    field = Column(String, nullable=False)
    previousValue = Column(String, nullable=True)
    newValue = Column(String, nullable=True)
    changeDate = Column(DateTime, server_default=func.current_timestamp())

