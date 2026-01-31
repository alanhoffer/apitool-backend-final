from .auth import router as auth_router
from .user import router as user_router
from .apiary import router as apiary_router
from .news import router as news_router
from .weather import router as weather_router
from .recommendations import router as recommendations_router
from .notification import router as notification_router
from .drum import router as drum_router

__all__ = ["auth_router", "user_router", "apiary_router", "news_router", "weather_router", "recommendations_router", "notification_router", "drum_router"]

