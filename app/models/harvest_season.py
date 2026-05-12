from sqlalchemy import Column, DateTime, ForeignKey, Index, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class HarvestSeason(Base):
    __tablename__ = "harvest_season"
    __table_args__ = (
        Index("idx_harvest_season_user_status_started", "userId", "status", "startedAt"),
    )

    id = Column(Integer, primary_key=True, index=True)
    userId = Column(Integer, ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(120), nullable=False)
    status = Column(String(20), nullable=False, default="active")
    startedAt = Column(DateTime, nullable=False, server_default=func.current_timestamp())
    endedAt = Column(DateTime, nullable=True)
    createdAt = Column(DateTime, server_default=func.current_timestamp())
    updatedAt = Column(DateTime, server_default=func.current_timestamp(), onupdate=func.current_timestamp())

    apiaryTotals = relationship(
        "HarvestSeasonApiaryTotal",
        back_populates="season",
        cascade="all, delete-orphan",
    )


class HarvestSeasonApiaryTotal(Base):
    __tablename__ = "harvest_season_apiary_total"
    __table_args__ = (
        Index("idx_harvest_season_total_season_apiary", "seasonId", "apiaryId", unique=True),
        Index("idx_harvest_season_total_user_season", "userId", "seasonId"),
    )

    id = Column(Integer, primary_key=True, index=True)
    seasonId = Column(Integer, ForeignKey("harvest_season.id", ondelete="CASCADE"), nullable=False)
    apiaryId = Column(Integer, ForeignKey("apiary.id", ondelete="SET NULL"), nullable=True)
    userId = Column(Integer, ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    apiaryName = Column(String(255), nullable=True)
    hives = Column(Integer, default=0)
    box = Column(Integer, default=0)
    boxMedium = Column(Integer, default=0)
    boxSmall = Column(Integer, default=0)
    createdAt = Column(DateTime, server_default=func.current_timestamp())
    updatedAt = Column(DateTime, server_default=func.current_timestamp(), onupdate=func.current_timestamp())

    season = relationship("HarvestSeason", back_populates="apiaryTotals")
