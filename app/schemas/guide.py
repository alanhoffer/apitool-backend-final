from pydantic import BaseModel
from typing import Optional


class GuideBase(BaseModel):
    title: str
    content: str
    description: Optional[str] = None
    category: Optional[str] = None
    readTime: Optional[str] = None
    icon: Optional[str] = None
    color: Optional[str] = None
    featured: bool = False


class GuideCreate(GuideBase):
    pass


class GuideUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    readTime: Optional[str] = None
    icon: Optional[str] = None
    color: Optional[str] = None
    featured: Optional[bool] = None


class GuideResponse(GuideBase):
    id: int

    class Config:
        from_attributes = True
