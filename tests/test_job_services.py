from datetime import datetime, timedelta

from app.models.apiary import Apiary
from app.models.device import Device
from app.models.notification import Notification
from app.models.subscription import Subscription
from app.models.task import Task
from app.models.user import User
from app.services.notification_service import (
    NotificationService,
    SUBSCRIPTION_REMINDER_NOTIFICATION_TYPE,
    TASK_REMINDER_NOTIFICATION_TYPE,
    WEEKLY_DIGEST_NOTIFICATION_TYPE,
)
from app.services.subscription_service import SubscriptionService


def test_create_task_due_reminders_creates_and_deduplicates_notifications(db, test_user, monkeypatch):
    now = datetime(2026, 4, 26, 10, 0, 0)
    due_today = Task(
        user_id=test_user.id,
        title="Revisar colmena 1",
        completed=False,
        due_date=now + timedelta(hours=2),
    )
    overdue = Task(
        user_id=test_user.id,
        title="Alimentar apiario norte",
        completed=False,
        due_date=now - timedelta(days=2),
    )
    future = Task(
        user_id=test_user.id,
        title="Cosecha futura",
        completed=False,
        due_date=now + timedelta(days=5),
    )
    db.add_all([due_today, overdue, future])
    db.commit()

    monkeypatch.setattr(NotificationService, "send_push_notification", lambda *args, **kwargs: None)

    service = NotificationService(db)
    created = service.create_task_due_reminders(reference_time=now)
    second_run_created = service.create_task_due_reminders(reference_time=now)

    notifications = db.query(Notification).all()
    notifications_by_message = {notification.message: notification for notification in notifications}

    assert created == 2
    assert second_run_created == 0
    assert len(notifications) == 2
    assert {notification.type for notification in notifications} == {TASK_REMINDER_NOTIFICATION_TYPE}
    assert notifications_by_message["La tarea 'Revisar colmena 1' vence hoy."].data == {"taskId": due_today.id}
    assert notifications_by_message["La tarea 'Alimentar apiario norte' está vencida desde el 24/04/2026."].data == {
        "taskId": overdue.id
    }


def test_create_subscription_expiry_reminders_creates_notification(db, test_user, monkeypatch):
    now = datetime(2026, 4, 26, 10, 0, 0)
    subscription = Subscription(
        userId=test_user.id,
        tier="maestro",
        status="active",
        expiresAt=now + timedelta(days=3),
    )
    db.add(subscription)
    db.commit()

    monkeypatch.setattr(NotificationService, "send_push_notification", lambda *args, **kwargs: None)

    created = NotificationService(db).create_subscription_expiry_reminders(reference_time=now)
    notifications = db.query(Notification).all()

    assert created == 1
    assert len(notifications) == 1
    assert notifications[0].type == SUBSCRIPTION_REMINDER_NOTIFICATION_TYPE
    assert notifications[0].data == {"subscriptionId": subscription.id, "daysRemaining": 3}


def test_reconcile_expired_subscriptions_demotes_to_aprendiz(db, test_user):
    now = datetime(2026, 4, 26, 10, 0, 0)
    subscription = Subscription(
        userId=test_user.id,
        tier="maestro",
        status="active",
        expiresAt=now - timedelta(hours=1),
    )
    db.add(subscription)
    db.commit()

    updated = SubscriptionService(db).reconcile_expired_subscriptions(reference_time=now)
    db.refresh(subscription)

    assert updated == 1
    assert subscription.status == "expired"
    assert subscription.tier == "aprendiz"


def test_cleanup_stale_devices_clears_invalid_tokens_and_deletes_old_devices(db, test_user):
    now = datetime(2026, 4, 26, 10, 0, 0)
    test_user.expoPushToken = "native-fcm-token"

    valid_device = Device(
        userId=test_user.id,
        deviceName="Pixel 9",
        platform="android",
        expoPushToken="ExponentPushToken[valid-token]",
        lastActive=now,
    )
    invalid_device = Device(
        userId=test_user.id,
        deviceName="Moto G",
        platform="android",
        expoPushToken="native-fcm-token",
        lastActive=now,
    )
    stale_device = Device(
        userId=test_user.id,
        deviceName="Old tablet",
        platform="android",
        expoPushToken=None,
        lastActive=now - timedelta(days=120),
    )
    db.add_all([valid_device, invalid_device, stale_device])
    db.commit()

    result = NotificationService(db).cleanup_stale_devices(reference_time=now)

    db.refresh(test_user)
    db.refresh(valid_device)
    db.refresh(invalid_device)

    assert result == {
        "invalidDeviceTokensCleared": 1,
        "invalidLegacyTokensCleared": 1,
        "staleDevicesDeleted": 1,
    }
    assert test_user.expoPushToken is None
    assert valid_device.expoPushToken == "ExponentPushToken[valid-token]"
    assert invalid_device.expoPushToken is None
    assert db.query(Device).filter(Device.id == stale_device.id).first() is None


def test_create_weekly_digest_uses_current_state(db, test_user):
    now = datetime(2026, 4, 27, 9, 0, 0)
    task = Task(
        user_id=test_user.id,
        title="Tarea pendiente",
        completed=False,
        due_date=now - timedelta(days=1),
    )
    apiary = Apiary(
        userId=test_user.id,
        name="Apiario Sur",
        hives=4,
        status="normal",
        image="apiary-default.png",
        updatedAt=now - timedelta(days=45),
    )
    db.add_all([task, apiary])
    db.commit()

    created = NotificationService(db).create_weekly_digest(reference_time=now)
    notifications = db.query(Notification).all()

    assert created == 1
    assert len(notifications) == 1
    assert notifications[0].type == WEEKLY_DIGEST_NOTIFICATION_TYPE
    assert notifications[0].title == "Resumen semanal"
    assert notifications[0].data["pendingTasks"] == 1
    assert notifications[0].data["overdueTasks"] == 1
    assert notifications[0].data["neglectedApiaries"] == 1
