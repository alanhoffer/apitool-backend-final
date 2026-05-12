from contextlib import asynccontextmanager
import logging
import os
import time

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import OperationalError

from app.config import settings
from app.cron import scheduler
from app.database import Base, engine, ensure_runtime_schema_compatibility
from app.middleware.metrics import MetricsMiddleware
from app.middleware.rate_limit import RateLimitMiddleware
from app.middleware.request_id import RequestIDMiddleware
from app.middleware.request_size import RequestSizeMiddleware
from app.middleware.security_headers import SecurityHeadersMiddleware
from app.routers import (
    account_deletion_router,
    apiary_router,
    auth_router,
    cron_router,
    drum_router,
    hive_router,
    legal_router,
    news_router,
    notification_router,
    recommendations_router,
    subscription_router,
    task_router,
    user_router,
    weather_router,
)
from app.routers.audio import router as audio_router
from app.routers.health import router as health_router
from app.routers.metrics import router as metrics_router
from app.runtime import should_run_scheduler, should_run_startup_schema_sync
from app.utils.logging_config import setup_logging

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


def _custom_middleware_enabled() -> bool:
    return os.getenv("DISABLE_CUSTOM_MIDDLEWARE", "false").lower() != "true"


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    if os.getenv("TESTING") != "1":
        if should_run_startup_schema_sync():
            # En runtimes persistentes podemos verificar el schema en startup.
            try:
                Base.metadata.create_all(bind=engine)
                ensure_runtime_schema_compatibility()
                logger.info("Database tables created/verified successfully")
            except OperationalError as exc:
                logger.warning(f"Could not connect to database during startup: {exc}")
                logger.warning(
                    "Server will start, but database operations will fail until connection is available"
                )
            except Exception as exc:
                logger.error(f"Unexpected error creating database tables: {exc}")
        else:
            logger.info("Skipping startup schema sync in serverless/runtime-constrained environment")

        if should_run_scheduler() and not scheduler.running:
            scheduler.start()
    yield
    # Shutdown
    if os.getenv("TESTING") != "1" and scheduler.running:
        scheduler.shutdown()


app = FastAPI(
    title="API Tool",
    version=settings.app_version,
    lifespan=lifespan,
)

# Request ID middleware (debe ir primero para que todos los logs tengan request_id)
if _custom_middleware_enabled():
    app.add_middleware(RequestIDMiddleware)

# Request size validation (debe ir temprano para rechazar requests grandes)
if _custom_middleware_enabled():
    app.add_middleware(RequestSizeMiddleware)

# Rate limiting middleware (debe ir antes de otros middlewares)
# Deshabilitar en modo testing para evitar bloqueos en tests
if _custom_middleware_enabled() and os.getenv("TESTING") != "1" and settings.rate_limit_enabled:
    app.add_middleware(RateLimitMiddleware)

# Metrics middleware
if _custom_middleware_enabled():
    app.add_middleware(MetricsMiddleware)

# Security headers middleware
if _custom_middleware_enabled():
    app.add_middleware(SecurityHeadersMiddleware)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=settings.cors_origins_list != ["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health_router)  # Health checks (no auth required)
app.include_router(metrics_router)  # Metrics endpoint (no auth required)
app.include_router(cron_router)  # Cron endpoint secured by CRON_SECRET
app.include_router(auth_router)
app.include_router(user_router)
app.include_router(apiary_router)
app.include_router(news_router)
app.include_router(weather_router)
app.include_router(recommendations_router)
app.include_router(notification_router)
app.include_router(drum_router)
app.include_router(hive_router)
app.include_router(task_router)
app.include_router(audio_router)
app.include_router(subscription_router)
app.include_router(account_deletion_router)
app.include_router(legal_router)

# Import cache router after other routers
from app.routers.cache import router as cache_router

app.include_router(cache_router)


@app.get("/")
async def root():
    return {"message": "UnAuthorized"}
