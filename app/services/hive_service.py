from typing import List, Optional

from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from app.models.apiary import Apiary
from app.models.hive import Hive
from app.schemas.hive import HiveCreate, HiveUpdate


class HiveService:
    def __init__(self, db: Session):
        self.db = db

    def _get_owned_apiary(self, apiary_id: int, user_id: int) -> Optional[Apiary]:
        return self.db.query(Apiary).filter(
            and_(Apiary.id == apiary_id, Apiary.userId == user_id)
        ).first()

    def _sync_apiary_hive_count(self, apiary_id: int) -> None:
        hive_count = self.db.query(func.count(Hive.id)).filter(Hive.apiaryId == apiary_id).scalar() or 0
        apiary = self.db.query(Apiary).filter(Apiary.id == apiary_id).first()
        if apiary:
            apiary.hives = int(hive_count)
            self.db.flush()

    def create_hive(self, user_id: int, hive_data: HiveCreate) -> Optional[Hive]:
        apiary = self._get_owned_apiary(hive_data.apiaryId, user_id)
        if not apiary:
            return None

        hive = Hive(userId=user_id, **hive_data.model_dump())
        self.db.add(hive)
        self.db.flush()
        self._sync_apiary_hive_count(hive.apiaryId)
        self.db.commit()
        self.db.refresh(hive)
        return hive

    def get_hives(self, user_id: int, apiary_id: Optional[int] = None) -> List[Hive]:
        query = self.db.query(Hive).filter(Hive.userId == user_id)
        if apiary_id is not None:
            query = query.filter(Hive.apiaryId == apiary_id)
        return query.order_by(Hive.updatedAt.desc(), Hive.id.desc()).all()

    def get_hive_by_id(self, hive_id: int, user_id: int) -> Optional[Hive]:
        return self.db.query(Hive).filter(
            and_(Hive.id == hive_id, Hive.userId == user_id)
        ).first()

    def update_hive(self, hive_id: int, user_id: int, updates: HiveUpdate) -> Optional[Hive]:
        hive = self.get_hive_by_id(hive_id, user_id)
        if not hive:
            return None

        update_data = updates.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(hive, key, value)

        self.db.commit()
        self.db.refresh(hive)
        return hive

    def delete_hive(self, hive_id: int, user_id: int) -> bool:
        hive = self.get_hive_by_id(hive_id, user_id)
        if not hive:
            return False

        apiary_id = hive.apiaryId
        self.db.delete(hive)
        self.db.flush()
        self._sync_apiary_hive_count(apiary_id)
        self.db.commit()
        return True
