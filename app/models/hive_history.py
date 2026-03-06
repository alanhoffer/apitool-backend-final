from sqlalchemy import Column, Integer, DateTime, ForeignKey, String, JSON
from sqlalchemy.sql import func

from app.database import Base


class HiveHistory(Base):
    __tablename__ = "hive_history"

    id = Column(Integer, primary_key=True, index=True)
    hiveId = Column(Integer, ForeignKey("hive.id"), nullable=False, index=True)
    apiaryId = Column(Integer, ForeignKey("apiary.id"), nullable=False, index=True)
    userId = Column(Integer, ForeignKey("user.id"), nullable=False, index=True)
    createdBy = Column(Integer, ForeignKey("user.id"), nullable=False)
    changes = Column(JSON, nullable=False, default=dict)
    comment = Column(String, nullable=True)
    date = Column(DateTime, server_default=func.current_timestamp())
