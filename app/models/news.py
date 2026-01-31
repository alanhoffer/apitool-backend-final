from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class News(Base):
    __tablename__ = "news"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(100), nullable=False)
    content = Column(String(1000), nullable=False)
    date = Column(DateTime, server_default=func.current_timestamp(), nullable=False)
    image = Column(String, nullable=True)
    user_id = Column(Integer, ForeignKey("user.id"), nullable=True)
    
    user = relationship("User", back_populates="news")

