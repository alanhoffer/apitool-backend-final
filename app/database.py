from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from app.config import settings

import os


DATABASE_URL = settings.effective_database_url

# Configurar timezone UTC para la conexion
timezone = os.getenv("TZ", "UTC")
connect_args = {}

if DATABASE_URL.startswith("postgresql"):
    connect_args = {
        "connect_timeout": 10,
        "options": f"-c statement_timeout=30000 -c timezone={timezone}",
    }

# Configurar el engine con timeouts y pool settings para mejor manejo de errores
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=3600,
    connect_args=connect_args,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
