from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.dependencies import get_current_user_payload, require_role
from app.services.news_service import NewsService
from app.schemas.news import NewsCreate, NewsUpdate, NewsResponse
from app.models.news import News
from typing import List

router = APIRouter(prefix="/news", tags=["news"])

@router.get("", response_model=List[NewsResponse])
async def find_all(
    payload: dict = Depends(get_current_user_payload),
    db: Session = Depends(get_db)
):
    news_service = NewsService(db)
    return news_service.find_all()

@router.get("/{id}", response_model=NewsResponse)
async def find_by_id(
    id: int, 
    payload: dict = Depends(get_current_user_payload),
    db: Session = Depends(get_db)
):
    news_service = NewsService(db)
    news = news_service.find_by_id(id)
    if not news:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="News not found"
        )
    return news

@router.post("", response_model=NewsResponse)
async def create(
    news_data: NewsCreate,
    payload: dict = Depends(require_role("admin")),
    db: Session = Depends(get_db)
):
    news_service = NewsService(db)
    user_id = int(payload.get("sub"))
    return news_service.create(news_data, user_id)

@router.put("/{id}", response_model=NewsResponse)
async def update(
    id: int,
    news_data: NewsUpdate,
    payload: dict = Depends(require_role("admin")),
    db: Session = Depends(get_db)
):
    news_service = NewsService(db)
    news = news_service.update(id, news_data)
    if not news:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="News not found"
        )
    return news

@router.delete("/{id}")
async def delete(
    id: int, 
    payload: dict = Depends(require_role("admin")),
    db: Session = Depends(get_db)
):
    news_service = NewsService(db)
    success = news_service.delete(id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="News not found"
        )
    return {"message": "News deleted successfully"}

