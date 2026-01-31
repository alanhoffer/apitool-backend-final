from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class NewsCreate(BaseModel):
    title: str
    content: str
    image: Optional[str] = None

class NewsUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    image: Optional[str] = None

class NewsResponse(BaseModel):
    id: int
    title: str
    content: str
    date: datetime
    image: Optional[str] = None
    
    class Config:
        from_attributes = True

