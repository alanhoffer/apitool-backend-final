from datetime import datetime
from typing import Dict, Any, Optional

from pydantic import BaseModel


class HiveHistoryResponse(BaseModel):
    id: int
    hiveId: int
    apiaryId: int
    userId: int
    createdBy: int
    changes: Dict[str, Any]
    comment: Optional[str]
    date: datetime

    class Config:
        from_attributes = True
