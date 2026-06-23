from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime
from sqlalchemy.sql import func
from app.database import Base


class Guide(Base):
    __tablename__ = "guide"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(150), nullable=False)
    description = Column(String(500), nullable=True)
    content = Column(Text, nullable=False)  # markdown
    category = Column(String(60), nullable=True)
    readTime = Column(String(20), nullable=True)
    icon = Column(String(60), nullable=True)
    color = Column(String(20), nullable=True)
    featured = Column(Boolean, default=False)
    date = Column(DateTime, server_default=func.current_timestamp(), nullable=False)
