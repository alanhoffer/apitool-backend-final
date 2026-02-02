from sqlalchemy import Column, Integer, String, Numeric, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class Drum(Base):
    __tablename__ = "drums"
    
    id = Column(Integer, primary_key=True, index=True)
    userId = Column(Integer, ForeignKey("user.id"), nullable=False, index=True)
    code = Column(String(100), nullable=False, index=True)
    tare = Column(Numeric(10, 2), nullable=False)
    weight = Column(Numeric(10, 2), nullable=False)
    sold = Column(Boolean, default=False, index=True)
    createdAt = Column(DateTime, server_default=func.current_timestamp(), index=True)
    updatedAt = Column(DateTime, server_default=func.current_timestamp(), onupdate=func.current_timestamp())
    
    user = relationship("User", back_populates="drums")
    
    __table_args__ = (
        Index('idx_drums_user_id', 'userId'),
        Index('idx_drums_code', 'code'),
        Index('idx_drums_sold', 'sold'),
        Index('idx_drums_created_at', 'createdAt'),
    )





























