from sqlalchemy.orm import Session
from app.models.news import News
from app.schemas.news import NewsCreate, NewsUpdate
from typing import List, Optional

class NewsService:
    def __init__(self, db: Session):
        self.db = db
    
    def find_all(self) -> List[News]:
        return self.db.query(News).order_by(News.date.desc()).all()
    
    def find_by_id(self, news_id: int) -> Optional[News]:
        return self.db.query(News).filter(News.id == news_id).first()
    
    def create(self, news_data: NewsCreate, user_id: int) -> News:
        new_news = News(
            title=news_data.title,
            content=news_data.content,
            image=news_data.image,
            user_id=user_id
        )
        self.db.add(new_news)
        self.db.commit()
        self.db.refresh(new_news)
        return new_news
    
    def update(self, news_id: int, news_data: NewsUpdate) -> Optional[News]:
        news = self.db.query(News).filter(News.id == news_id).first()
        if not news:
            return None
        
        update_data = news_data.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(news, key, value)
        
        self.db.commit()
        self.db.refresh(news)
        return news
    
    def delete(self, news_id: int) -> bool:
        news = self.db.query(News).filter(News.id == news_id).first()
        if not news:
            return False
        
        self.db.delete(news)
        self.db.commit()
        return True

