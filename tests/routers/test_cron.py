import os


def test_daily_cron_requires_configured_secret(client, monkeypatch):
    monkeypatch.delenv("CRON_SECRET", raising=False)

    response = client.get("/internal/cron/daily")

    assert response.status_code == 503
    assert response.json()["detail"] == "Cron secret not configured"


def test_daily_cron_requires_valid_authorization(client, monkeypatch):
    monkeypatch.setenv("CRON_SECRET", "super-secret")

    response = client.get("/internal/cron/daily", headers={"Authorization": "Bearer wrong"})

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid cron authorization"


def test_daily_cron_runs_maintenance(client, monkeypatch):
    monkeypatch.setenv("CRON_SECRET", "super-secret")

    def fake_run_daily_maintenance():
        return {
            "job": "daily_apiary_update",
            "status": "success",
            "alertsCount": 2,
            "durationSeconds": 0.123,
        }

    monkeypatch.setattr("app.routers.cron.run_daily_maintenance", fake_run_daily_maintenance)

    response = client.get(
        "/internal/cron/daily",
        headers={"Authorization": "Bearer super-secret"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "job": "daily_apiary_update",
        "status": "success",
        "alertsCount": 2,
        "durationSeconds": 0.123,
    }


def test_named_cron_runs_specific_job(client, monkeypatch):
    monkeypatch.setenv("CRON_SECRET", "super-secret")

    def fake_run_task_reminders_job():
        return {
            "job": "task_reminders",
            "status": "success",
            "taskRemindersCreated": 3,
            "durationSeconds": 0.456,
        }

    monkeypatch.setattr("app.routers.cron.run_task_reminders_job", fake_run_task_reminders_job)

    response = client.get(
        "/internal/cron/task-reminders",
        headers={"Authorization": "Bearer super-secret"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "job": "task_reminders",
        "status": "success",
        "taskRemindersCreated": 3,
        "durationSeconds": 0.456,
    }


def test_named_cron_rejects_unknown_job(client, monkeypatch):
    monkeypatch.setenv("CRON_SECRET", "super-secret")

    response = client.get(
        "/internal/cron/not-a-real-job",
        headers={"Authorization": "Bearer super-secret"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Unknown cron job"
