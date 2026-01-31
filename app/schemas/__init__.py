from .user import CreateUser, LoginUser, UserResponse
from .auth import AuthData
from .apiary import CreateApiary, UpdateApiary, ApiaryResponse, ApiaryDetail
from .settings import CreateSettings, UpdateSettings, SettingsResponse
from .history import HistoryResponse
from .news import NewsCreate, NewsUpdate, NewsResponse

# Resolver forward references para Pydantic v2
# Esto debe ejecutarse después de que todos los módulos estén importados
try:
    ApiaryResponse.model_rebuild()
except Exception:
    pass

__all__ = [
    "CreateUser", "LoginUser", "UserResponse",
    "AuthData",
    "CreateApiary", "UpdateApiary", "ApiaryResponse",
    "CreateSettings", "UpdateSettings", "SettingsResponse",
    "HistoryResponse",
    "NewsCreate", "NewsUpdate", "NewsResponse"
]

