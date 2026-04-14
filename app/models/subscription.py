from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Subscription(Base):
    __tablename__ = "subscription"

    id = Column(Integer, primary_key=True, index=True)
    userId = Column(Integer, ForeignKey("user.id"), nullable=False, unique=True)
    tier = Column(String, nullable=False, default="aprendiz")  # aprendiz | apicultor | maestro
    status = Column(String, nullable=False, default="active")  # active | expired | cancelled
    revenuecatCustomerId = Column(String, nullable=True)
    expiresAt = Column(DateTime, nullable=True)
    createdAt = Column(DateTime, server_default=func.current_timestamp())
    updatedAt = Column(DateTime, server_default=func.current_timestamp(), onupdate=func.current_timestamp())

    user = relationship("User", back_populates="subscription")
