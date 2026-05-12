import os

from fastapi import APIRouter, Header, HTTPException, status

from app.cron import (
    run_apiary_alerts_job,
    run_apiary_maintenance_job,
    run_daily_maintenance,
    run_push_token_cleanup_job,
    run_subscription_reconciliation_job,
    run_subscription_reminders_job,
    run_task_reminders_job,
    run_weekly_digest_job,
)

router = APIRouter(prefix="/internal/cron", tags=["cron"])

JOB_RUNNER_NAMES = {
    "daily": "run_daily_maintenance",
    "apiary-maintenance": "run_apiary_maintenance_job",
    "apiary-alerts": "run_apiary_alerts_job",
    "task-reminders": "run_task_reminders_job",
    "subscription-reminders": "run_subscription_reminders_job",
    "subscription-reconciliation": "run_subscription_reconciliation_job",
    "push-token-cleanup": "run_push_token_cleanup_job",
    "weekly-digest": "run_weekly_digest_job",
}


def _get_cron_secret() -> str:
    return os.getenv("CRON_SECRET", "").strip()


def _authorize_cron_request(authorization: str | None) -> None:
    cron_secret = _get_cron_secret()
    if not cron_secret:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Cron secret not configured",
        )

    expected_header = f"Bearer {cron_secret}"
    if authorization != expected_header:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid cron authorization",
        )


@router.get("/{job_name}")
async def run_cron_job(job_name: str, authorization: str | None = Header(default=None)):
    _authorize_cron_request(authorization)

    runner_name = JOB_RUNNER_NAMES.get(job_name)
    if not runner_name:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Unknown cron job",
        )

    runner = globals()[runner_name]
    return runner()
