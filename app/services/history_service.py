from sqlalchemy.orm import Session
from app.models.history import History
from typing import List, Any

class HistoryService:
    def __init__(self, db: Session):
        self.db = db
    
    def log_changes(self, old_apiary: Any, new_apiary: Any):
        changes = self._find_differences(old_apiary, new_apiary)
        
        for change in changes:
            history_entry = History(
                userId=old_apiary.userId,
                apiaryId=old_apiary.id,
                field=change['field'],
                previousValue=change['previousValue'],
                newValue=change['newValue']
            )
            self.db.add(history_entry)
        
        self.db.commit()
    
    def _find_differences(self, old_apiary: Any, new_apiary: Any) -> List[dict]:
        changes = []
        old_dict = {
            'name': getattr(old_apiary, 'name', None),
            'hives': getattr(old_apiary, 'hives', None),
            'status': getattr(old_apiary, 'status', None),
            'image': getattr(old_apiary, 'image', None),
            'honey': getattr(old_apiary, 'honey', None),
            'levudex': getattr(old_apiary, 'levudex', None),
            'sugar': getattr(old_apiary, 'sugar', None),
            'box': getattr(old_apiary, 'box', None),
            'boxMedium': getattr(old_apiary, 'boxMedium', None),
            'boxSmall': getattr(old_apiary, 'boxSmall', None),
            'tOxalic': getattr(old_apiary, 'tOxalic', None),
            'tAmitraz': getattr(old_apiary, 'tAmitraz', None),
            'tFlumetrine': getattr(old_apiary, 'tFlumetrine', None),
            'tFence': getattr(old_apiary, 'tFence', None),
            'tComment': getattr(old_apiary, 'tComment', None),
            'transhumance': getattr(old_apiary, 'transhumance', None)
        }
        
        new_dict = {
            'name': getattr(new_apiary, 'name', None),
            'hives': getattr(new_apiary, 'hives', None),
            'status': getattr(new_apiary, 'status', None),
            'image': getattr(new_apiary, 'image', None),
            'honey': getattr(new_apiary, 'honey', None),
            'levudex': getattr(new_apiary, 'levudex', None),
            'sugar': getattr(new_apiary, 'sugar', None),
            'box': getattr(new_apiary, 'box', None),
            'boxMedium': getattr(new_apiary, 'boxMedium', None),
            'boxSmall': getattr(new_apiary, 'boxSmall', None),
            'tOxalic': getattr(new_apiary, 'tOxalic', None),
            'tAmitraz': getattr(new_apiary, 'tAmitraz', None),
            'tFlumetrine': getattr(new_apiary, 'tFlumetrine', None),
            'tFence': getattr(new_apiary, 'tFence', None),
            'tComment': getattr(new_apiary, 'tComment', None),
            'transhumance': getattr(new_apiary, 'transhumance', None)
        }
        
        for key in old_dict:
            if old_dict[key] != new_dict[key]:
                changes.append({
                    'field': key,
                    'previousValue': str(old_dict[key]) if old_dict[key] is not None else '',
                    'newValue': str(new_dict[key]) if new_dict[key] is not None else ''
                })
        
        return changes

