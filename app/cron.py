import logging
import time

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.services.apiary_service import ApiaryService
from app.services.notification_service import NotificationService
from app.services.subscription_service import SubscriptionService

try:
    from app.utils.business_metrics import (
        cron_jobs_executed_total,
        cron_job_duration_seconds,
    )

    METRICS_AVAILABLE = True
except (ImportError, AttributeError):
    METRICS_AVAILABLE = False

    class DummyMetric:
        def labels(self, **kwargs):
            return self

        def inc(self, value=1):
            pass

        def observe(self, value):
            pass

    cron_jobs_executed_total = DummyMetric()
    cron_job_duration_seconds = DummyMetric()


logger = logging.getLogger(__name__)
scheduler = AsyncIOScheduler()
TREATMENT_TYPES = ("tFence", "tAmitraz", "tFlumetrine", "tOxalic")


def _execute_job(job_name: str, job_handler) -> dict:
    start_time = time.time()
    db: Session = SessionLocal()
    try:
        result = job_handler(db) or {}
        duration = time.time() - start_time
        cron_jobs_executed_total.labels(job_name=job_name, status="success").inc()
        cron_job_duration_seconds.labels(job_name=job_name).observe(duration)
        payload = {
            "job": job_name,
            "status": "success",
            "durationSeconds": round(duration, 3),
        }
        payload.update(result)
        return payload
    except Exception as error:
        duration = time.time() - start_time
        cron_jobs_executed_total.labels(job_name=job_name, status="failed").inc()
        cron_job_duration_seconds.labels(job_name=job_name).observe(duration)
        logger.error(f"Error running cron job {job_name}: {error}", exc_info=True)
        raise
    finally:
        db.close()


def _run_apiary_maintenance(db: Session) -> dict:
    apiary_service = ApiaryService(db)
    apiary_service.subtract_food()
    for treatment_type in TREATMENT_TYPES:
        apiary_service.subtract_one_day_treatment(treatment_type)

    logger.info("Se completó el mantenimiento diario de apiarios.")
    return {"treatmentsProcessed": list(TREATMENT_TYPES)}


def _run_apiary_alerts(db: Session) -> dict:
    alerts_count = NotificationService(db).check_apiary_alerts()
    if alerts_count > 0:
        logger.info(f"Se generaron {alerts_count} alertas de apiarios.")
    return {"alertsCount": alerts_count}


def _run_task_reminders(db: Session) -> dict:
    reminders_created = NotificationService(db).create_task_due_reminders()
    return {"taskRemindersCreated": reminders_created}


def _run_subscription_reminders(db: Session) -> dict:
    reminders_created = NotificationService(db).create_subscription_expiry_reminders()
    return {"subscriptionRemindersCreated": reminders_created}


def _run_subscription_reconciliation(db: Session) -> dict:
    subscriptions_updated = SubscriptionService(db).reconcile_expired_subscriptions()
    return {"subscriptionsReconciled": subscriptions_updated}


def _run_push_token_cleanup(db: Session) -> dict:
    return NotificationService(db).cleanup_stale_devices()


def _run_weekly_digest(db: Session) -> dict:
    digests_created = NotificationService(db).create_weekly_digest()
    return {"weeklyDigestsCreated": digests_created}


def _run_daily_operations(db: Session) -> dict:
    return {
        "results": {
            "apiaryMaintenance": _run_apiary_maintenance(db),
            "apiaryAlerts": _run_apiary_alerts(db),
            "taskReminders": _run_task_reminders(db),
            "subscriptionReminders": _run_subscription_reminders(db),
            "subscriptionReconciliation": _run_subscription_reconciliation(db),
        }
    }


def run_daily_maintenance() -> dict:
    return _execute_job("daily_apiary_update", _run_daily_operations)


def run_apiary_maintenance_job() -> dict:
    return _execute_job("apiary_maintenance", _run_apiary_maintenance)


def run_apiary_alerts_job() -> dict:
    return _execute_job("apiary_alerts", _run_apiary_alerts)


def run_task_reminders_job() -> dict:
    return _execute_job("task_reminders", _run_task_reminders)


def run_subscription_reminders_job() -> dict:
    return _execute_job("subscription_reminders", _run_subscription_reminders)


def run_subscription_reconciliation_job() -> dict:
    return _execute_job("subscription_reconciliation", _run_subscription_reconciliation)


def run_push_token_cleanup_job() -> dict:
    return _execute_job("push_token_cleanup", _run_push_token_cleanup)


def run_weekly_digest_job() -> dict:
    return _execute_job("weekly_digest", _run_weekly_digest)


def _register_job(func, *, hour: int, minute: int, job_id: str, name: str, day_of_week: str | None = None) -> None:
    trigger_kwargs = {"hour": hour, "minute": minute}
    if day_of_week is not None:
        trigger_kwargs["day_of_week"] = day_of_week

    scheduler.add_job(
        func,
        trigger=CronTrigger(**trigger_kwargs),
        id=job_id,
        name=name,
        replace_existing=True,
        max_instances=1,
    )


_register_job(
    run_apiary_maintenance_job,
    hour=0,
    minute=0,
    job_id="apiary_maintenance",
    name="Run apiary maintenance",
)
_register_job(
    run_apiary_alerts_job,
    hour=0,
    minute=10,
    job_id="apiary_alerts",
    name="Generate apiary alerts",
)
_register_job(
    run_task_reminders_job,
    hour=8,
    minute=0,
    job_id="task_reminders",
    name="Create task due reminders",
)
_register_job(
    run_subscription_reminders_job,
    hour=9,
    minute=0,
    job_id="subscription_reminders",
    name="Create subscription expiry reminders",
)
_register_job(
    run_subscription_reconciliation_job,
    hour=9,
    minute=15,
    job_id="subscription_reconciliation",
    name="Reconcile expired subscriptions",
)
_register_job(
    run_push_token_cleanup_job,
    hour=3,
    minute=0,
    day_of_week="sun",
    job_id="push_token_cleanup",
    name="Clean up stale push devices",
)
_register_job(
    run_weekly_digest_job,
    hour=8,
    minute=30,
    day_of_week="mon",
    job_id="weekly_digest",
    name="Create weekly digest notifications",
)
