from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List

from exponent_server_sdk import PushClient, PushMessage
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.models.apiary import Apiary
from app.models.device import Device
from app.models.notification import Notification
from app.models.subscription import Subscription
from app.models.task import Task
from app.models.user import User
from app.schemas.notification import NotificationCreate

TASK_REMINDER_NOTIFICATION_TYPE = "TASK_REMINDER"
SUBSCRIPTION_REMINDER_NOTIFICATION_TYPE = "SUBSCRIPTION_REMINDER"
WEEKLY_DIGEST_NOTIFICATION_TYPE = "WEEKLY_DIGEST"
EXPO_PUSH_TOKEN_PREFIXES = ("ExponentPushToken[", "ExpoPushToken[")


@dataclass(frozen=True)
class PendingNotification:
    user_id: int
    title: str
    message: str
    notification_type: str
    push_data: dict | None = None
    send_push: bool = False


class NotificationService:
    def __init__(self, db: Session):
        self.db = db

    @staticmethod
    def is_valid_expo_push_token(token: str | None) -> bool:
        if not token:
            return False
        return token.startswith(EXPO_PUSH_TOKEN_PREFIXES) and token.endswith("]")

    @staticmethod
    def _build_notification_key(*, user_id: int, title: str, message: str, notification_type: str) -> tuple[int, str, str, str]:
        return user_id, title, message, notification_type

    def _get_existing_unread_keys(self, pending_notifications: list[PendingNotification]) -> set[tuple[int, str, str, str]]:
        if not pending_notifications:
            return set()

        user_ids = sorted({pending.user_id for pending in pending_notifications})
        notification_types = sorted({pending.notification_type for pending in pending_notifications})
        titles = sorted({pending.title for pending in pending_notifications})

        rows = (
            self.db.query(Notification.userId, Notification.title, Notification.message, Notification.type)
            .filter(
                Notification.userId.in_(user_ids),
                Notification.type.in_(notification_types),
                Notification.title.in_(titles),
                Notification.isRead == False,
            )
            .all()
        )
        return {
            self._build_notification_key(
                user_id=row.userId,
                title=row.title,
                message=row.message,
                notification_type=row.type,
            )
            for row in rows
        }

    def _persist_notifications(self, pending_notifications: list[PendingNotification]) -> int:
        if not pending_notifications:
            return 0

        db_notifications = [
            Notification(
                userId=pending.user_id,
                title=pending.title,
                message=pending.message,
                type=pending.notification_type,
                data=pending.push_data,
            )
            for pending in pending_notifications
        ]

        self.db.add_all(db_notifications)
        self.db.commit()

        for pending in pending_notifications:
            if pending.send_push:
                self.send_push_notification(
                    pending.user_id,
                    pending.title,
                    pending.message,
                    data=pending.push_data,
                )

        return len(db_notifications)

    def get_user_notifications(self, user_id: int, unread_only: bool = False) -> List[Notification]:
        query = self.db.query(Notification).filter(Notification.userId == user_id)
        if unread_only:
            query = query.filter(Notification.isRead == False)
        return query.order_by(Notification.createdAt.desc()).all()

    def get_user_notification_counts(self, user_id: int) -> dict[str, int]:
        total_count = (
            self.db.query(func.count(Notification.id))
            .filter(Notification.userId == user_id)
            .scalar()
            or 0
        )
        unread_count = (
            self.db.query(func.count(Notification.id))
            .filter(
                Notification.userId == user_id,
                Notification.isRead == False,
            )
            .scalar()
            or 0
        )
        return {
            "totalCount": int(total_count),
            "unreadCount": int(unread_count),
        }

    def _notification_exists(
        self,
        *,
        user_id: int,
        title: str,
        message: str,
        notification_type: str,
    ) -> bool:
        return (
            self.db.query(Notification)
            .filter(
                Notification.userId == user_id,
                Notification.title == title,
                Notification.message == message,
                Notification.type == notification_type,
                Notification.isRead == False,
            )
            .first()
            is not None
        )

    def send_push_notification(self, user_id: int, title: str, message: str, data: dict = None):
        """
        Envía una notificación push real a través de Expo a todos los dispositivos válidos.
        """
        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                print(f"Usuario {user_id} no encontrado")
                return

            devices = self.db.query(Device).filter(Device.userId == user_id).all()
            legacy_token = user.expoPushToken if self.is_valid_expo_push_token(user.expoPushToken) else None
            if not devices and legacy_token:
                print(f"[LEGACY] Usando token legacy para usuario {user_id}")

                class LegacyDevice:
                    def __init__(self, token):
                        self.expoPushToken = token
                        self.id = None
                        self.deviceName = "Legacy Device"

                devices = [LegacyDevice(legacy_token)]

            if not devices:
                print(f"Usuario {user_id} no tiene dispositivos registrados")
                return

            push_client = PushClient()
            success_count = 0
            error_count = 0
            invalid_tokens_cleared = 0

            for device in devices:
                token = getattr(device, "expoPushToken", None)
                if not self.is_valid_expo_push_token(token):
                    if isinstance(device, Device) and device.expoPushToken:
                        device.expoPushToken = None
                        invalid_tokens_cleared += 1
                    continue

                try:
                    push_message = PushMessage(
                        to=token,
                        sound="default",
                        title=title,
                        body=message,
                        priority="high",
                        channel_id="default",
                        data=data or {},
                    )
                    response = push_client.publish(push_message)
                    device_name = getattr(device, "deviceName", "Unknown") or "Unknown"
                    print(f"Push enviada a dispositivo {device.id or 'legacy'} ({device_name}): {response.status}")
                    success_count += 1
                except Exception as exc:
                    error_count += 1
                    device_name = getattr(device, "deviceName", "Unknown") or "Unknown"
                    print(f"Error enviando push a dispositivo {device.id or 'legacy'} ({device_name}): {exc}")
                    if isinstance(device, Device) and "push token" in str(exc).lower():
                        device.expoPushToken = None
                        invalid_tokens_cleared += 1

            if invalid_tokens_cleared:
                self.db.commit()

            print(f"Push notifications enviadas a {user.email}: {success_count} exitosas, {error_count} errores")
        except Exception as exc:
            print(f"Error enviando push notification: {exc}")
            import traceback

            traceback.print_exc()

    def create_notification(
        self,
        notification: NotificationCreate,
        push_data: dict = None,
        send_push: bool | None = None,
    ):
        """
        Crea una notificación en base de datos y opcionalmente envía push.
        """
        db_notification = Notification(**notification.model_dump(), data=push_data)
        self.db.add(db_notification)
        self.db.commit()
        self.db.refresh(db_notification)

        push_enabled = notification.type == "ALERT" if send_push is None else send_push
        if push_enabled:
            self.send_push_notification(
                notification.userId,
                notification.title,
                notification.message,
                data=push_data,
            )

        return db_notification

    def create_notification_once(
        self,
        notification: NotificationCreate,
        push_data: dict = None,
        send_push: bool | None = None,
    ) -> bool:
        if self._notification_exists(
            user_id=notification.userId,
            title=notification.title,
            message=notification.message,
            notification_type=notification.type,
        ):
            return False

        self.create_notification(notification, push_data=push_data, send_push=send_push)
        return True

    def mark_as_read(self, notification_id: int, user_id: int):
        notification = self.db.query(Notification).filter(
            Notification.id == notification_id,
            Notification.userId == user_id,
        ).first()
        if notification:
            notification.isRead = True
            self.db.commit()
            return True
        return False

    def mark_all_as_read(self, user_id: int) -> int:
        marked_count = (
            self.db.query(Notification)
            .filter(
                Notification.userId == user_id,
                Notification.isRead == False,
            )
            .update({Notification.isRead: True}, synchronize_session=False)
        )
        self.db.commit()
        return int(marked_count or 0)

    def create_task_due_reminders(
        self,
        reference_time: datetime | None = None,
        reminder_window: timedelta = timedelta(days=1),
    ) -> int:
        now = reference_time or datetime.utcnow()
        due_before = now + reminder_window
        tasks = (
            self.db.query(Task)
            .filter(
                Task.completed == False,
                Task.due_date.isnot(None),
                Task.due_date <= due_before,
            )
            .all()
        )

        pending_notifications: list[PendingNotification] = []
        for task in tasks:
            due_date = task.due_date
            if due_date is None:
                continue

            if due_date.date() < now.date():
                title = "Tarea vencida"
                message = f"La tarea '{task.title}' está vencida desde el {due_date.strftime('%d/%m/%Y')}."
            elif due_date.date() == now.date():
                title = "Tarea para hoy"
                message = f"La tarea '{task.title}' vence hoy."
            else:
                title = "Tarea próxima"
                message = f"La tarea '{task.title}' vence el {due_date.strftime('%d/%m/%Y')}."

            push_data = {"taskId": task.id}
            if task.apiary_id is not None:
                push_data["apiaryId"] = task.apiary_id

            pending_notifications.append(
                PendingNotification(
                    user_id=task.user_id,
                    title=title,
                    message=message,
                    notification_type=TASK_REMINDER_NOTIFICATION_TYPE,
                    push_data=push_data,
                    send_push=True,
                )
            )

        existing_keys = self._get_existing_unread_keys(pending_notifications)
        notifications_to_create = [
            pending
            for pending in pending_notifications
            if self._build_notification_key(
                user_id=pending.user_id,
                title=pending.title,
                message=pending.message,
                notification_type=pending.notification_type,
            )
            not in existing_keys
        ]

        return self._persist_notifications(notifications_to_create)

    def create_subscription_expiry_reminders(
        self,
        reference_time: datetime | None = None,
        reminder_days: tuple[int, ...] = (7, 3, 1),
    ) -> int:
        now = reference_time or datetime.utcnow()
        max_days = max(reminder_days)
        expiring_subscriptions = (
            self.db.query(Subscription)
            .filter(
                Subscription.status == "active",
                Subscription.expiresAt.isnot(None),
                Subscription.expiresAt > now,
                Subscription.expiresAt <= now + timedelta(days=max_days),
                Subscription.tier != "aprendiz",
            )
            .all()
        )

        pending_notifications: list[PendingNotification] = []
        for subscription in expiring_subscriptions:
            expires_at = subscription.expiresAt
            if expires_at is None:
                continue

            days_remaining = (expires_at.date() - now.date()).days
            if days_remaining not in reminder_days:
                continue

            if days_remaining == 1:
                message = "Tu plan vence mañana. Renovalo para no perder acceso premium."
            else:
                message = (
                    f"Tu plan vence en {days_remaining} días. "
                    "Revisá tu suscripción para mantener el acceso premium."
                )

            pending_notifications.append(
                PendingNotification(
                    user_id=subscription.userId,
                    title="Tu suscripción vence pronto",
                    message=message,
                    notification_type=SUBSCRIPTION_REMINDER_NOTIFICATION_TYPE,
                    push_data={
                        "subscriptionId": subscription.id,
                        "daysRemaining": days_remaining,
                    },
                    send_push=True,
                )
            )

        existing_keys = self._get_existing_unread_keys(pending_notifications)
        notifications_to_create = [
            pending
            for pending in pending_notifications
            if self._build_notification_key(
                user_id=pending.user_id,
                title=pending.title,
                message=pending.message,
                notification_type=pending.notification_type,
            )
            not in existing_keys
        ]

        return self._persist_notifications(notifications_to_create)

    def create_weekly_digest(self, reference_time: datetime | None = None) -> int:
        now = reference_time or datetime.utcnow()
        neglected_threshold = now - timedelta(days=30)
        iso_week = now.isocalendar().week

        pending_counts = dict(
            self.db.query(Task.user_id, func.count(Task.id))
            .filter(Task.completed == False)
            .group_by(Task.user_id)
            .all()
        )
        overdue_counts = dict(
            self.db.query(Task.user_id, func.count(Task.id))
            .filter(
                Task.completed == False,
                Task.due_date.isnot(None),
                Task.due_date < now,
            )
            .group_by(Task.user_id)
            .all()
        )
        neglected_counts = dict(
            self.db.query(Apiary.userId, func.count(Apiary.id))
            .filter(Apiary.updatedAt < neglected_threshold)
            .group_by(Apiary.userId)
            .all()
        )

        user_ids = sorted(set(pending_counts) | set(overdue_counts) | set(neglected_counts))
        if not user_ids:
            return 0

        pending_notifications: list[PendingNotification] = []
        for user_id in user_ids:
            pending_tasks = int(pending_counts.get(user_id, 0) or 0)
            overdue_tasks = int(overdue_counts.get(user_id, 0) or 0)
            neglected_apiaries = int(neglected_counts.get(user_id, 0) or 0)

            if pending_tasks == 0 and overdue_tasks == 0 and neglected_apiaries == 0:
                continue

            message = (
                f"Semana {iso_week}: {pending_tasks} tareas pendientes, "
                f"{overdue_tasks} vencidas y {neglected_apiaries} apiarios sin visitar."
            )
            pending_notifications.append(
                PendingNotification(
                    user_id=user_id,
                    title="Resumen semanal",
                    message=message,
                    notification_type=WEEKLY_DIGEST_NOTIFICATION_TYPE,
                    push_data={
                        "isoWeek": iso_week,
                        "pendingTasks": pending_tasks,
                        "overdueTasks": overdue_tasks,
                        "neglectedApiaries": neglected_apiaries,
                    },
                    send_push=False,
                )
            )

        existing_keys = self._get_existing_unread_keys(pending_notifications)
        notifications_to_create = [
            pending
            for pending in pending_notifications
            if self._build_notification_key(
                user_id=pending.user_id,
                title=pending.title,
                message=pending.message,
                notification_type=pending.notification_type,
            )
            not in existing_keys
        ]

        return self._persist_notifications(notifications_to_create)

    def cleanup_stale_devices(
        self,
        reference_time: datetime | None = None,
        stale_device_days: int = 90,
    ) -> dict:
        now = reference_time or datetime.utcnow()
        stale_threshold = now - timedelta(days=stale_device_days)

        invalid_device_tokens_cleared = 0
        invalid_legacy_tokens_cleared = 0
        stale_devices_deleted = 0

        for device in self.db.query(Device).filter(Device.expoPushToken.isnot(None)).all():
            if not self.is_valid_expo_push_token(device.expoPushToken):
                device.expoPushToken = None
                invalid_device_tokens_cleared += 1

        for user in self.db.query(User).filter(User.expoPushToken.isnot(None)).all():
            if not self.is_valid_expo_push_token(user.expoPushToken):
                user.expoPushToken = None
                invalid_legacy_tokens_cleared += 1

        stale_devices = (
            self.db.query(Device)
            .filter(
                Device.lastActive < stale_threshold,
                or_(Device.expoPushToken.is_(None), Device.expoPushToken == ""),
            )
            .all()
        )
        for device in stale_devices:
            self.db.delete(device)
            stale_devices_deleted += 1

        self.db.commit()
        return {
            "invalidDeviceTokensCleared": invalid_device_tokens_cleared,
            "invalidLegacyTokensCleared": invalid_legacy_tokens_cleared,
            "staleDevicesDeleted": stale_devices_deleted,
        }

    def check_apiary_alerts(self):
        """
        Revisa apiarios no actualizados recientemente y genera alertas.
        """
        threshold_date = datetime.now() - timedelta(days=30)
        neglected_apiaries = self.db.query(Apiary).filter(Apiary.updatedAt < threshold_date).all()
        if not neglected_apiaries:
            return 0

        pending_notifications: list[PendingNotification] = []
        for apiary in neglected_apiaries:
            pending_notifications.append(
                PendingNotification(
                    user_id=apiary.userId,
                    title="Apiario sin visitar",
                    message=f"Hace más de 30 días que no registras actividad en el apiario '{apiary.name}'.",
                    notification_type="ALERT",
                    push_data={"apiaryId": apiary.id},
                    send_push=True,
                )
            )

        existing_keys = self._get_existing_unread_keys(pending_notifications)
        notifications_to_create = [
            pending
            for pending in pending_notifications
            if self._build_notification_key(
                user_id=pending.user_id,
                title=pending.title,
                message=pending.message,
                notification_type=pending.notification_type,
            )
            not in existing_keys
        ]

        return self._persist_notifications(notifications_to_create)
