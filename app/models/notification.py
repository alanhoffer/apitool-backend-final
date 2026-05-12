from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, JSON, Index
from sqlalchemy.sql import func
from app.database import Base

class Notification(Base):
    __tablename__ = "notifications"
    __table_args__ = (
        Index("idx_notifications_user_read_created", "userId", "isRead", "createdAt"),
        Index("idx_notifications_user_type_title_read", "userId", "type", "title", "isRead"),
    )

    id = Column(Integer, primary_key=True, index=True)
    userId = Column(Integer, ForeignKey("user.id"), nullable=False)
    title = Column(String, nullable=False)
    message = Column(String, nullable=False)
    type = Column(String, default="INFO") # ALERT, INFO, WARNING
    isRead = Column(Boolean, default=False)
    data = Column(JSON, nullable=True)  # Navigation context: {apiaryId, hiveId, taskId}
    createdAt = Column(DateTime, server_default=func.current_timestamp())


