from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class HistoryResponse(BaseModel):
    id: int
    userId: int
    apiaryId: int
    field: str
    previousValue: Optional[str]
    newValue: Optional[str]
    changeDate: datetime
    userName: Optional[str] = None

    class Config:
        from_attributes = True

