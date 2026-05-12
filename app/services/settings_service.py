from sqlalchemy.orm import Session
from app.models.settings import Settings
from app.schemas.settings import UpdateSettings
from typing import Optional

class SettingsService:
    def __init__(self, db: Session):
        self.db = db
    
    def get_settings(self, settings_id: int) -> Optional[Settings]:
        return self.db.query(Settings).filter(Settings.id == settings_id).first()
    
    def update_settings(self, settings_id: int, settings_data: UpdateSettings) -> Optional[Settings]:
        settings = self.db.query(Settings).filter(Settings.id == settings_id).first()
        if not settings:
            return None
        
        update_data = settings_data.dict(exclude_unset=True)
        for key, value in update_data.items():
            if key not in ['apiaryId', 'apiaryUserId']:
                setattr(settings, key, value)
        
        self.db.commit()
        self.db.refresh(settings)
        return settings
    
    def delete_settings(self, settings_id: int) -> bool:
        settings = self.db.query(Settings).filter(Settings.id == settings_id).first()
        if not settings:
            return False
        
        self.db.delete(settings)
        self.db.commit()
        return True
    
