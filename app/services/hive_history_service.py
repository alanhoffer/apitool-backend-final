from types import SimpleNamespace
from typing import Any, Dict, List, Optional
from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.hive_history import HiveHistory


class HiveHistoryService:
    tracked_fields = [
        "name",
        "image",
        "status",
        "honey",
        "levudex",
        "sugar",
        "tOxalic",
        "tAmitraz",
        "tFlumetrine",
        "disease",
        "box",
        "boxMedium",
        "boxSmall",
        "production",
        "queenStatus",
        "population",
        "broodFrames",
        "honeyFrames",
        "pollenFrames",
        "hiveStrength",
        "swarming",
        "lastInspection",
        "tComment",
    ]

    def __init__(self, db: Session):
        self.db = db

    def log_changes(self, old_hive: Any, new_hive: Any, comment: Optional[str] = None) -> Optional[HiveHistory]:
        changes = self._find_differences(old_hive, new_hive)
        if not changes:
            return None

        entry = HiveHistory(
            hiveId=new_hive.id,
            apiaryId=new_hive.apiaryId,
            userId=new_hive.userId,
            createdBy=new_hive.userId,
            changes=changes,
            comment=comment or changes.get("tComment"),
        )
        self.db.add(entry)
        self.db.commit()
        self.db.refresh(entry)
        return entry

    def get_hive_history(self, hive_id: int, user_id: int) -> List[HiveHistory]:
        return self.db.query(HiveHistory).filter(
            HiveHistory.hiveId == hive_id,
            HiveHistory.userId == user_id,
        ).order_by(HiveHistory.date.desc(), HiveHistory.id.desc()).all()

    def build_empty_hive(self, hive: Any) -> Any:
        payload = {field: None for field in self.tracked_fields}
        payload.update({
            "id": hive.id,
            "apiaryId": hive.apiaryId,
            "userId": hive.userId,
        })
        return SimpleNamespace(**payload)

    def _find_differences(self, old_hive: Any, new_hive: Any) -> Dict[str, Any]:
        changes: Dict[str, Any] = {}
        for field in self.tracked_fields:
            old_value = getattr(old_hive, field, None)
            new_value = getattr(new_hive, field, None)
            if old_value != new_value:
                changes[field] = self._serialize_value(new_value)
        return changes

    def _serialize_value(self, value: Any) -> Any:
        if isinstance(value, Decimal):
            return float(value)
        return value
