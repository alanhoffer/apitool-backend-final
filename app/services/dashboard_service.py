from __future__ import annotations

from collections import Counter, OrderedDict
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import Dict, Iterable, List, Literal, Tuple

from sqlalchemy.orm import Session

from app.models.apiary import Apiary
from app.models.history import History
from app.models.hive import Hive
from app.models.notification import Notification
from app.models.task import Task
from app.models.user import User
from app.services.harvest_season_service import HarvestSeasonService

DashboardPeriod = Literal["day", "week", "month", "year"]

_MONTH_ABBR = [
    "Ene",
    "Feb",
    "Mar",
    "Abr",
    "May",
    "Jun",
    "Jul",
    "Ago",
    "Sep",
    "Oct",
    "Nov",
    "Dic",
]

_WEEKDAY_ABBR = ["Lun", "Mar", "Mie", "Jue", "Vie", "Sab", "Dom"]
_HARVEST_FIELDS = {"box", "boxMedium", "boxSmall"}
_QUEEN_OK = {"present", "marked"}
_WEAK_STRENGTH = {"weak", "debil", "low"}


class DashboardService:
    def __init__(self, db: Session):
        self.db = db

    def get_dashboard_summary(self, user: User) -> dict:
        active_season = HarvestSeasonService(self.db).get_or_create_active_season(user.id)
        metrics = self._build_operational_metrics(user.id, active_season.startedAt)
        return {
            "id": user.id,
            "name": user.name,
            "surname": user.surname,
            "role": user.role,
            **metrics,
        }

    def get_statistics_overview(self, user_id: int, period: DashboardPeriod) -> dict:
        active_season = HarvestSeasonService(self.db).get_or_create_active_season(user_id)
        metrics = self._build_operational_metrics(user_id, active_season.startedAt)
        harvest_series = self._build_harvest_series(user_id, period, active_season.startedAt)

        return {
            "period": period,
            "generatedAt": self._utcnow_naive(),
            **metrics,
            "periodHarvestBoxes": int(sum(point["total"] for point in harvest_series)),
            "apiaryStatusCounts": self._build_apiary_status_counts(user_id),
            "hiveStrengthCounts": self._build_hive_strength_counts(user_id),
            "harvestSeries": harvest_series,
        }

    def _build_operational_metrics(self, user_id: int, active_season_started_at: datetime | None = None) -> dict:
        apiaries = self.db.query(Apiary).filter(Apiary.userId == user_id).all()
        hives = self.db.query(Hive).filter(Hive.userId == user_id).all()
        tasks = self.db.query(Task).filter(Task.user_id == user_id).all()

        harvested_apiary_count = sum(
            1
            for apiary in apiaries
            if any(
                self._decimal_to_int(value) > 0
                for value in (apiary.box, apiary.boxMedium, apiary.boxSmall)
            )
        )
        unread_notification_count = (
            self.db.query(Notification)
            .filter(Notification.userId == user_id, Notification.isRead == False)
            .count()
        )

        today = self._utcnow_naive().date()
        pending_task_count = 0
        overdue_task_count = 0
        due_today_task_count = 0
        completed_task_count = 0

        for task in tasks:
            if task.completed:
                completed_task_count += 1
                continue

            pending_task_count += 1
            due_date = self._coerce_datetime(task.due_date)
            if not due_date:
                continue

            if due_date.date() < today:
                overdue_task_count += 1
            elif due_date.date() == today:
                due_today_task_count += 1

        total_task_count = len(tasks)
        completion_rate = round((completed_task_count / total_task_count) * 100, 1) if total_task_count else 0.0

        total_honey = sum(self._decimal_to_float(apiary.honey) for apiary in apiaries)
        total_sugar = sum(self._decimal_to_float(apiary.sugar) for apiary in apiaries)
        total_levudex = sum(self._decimal_to_float(apiary.levudex) for apiary in apiaries)
        total_harvest_boxes = sum(
            self._decimal_to_int(apiary.box)
            + self._decimal_to_int(apiary.boxMedium)
            + self._decimal_to_int(apiary.boxSmall)
            for apiary in apiaries
        )

        weak_hive_count = 0
        queen_issue_hive_count = 0
        swarming_hive_count = 0
        stale_inspection_hive_count = 0
        attention_hive_count = 0

        for hive in hives:
            is_weak = self._normalize_text(hive.hiveStrength) in _WEAK_STRENGTH
            has_queen_issue = self._normalize_text(hive.queenStatus) not in _QUEEN_OK
            is_swarming = bool(hive.swarming)
            is_stale = self._is_stale_inspection(hive.lastInspection, today)

            if is_weak:
                weak_hive_count += 1
            if has_queen_issue:
                queen_issue_hive_count += 1
            if is_swarming:
                swarming_hive_count += 1
            if is_stale:
                stale_inspection_hive_count += 1
            if is_weak or has_queen_issue or is_swarming or is_stale:
                attention_hive_count += 1

        recent_harvest_today = self._build_harvest_series(user_id, "week", active_season_started_at)
        recent_harvest_boxes_today = recent_harvest_today[-1]["total"] if recent_harvest_today else 0

        return {
            "apiaryCount": len(apiaries),
            "hiveCount": sum(int(apiary.hives or 0) for apiary in apiaries),
            "harvestedApiaryCount": harvested_apiary_count,
            "pendingTaskCount": pending_task_count,
            "overdueTaskCount": overdue_task_count,
            "dueTodayTaskCount": due_today_task_count,
            "completedTaskCount": completed_task_count,
            "completionRate": completion_rate,
            "unreadNotificationCount": unread_notification_count,
            "totalHoneyKg": round(total_honey, 2),
            "totalSugarKg": round(total_sugar, 2),
            "totalLevudexKg": round(total_levudex, 2),
            "totalHarvestBoxes": total_harvest_boxes,
            "recentHarvestBoxesToday": recent_harvest_boxes_today,
            "weakHiveCount": weak_hive_count,
            "queenIssueHiveCount": queen_issue_hive_count,
            "swarmingHiveCount": swarming_hive_count,
            "staleInspectionHiveCount": stale_inspection_hive_count,
            "attentionHiveCount": attention_hive_count,
        }

    def _build_apiary_status_counts(self, user_id: int) -> Dict[str, int]:
        apiaries = self.db.query(Apiary).filter(Apiary.userId == user_id).all()
        counter = Counter(self._normalize_status_label(apiary.status) for apiary in apiaries)
        return dict(counter)

    def _build_hive_strength_counts(self, user_id: int) -> Dict[str, int]:
        hives = self.db.query(Hive).filter(Hive.userId == user_id).all()
        counter = Counter(self._normalize_strength_label(hive.hiveStrength) for hive in hives)
        return dict(counter)

    def _build_harvest_series(
        self,
        user_id: int,
        period: DashboardPeriod,
        active_season_started_at: datetime | None = None,
    ) -> List[dict]:
        buckets = self._build_period_buckets(period)
        if not buckets:
            return []

        bucket_map = OrderedDict()
        for bucket_key, start_date, end_date, label in buckets:
            bucket_map[bucket_key] = {
                "label": label,
                "startDate": start_date,
                "endDate": end_date,
                "box": 0,
                "boxMedium": 0,
                "boxSmall": 0,
                "total": 0,
            }

        start_cutoff = datetime.combine(buckets[0][1], datetime.min.time())
        if active_season_started_at and active_season_started_at > start_cutoff:
            start_cutoff = active_season_started_at
        history_rows = (
            self.db.query(History)
            .filter(
                History.userId == user_id,
                History.field.in_(tuple(_HARVEST_FIELDS)),
                History.changeDate >= start_cutoff,
            )
            .order_by(History.changeDate.asc(), History.id.asc())
            .all()
        )

        for row in history_rows:
            bucket_key = self._bucket_key(period, row.changeDate)
            point = bucket_map.get(bucket_key)
            if not point:
                continue

            delta = max(
                0,
                self._parse_number(row.newValue) - self._parse_number(row.previousValue),
            )
            if delta == 0:
                continue

            point[row.field] += delta
            point["total"] += delta

        return list(bucket_map.values())

    def _build_period_buckets(self, period: DashboardPeriod) -> List[Tuple[str, date, date, str]]:
        today = self._utcnow_naive().date()

        if period == "day":
            return [
                (
                    f"{today.isoformat()}-{hour:02d}",
                    today,
                    today,
                    f"{hour:02d}:00",
                )
                for hour in range(24)
            ]

        if period == "week":
            buckets = []
            for offset in range(6, -1, -1):
                bucket_date = today - timedelta(days=offset)
                buckets.append((
                    bucket_date.isoformat(),
                    bucket_date,
                    bucket_date,
                    f"{_WEEKDAY_ABBR[bucket_date.weekday()]} {bucket_date.day}",
                ))
            return buckets

        if period == "month":
            buckets = []
            for offset in range(29, -1, -1):
                bucket_date = today - timedelta(days=offset)
                buckets.append((
                    bucket_date.isoformat(),
                    bucket_date,
                    bucket_date,
                    f"{bucket_date.day} {_MONTH_ABBR[bucket_date.month - 1]}",
                ))
            return buckets

        buckets = []
        current = date(today.year, today.month, 1)
        for offset in range(11, -1, -1):
            year = current.year
            month = current.month - offset
            while month <= 0:
                month += 12
                year -= 1
            bucket_start = date(year, month, 1)
            if month == 12:
                next_month = date(year + 1, 1, 1)
            else:
                next_month = date(year, month + 1, 1)
            bucket_end = next_month - timedelta(days=1)
            bucket_key = f"{year}-{month:02d}"
            buckets.append((bucket_key, bucket_start, bucket_end, _MONTH_ABBR[month - 1]))
        return buckets

    def _bucket_key(self, period: DashboardPeriod, value: date | datetime) -> str:
        bucket_date = value.date() if isinstance(value, datetime) else value
        if period == "day":
            hour = value.hour if isinstance(value, datetime) else 0
            return f"{bucket_date.isoformat()}-{hour:02d}"
        if period in {"week", "month"}:
            return bucket_date.isoformat()
        return f"{bucket_date.year}-{bucket_date.month:02d}"

    def _is_stale_inspection(self, value: str | None, today: date) -> bool:
        inspection_date = self._parse_date(value)
        if not inspection_date:
            return True
        return (today - inspection_date).days > 30

    def _normalize_status_label(self, value: str | None) -> str:
        normalized = self._normalize_text(value)
        if not normalized:
            return "Desconocido"
        if normalized == "normal":
            return "Normal"
        return normalized.capitalize()

    def _normalize_strength_label(self, value: str | None) -> str:
        normalized = self._normalize_text(value)
        if not normalized:
            return "Sin dato"
        if normalized == "weak":
            return "Debil"
        if normalized == "medium":
            return "Media"
        if normalized == "strong":
            return "Fuerte"
        return normalized.capitalize()

    def _normalize_text(self, value: str | None) -> str:
        return (value or "").strip().lower()

    def _parse_date(self, value: str | None) -> date | None:
        if not value:
            return None
        candidate = value.strip()
        if not candidate:
            return None

        for parser in (
            lambda raw: datetime.fromisoformat(raw.replace("Z", "+00:00")).date(),
            lambda raw: datetime.strptime(raw[:10], "%Y-%m-%d").date(),
        ):
            try:
                return parser(candidate)
            except Exception:
                continue
        return None

    def _coerce_datetime(self, value: datetime | None) -> datetime | None:
        if not value:
            return None
        return value

    def _parse_number(self, value: str | None) -> int:
        if value in (None, ""):
            return 0
        try:
            return int(Decimal(str(value)))
        except Exception:
            try:
                return int(float(str(value)))
            except Exception:
                return 0

    def _decimal_to_float(self, value: Decimal | float | int | None) -> float:
        if value is None:
            return 0.0
        return float(value)

    def _decimal_to_int(self, value: Decimal | float | int | None) -> int:
        if value is None:
            return 0
        return int(value)

    def _utcnow_naive(self) -> datetime:
        return datetime.now(timezone.utc).replace(tzinfo=None)
