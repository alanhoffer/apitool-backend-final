from sqlalchemy.orm import Session
from sqlalchemy import func, and_, Integer as SQLInteger, case
from app.models.drum import Drum
from app.schemas.drum import DrumCreate, DrumUpdate
from typing import List, Optional
from decimal import Decimal

class DrumService:
    def __init__(self, db: Session):
        self.db = db
    
    def create_drum(self, user_id: int, drum_data: DrumCreate) -> Drum:
        drum = Drum(
            userId=user_id,
            code=drum_data.code,
            tare=drum_data.tare,
            weight=drum_data.weight
        )
        self.db.add(drum)
        self.db.commit()
        self.db.refresh(drum)
        return drum
    
    def get_drums(
        self, 
        user_id: int, 
        sold: Optional[bool] = None,
        page: int = 1,
        limit: int = 50
    ) -> tuple[List[Drum], int]:
        query = self.db.query(Drum).filter(Drum.userId == user_id)
        
        if sold is not None:
            query = query.filter(Drum.sold == sold)
        
        total = query.count()
        offset = (page - 1) * limit
        
        drums = query.order_by(Drum.createdAt.desc()).offset(offset).limit(limit).all()
        return drums, total
    
    def get_drum_by_id(self, drum_id: int, user_id: int) -> Optional[Drum]:
        return self.db.query(Drum).filter(
            and_(Drum.id == drum_id, Drum.userId == user_id)
        ).first()
    
    def update_drum(self, drum_id: int, user_id: int, updates: DrumUpdate) -> Optional[Drum]:
        drum = self.get_drum_by_id(drum_id, user_id)
        if not drum:
            return None
        
        update_data = updates.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(drum, key, value)
        
        self.db.commit()
        self.db.refresh(drum)
        return drum
    
    def mark_as_sold(self, drum_id: int, user_id: int, sold: bool) -> Optional[Drum]:
        return self.update_drum(drum_id, user_id, DrumUpdate(sold=sold))
    
    def delete_drum(self, drum_id: int, user_id: int) -> bool:
        drum = self.get_drum_by_id(drum_id, user_id)
        if not drum:
            return False
        
        self.db.delete(drum)
        self.db.commit()
        return True
    
    def delete_all_drums(self, user_id: int, sold: Optional[bool] = None) -> int:
        query = self.db.query(Drum).filter(Drum.userId == user_id)
        
        if sold is not None:
            query = query.filter(Drum.sold == sold)
        
        count = query.count()
        query.delete(synchronize_session=False)
        self.db.commit()
        return count
    
    def get_stats(self, user_id: int) -> dict:
        # Contar totales
        total = self.db.query(func.count(Drum.id)).filter(Drum.userId == user_id).scalar()
        
        # Contar vendidos y no vendidos
        sold_count = self.db.query(func.count(Drum.id)).filter(
            and_(Drum.userId == user_id, Drum.sold == True)
        ).scalar()
        
        not_sold_count = self.db.query(func.count(Drum.id)).filter(
            and_(Drum.userId == user_id, Drum.sold == False)
        ).scalar()
        
        # Sumar taras y pesos
        result = self.db.query(
            func.sum(Drum.tare).label('total_tare'),
            func.sum(Drum.weight).label('total_weight')
        ).filter(Drum.userId == user_id).first()
        
        total_tare = float(result.total_tare or 0)
        total_weight = float(result.total_weight or 0)
        net_weight = total_weight - total_tare
        
        return {
            "total": total or 0,
            "sold": sold_count or 0,
            "not_sold": not_sold_count or 0,
            "total_tare": Decimal(str(total_tare)),
            "total_weight": Decimal(str(total_weight)),
            "net_weight": Decimal(str(net_weight))
        }



























