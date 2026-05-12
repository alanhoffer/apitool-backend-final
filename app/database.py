from sqlalchemy import create_engine, inspect, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from app.config import settings

import os


DATABASE_URL = settings.effective_database_url

# Configurar timezone UTC para la conexion
timezone = os.getenv("TZ", "UTC")
connect_args = {}

if DATABASE_URL.startswith("postgresql"):
    option_parts = [f"-c statement_timeout=30000", f"-c timezone={timezone}"]
    if settings.db_schema:
        option_parts.append(f"-c search_path={settings.db_schema},public")
    connect_args = {
        "connect_timeout": 10,
        "options": " ".join(option_parts),
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


def ensure_runtime_schema_compatibility(bind=None) -> None:
    """
    Apply small idempotent schema fixes that `create_all()` cannot handle.

    This keeps production alive when a legacy table is missing a non-breaking
    nullable column that newer API code expects.
    """
    active_bind = bind or engine
    inspector = inspect(active_bind)

    with active_bind.begin() as connection:
        if inspector.has_table("notifications"):
            notification_columns = {column["name"] for column in inspector.get_columns("notifications")}
            if "data" not in notification_columns:
                connection.execute(text('ALTER TABLE notifications ADD COLUMN data JSON NULL'))

            connection.execute(
                text(
                    'CREATE INDEX IF NOT EXISTS idx_notifications_user_read_created '
                    'ON notifications ("userId", "isRead", "createdAt")'
                )
            )
            connection.execute(
                text(
                    'CREATE INDEX IF NOT EXISTS idx_notifications_user_type_title_read '
                    'ON notifications ("userId", type, title, "isRead")'
                )
            )

        if inspector.has_table("tasks"):
            connection.execute(
                text(
                    'CREATE INDEX IF NOT EXISTS idx_tasks_user_completed_due '
                    'ON tasks (user_id, completed, due_date)'
                )
            )
            connection.execute(
                text(
                    'CREATE INDEX IF NOT EXISTS idx_tasks_user_apiary '
                    'ON tasks (user_id, apiary_id)'
                )
            )

        if inspector.has_table("apiary"):
            connection.execute(
                text(
                    'CREATE INDEX IF NOT EXISTS idx_apiary_user_updated_at '
                    'ON apiary ("userId", "updatedAt")'
                )
            )
            connection.execute(
                text(
                    'CREATE INDEX IF NOT EXISTS idx_apiary_user_management_type '
                    'ON apiary ("userId", "managementType")'
                )
            )

        if inspector.has_table("devices"):
            connection.execute(
                text(
                    'CREATE INDEX IF NOT EXISTS idx_devices_last_active_token '
                    'ON devices ("lastActive", "expoPushToken")'
                )
            )


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
