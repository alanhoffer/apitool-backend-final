from .auth import router as auth_router
from .user import router as user_router
from .apiary import router as apiary_router
from .news import router as news_router
from .weather import router as weather_router
from .recommendations import router as recommendations_router
from .notification import router as notification_router
from .drum import router as drum_router
from .hive import router as hive_router
from .task import router as task_router
from .subscription import router as subscription_router
from .account_deletion import router as account_deletion_router
from .legal import router as legal_router
from .cron import router as cron_router

__all__ = ["auth_router", "user_router", "apiary_router", "news_router", "weather_router", "recommendations_router", "notification_router", "drum_router", "hive_router", "task_router", "subscription_router", "account_deletion_router", "legal_router", "cron_router"]
