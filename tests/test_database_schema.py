from sqlalchemy import inspect, text

from app.database import ensure_runtime_schema_compatibility


def test_ensure_runtime_schema_adds_missing_notification_data_column(db):
    db.execute(text("DROP TABLE IF EXISTS devices"))
    db.execute(text("DROP TABLE IF EXISTS tasks"))
    db.execute(text("DROP TABLE IF EXISTS apiary"))
    db.execute(text("DROP TABLE IF EXISTS notifications"))
    db.execute(
        text(
            """
            CREATE TABLE apiary (
                id INTEGER PRIMARY KEY,
                "userId" INTEGER NOT NULL,
                "updatedAt" DATETIME,
                "managementType" VARCHAR
            )
            """
        )
    )
    db.execute(
        text(
            """
            CREATE TABLE tasks (
                id INTEGER PRIMARY KEY,
                user_id INTEGER NOT NULL,
                apiary_id INTEGER,
                completed BOOLEAN,
                due_date DATETIME
            )
            """
        )
    )
    db.execute(
        text(
            """
            CREATE TABLE notifications (
                id INTEGER PRIMARY KEY,
                "userId" INTEGER NOT NULL,
                title VARCHAR NOT NULL,
                message VARCHAR NOT NULL,
                type VARCHAR,
                "isRead" BOOLEAN,
                "createdAt" DATETIME
            )
            """
        )
    )
    db.execute(
        text(
            """
            CREATE TABLE devices (
                id INTEGER PRIMARY KEY,
                "userId" INTEGER NOT NULL,
                "lastActive" DATETIME,
                "expoPushToken" VARCHAR
            )
            """
        )
    )
    db.commit()

    ensure_runtime_schema_compatibility(db.bind)

    inspector = inspect(db.bind)
    columns = {column["name"] for column in inspector.get_columns("notifications")}
    notification_indexes = {index["name"] for index in inspector.get_indexes("notifications")}
    task_indexes = {index["name"] for index in inspector.get_indexes("tasks")}
    apiary_indexes = {index["name"] for index in inspector.get_indexes("apiary")}
    device_indexes = {index["name"] for index in inspector.get_indexes("devices")}

    assert "data" in columns
    assert "idx_notifications_user_read_created" in notification_indexes
    assert "idx_notifications_user_type_title_read" in notification_indexes
    assert "idx_tasks_user_completed_due" in task_indexes
    assert "idx_tasks_user_apiary" in task_indexes
    assert "idx_apiary_user_updated_at" in apiary_indexes
    assert "idx_apiary_user_management_type" in apiary_indexes
    assert "idx_devices_last_active_token" in device_indexes
