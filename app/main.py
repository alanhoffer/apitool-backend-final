from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.routers import auth_router, user_router, apiary_router, news_router, weather_router, recommendations_router, notification_router
from app.database import engine, Base
from app.cron import scheduler
import os
import logging
from sqlalchemy.exc import OperationalError

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

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router)
app.include_router(user_router)
app.include_router(apiary_router)
app.include_router(news_router)
app.include_router(weather_router)
app.include_router(recommendations_router)
app.include_router(notification_router)

@app.get("/")
async def root():
    return {"message": "UnAuthorized"}

