from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.routers import (
    auth_router, user_router, apiary_router, news_router, 
    weather_router, recommendations_router, notification_router, drum_router,
    task_router,
)
from app.routers.audio import router as audio_router
from app.routers.health import router as health_router
from app.routers.metrics import router as metrics_router
from app.middleware.metrics import MetricsMiddleware
from app.middleware.request_id import RequestIDMiddleware
from app.middleware.rate_limit import RateLimitMiddleware
from app.middleware.security_headers import SecurityHeadersMiddleware
from app.middleware.request_size import RequestSizeMiddleware
from app.database import engine, Base
from app.cron import scheduler
from app.config import settings
from app.utils.logging_config import setup_logging
import os
import logging
import time
from sqlalchemy.exc import OperationalError

# Configurar timezone UTC
os.environ.setdefault("TZ", "UTC")
try:
    time.tzset()  # Linux/Unix
except AttributeError:
    pass  # Windows no tiene tzset

# Configurar logging
log_level = os.getenv("LOG_LEVEL", "INFO")
use_json_logging = os.getenv("JSON_LOGGING", "false").lower() == "true"
setup_logging(log_level=log_level, use_json=use_json_logging)

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    if os.getenv("TESTING") != "1":
        # Intentar crear las tablas, pero no fallar si la BD no está disponible
        try:
            Base.metadata.create_all(bind=engine)
            logger.info("Database tables created/verified successfully")
        except OperationalError as e:
            logger.warning(f"Could not connect to database during startup: {e}")
            logger.warning("Server will start, but database operations will fail until connection is available")
        except Exception as e:
            logger.error(f"Unexpected error creating database tables: {e}")
        
        if not scheduler.running:
            scheduler.start()
    yield
    # Shutdown
    if os.getenv("TESTING") != "1":
        if scheduler.running:
            scheduler.shutdown()

app = FastAPI(
    title="API Tool",
    version="0.0.1",
    lifespan=lifespan
)

# Request ID middleware (debe ir primero para que todos los logs tengan request_id)
app.add_middleware(RequestIDMiddleware)

# Request size validation (debe ir temprano para rechazar requests grandes)
app.add_middleware(RequestSizeMiddleware)

# Rate limiting middleware (debe ir antes de otros middlewares)
# Deshabilitar en modo testing para evitar bloqueos en tests
if os.getenv("TESTING") != "1":
    app.add_middleware(RateLimitMiddleware)

# Metrics middleware
app.add_middleware(MetricsMiddleware)

# Security headers middleware
app.add_middleware(SecurityHeadersMiddleware)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health_router)  # Health checks (no auth required)
app.include_router(metrics_router)  # Metrics endpoint (no auth required)
app.include_router(auth_router)
app.include_router(user_router)
app.include_router(apiary_router)
app.include_router(news_router)
app.include_router(weather_router)
app.include_router(recommendations_router)
app.include_router(notification_router)
app.include_router(drum_router)
app.include_router(task_router)
app.include_router(audio_router)

# Import cache router after other routers
from app.routers.cache import router as cache_router
app.include_router(cache_router)

@app.get("/")
async def root():
    return {"message": "UnAuthorized"}

