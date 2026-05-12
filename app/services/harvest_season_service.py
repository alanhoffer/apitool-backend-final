from __future__ import annotations

import re
from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.models.apiary import Apiary
from app.models.harvest_season import HarvestSeason, HarvestSeasonApiaryTotal


HARVEST_SEASON_ACTIVE = "active"
HARVEST_SEASON_CLOSED = "closed"


class HarvestSeasonService:
    def __init__(self, db: Session):
        self.db = db

    def get_active_season(self, user_id: int) -> Optional[HarvestSeason]:
        return self.get_or_create_active_season(user_id)

    def get_or_create_active_season(self, user_id: int) -> HarvestSeason:
        current_year = self._now().year
        current_start, _ = self._year_bounds(current_year)
        current_name = self._default_name(current_start)

        current_year_season = self._get_year_season(user_id, current_year)
        active_seasons = self._get_active_seasons(user_id)
        rollover_needed = current_year_season is None and any(
            self._season_year(season) < current_year for season in active_seasons
        )

        for season in active_seasons:
            if current_year_season and season.id == current_year_season.id:
                continue
            self._close_season(season)

        if rollover_needed:
            self._reset_current_harvest(user_id)

        if current_year_season:
            current_year_season.name = current_name
            current_year_season.status = HARVEST_SEASON_ACTIVE
            current_year_season.startedAt = current_start
            current_year_season.endedAt = None
            self.db.commit()
            self.db.refresh(current_year_season)
            return current_year_season

        season = self._new_active_season(
            user_id=user_id,
            name=current_name,
            started_at=current_start,
        )
        self.db.commit()
        self.db.refresh(season)
        return season

    def list_seasons(self, user_id: int) -> List[dict]:
        self.get_or_create_active_season(user_id)
        seasons = (
            self.db.query(HarvestSeason)
            .filter(HarvestSeason.userId == user_id)
            .order_by(HarvestSeason.startedAt.desc(), HarvestSeason.id.desc())
            .all()
        )
        return [self.build_summary(season) for season in seasons]

    def get_active_summary(self, user_id: int) -> dict:
        return self.build_summary(self.get_or_create_active_season(user_id))

    def get_season_apiary_totals(self, user_id: int, season_id: int) -> List[dict]:
        season = (
            self.db.query(HarvestSeason)
            .filter(HarvestSeason.id == season_id, HarvestSeason.userId == user_id)
            .first()
        )
        if not season:
            return []

        if season.status == HARVEST_SEASON_ACTIVE:
            apiaries = self.db.query(Apiary).filter(Apiary.userId == user_id).order_by(Apiary.name.asc()).all()
            return [
                self._apiary_total_response(
                    id=0,
                    season_id=season.id,
                    apiary_id=apiary.id,
                    apiary_name=apiary.name,
                    hives=apiary.hives,
                    box=apiary.box,
                    box_medium=apiary.boxMedium,
                    box_small=apiary.boxSmall,
                )
                for apiary in apiaries
            ]

        rows = (
            self.db.query(HarvestSeasonApiaryTotal)
            .filter(
                HarvestSeasonApiaryTotal.userId == user_id,
                HarvestSeasonApiaryTotal.seasonId == season_id,
            )
            .order_by(HarvestSeasonApiaryTotal.apiaryName.asc(), HarvestSeasonApiaryTotal.id.asc())
            .all()
        )
        return [
            self._apiary_total_response(
                id=row.id,
                season_id=row.seasonId,
                apiary_id=row.apiaryId,
                apiary_name=row.apiaryName,
                hives=row.hives,
                box=row.box,
                box_medium=row.boxMedium,
                box_small=row.boxSmall,
            )
            for row in rows
        ]

    def build_summary(self, season: HarvestSeason) -> dict:
        if season.status == HARVEST_SEASON_ACTIVE:
            totals = self._current_totals(season.userId)
        else:
            totals = self._archived_totals(season.id, season.userId)

        return {
            "id": season.id,
            "name": season.name,
            "status": season.status,
            "startedAt": season.startedAt,
            "endedAt": season.endedAt,
            "createdAt": season.createdAt,
            "updatedAt": season.updatedAt,
            "isActive": season.status == HARVEST_SEASON_ACTIVE,
            **totals,
        }

    def _new_active_season(self, user_id: int, name: str, started_at: datetime) -> HarvestSeason:
        season = HarvestSeason(
            userId=user_id,
            name=name,
            status=HARVEST_SEASON_ACTIVE,
            startedAt=started_at,
        )
        self.db.add(season)
        self.db.flush()
        return season

    def _get_active_seasons(self, user_id: int) -> List[HarvestSeason]:
        return (
            self.db.query(HarvestSeason)
            .filter(
                HarvestSeason.userId == user_id,
                HarvestSeason.status == HARVEST_SEASON_ACTIVE,
            )
            .order_by(HarvestSeason.startedAt.desc(), HarvestSeason.id.desc())
            .all()
        )

    def _get_year_season(self, user_id: int, year: int) -> Optional[HarvestSeason]:
        start, end = self._year_bounds(year)
        season = (
            self.db.query(HarvestSeason)
            .filter(
                HarvestSeason.userId == user_id,
                HarvestSeason.name == self._default_name(start),
            )
            .order_by(HarvestSeason.id.desc())
            .first()
        )
        if season:
            return season

        return (
            self.db.query(HarvestSeason)
            .filter(
                HarvestSeason.userId == user_id,
                HarvestSeason.startedAt >= start,
                HarvestSeason.startedAt < end,
            )
            .order_by(HarvestSeason.status.asc(), HarvestSeason.id.desc())
            .first()
        )

    def _close_season(self, season: HarvestSeason) -> None:
        self._snapshot_current_apiaries(season)
        season_year = self._season_year(season)
        _, season_end = self._year_bounds(season_year)
        season.status = HARVEST_SEASON_CLOSED
        season.endedAt = season_end

    def _snapshot_current_apiaries(self, season: HarvestSeason) -> None:
        apiaries = self.db.query(Apiary).filter(Apiary.userId == season.userId).all()
        existing_rows = (
            self.db.query(HarvestSeasonApiaryTotal)
            .filter(HarvestSeasonApiaryTotal.seasonId == season.id)
            .all()
        )
        rows_by_apiary_id = {row.apiaryId: row for row in existing_rows if row.apiaryId is not None}

        for apiary in apiaries:
            row = rows_by_apiary_id.get(apiary.id)
            if not row:
                row = HarvestSeasonApiaryTotal(
                    seasonId=season.id,
                    apiaryId=apiary.id,
                    userId=season.userId,
                )
                self.db.add(row)

            row.apiaryName = apiary.name
            row.hives = self._to_int(apiary.hives)
            row.box = self._to_int(apiary.box)
            row.boxMedium = self._to_int(apiary.boxMedium)
            row.boxSmall = self._to_int(apiary.boxSmall)

    def _reset_current_harvest(self, user_id: int) -> None:
        self.db.query(Apiary).filter(Apiary.userId == user_id).update(
            {
                "box": 0,
                "boxMedium": 0,
                "boxSmall": 0,
                "updatedAt": func.current_timestamp(),
            },
            synchronize_session=False,
        )

    def _current_totals(self, user_id: int) -> dict:
        harvested_filter = or_(Apiary.box > 0, Apiary.boxMedium > 0, Apiary.boxSmall > 0)
        result = (
            self.db.query(
                func.sum(Apiary.box).label("box"),
                func.sum(Apiary.boxMedium).label("boxMedium"),
                func.sum(Apiary.boxSmall).label("boxSmall"),
                func.count(Apiary.id).filter(harvested_filter).label("apiaryCount"),
                func.sum(Apiary.hives).filter(harvested_filter).label("hiveCount"),
            )
            .filter(Apiary.userId == user_id)
            .first()
        )
        return self._totals_response(
            box=getattr(result, "box", 0),
            box_medium=getattr(result, "boxMedium", 0),
            box_small=getattr(result, "boxSmall", 0),
            apiary_count=getattr(result, "apiaryCount", 0),
            hive_count=getattr(result, "hiveCount", 0),
        )

    def _archived_totals(self, season_id: int, user_id: int) -> dict:
        harvested_filter = or_(
            HarvestSeasonApiaryTotal.box > 0,
            HarvestSeasonApiaryTotal.boxMedium > 0,
            HarvestSeasonApiaryTotal.boxSmall > 0,
        )
        result = (
            self.db.query(
                func.sum(HarvestSeasonApiaryTotal.box).label("box"),
                func.sum(HarvestSeasonApiaryTotal.boxMedium).label("boxMedium"),
                func.sum(HarvestSeasonApiaryTotal.boxSmall).label("boxSmall"),
                func.count(HarvestSeasonApiaryTotal.id).filter(harvested_filter).label("apiaryCount"),
                func.sum(HarvestSeasonApiaryTotal.hives).filter(harvested_filter).label("hiveCount"),
            )
            .filter(
                HarvestSeasonApiaryTotal.userId == user_id,
                HarvestSeasonApiaryTotal.seasonId == season_id,
            )
            .first()
        )
        return self._totals_response(
            box=getattr(result, "box", 0),
            box_medium=getattr(result, "boxMedium", 0),
            box_small=getattr(result, "boxSmall", 0),
            apiary_count=getattr(result, "apiaryCount", 0),
            hive_count=getattr(result, "hiveCount", 0),
        )

    def _totals_response(self, box, box_medium, box_small, apiary_count, hive_count) -> dict:
        box_value = self._to_int(box)
        box_medium_value = self._to_int(box_medium)
        box_small_value = self._to_int(box_small)
        return {
            "box": box_value,
            "boxMedium": box_medium_value,
            "boxSmall": box_small_value,
            "total": box_value + box_medium_value + box_small_value,
            "apiaryCount": self._to_int(apiary_count),
            "hiveCount": self._to_int(hive_count),
        }

    def _apiary_total_response(
        self,
        id: int,
        season_id: int,
        apiary_id: Optional[int],
        apiary_name: Optional[str],
        hives,
        box,
        box_medium,
        box_small,
    ) -> dict:
        box_value = self._to_int(box)
        box_medium_value = self._to_int(box_medium)
        box_small_value = self._to_int(box_small)
        return {
            "id": id,
            "seasonId": season_id,
            "apiaryId": apiary_id,
            "apiaryName": apiary_name,
            "hives": self._to_int(hives),
            "box": box_value,
            "boxMedium": box_medium_value,
            "boxSmall": box_small_value,
            "total": box_value + box_medium_value + box_small_value,
        }

    def _default_name(self, value: Optional[datetime] = None) -> str:
        reference = value or self._now()
        return f"Cosecha {reference.year}"

    def _season_year(self, season: HarvestSeason) -> int:
        match = None
        if season.name:
            match = re.search(r"(\d{4})", season.name)
        if match:
            return int(match.group(1))
        return self._coerce_datetime(season.startedAt).year

    def _year_bounds(self, year: int) -> tuple[datetime, datetime]:
        return datetime(year, 1, 1), datetime(year + 1, 1, 1)

    def _coerce_datetime(self, value) -> datetime:
        if isinstance(value, datetime):
            return value.replace(tzinfo=None)
        if isinstance(value, str):
            try:
                return datetime.fromisoformat(value.replace("Z", "+00:00")).replace(tzinfo=None)
            except ValueError:
                return self._now()
        return self._now()

    def _to_int(self, value) -> int:
        if value is None:
            return 0
        if isinstance(value, Decimal):
            return int(value)
        try:
            return int(value)
        except (TypeError, ValueError):
            return 0

    def _now(self) -> datetime:
        return datetime.now(timezone.utc).replace(tzinfo=None)
