import pytest
from datetime import datetime, timedelta

from app.models.apiary import Apiary
from app.models.hive import Hive
from app.models.history import History
from app.models.harvest_season import HarvestSeason
from app.models.notification import Notification
from app.models.settings import Settings
from app.models.task import Task

def test_get_user(client, auth_headers, test_user):
    """Test getting current user."""
    response = client.get("/users", headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == test_user.id
    assert data["email"] == test_user.email

def test_get_user_unauthorized(client):
    """Test getting user without authentication."""
    response = client.get("/users")
    
    assert response.status_code == 403


def test_get_dashboard_summary(client, auth_headers, test_user, db):
    overdue_date = datetime.now() - timedelta(days=2)
    due_today = datetime.now()

    apiary = Apiary(
        userId=test_user.id,
        name="Apiario Norte",
        hives=8,
        status="normal",
        honey=12.5,
        sugar=4.0,
        levudex=1.5,
        box=3,
        boxMedium=1,
        boxSmall=0,
    )
    db.add(apiary)
    db.commit()
    db.refresh(apiary)

    db.add(Settings(apiaryId=apiary.id, apiaryUserId=test_user.id))
    db.add(Hive(
        apiaryId=apiary.id,
        userId=test_user.id,
        name="Colmena 1",
        hiveStrength="weak",
        queenStatus="unknown",
        swarming=True,
        lastInspection=(datetime.now() - timedelta(days=45)).date().isoformat(),
    ))
    db.add(Task(title="Revision", completed=False, user_id=test_user.id, due_date=overdue_date))
    db.add(Task(title="Hoy", completed=False, user_id=test_user.id, due_date=due_today))
    db.add(Task(title="Completada", completed=True, user_id=test_user.id))
    db.add(Notification(userId=test_user.id, title="Alerta", message="Pendiente", type="INFO", isRead=False))
    db.add(History(userId=test_user.id, apiaryId=apiary.id, field="box", previousValue="1", newValue="3"))
    db.commit()

    response = client.get("/users/dashboard-summary", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == test_user.id
    assert data["name"] == test_user.name
    assert data["surname"] == test_user.surname
    assert data["pendingTaskCount"] == 2
    assert data["overdueTaskCount"] == 1
    assert data["dueTodayTaskCount"] == 1
    assert data["completedTaskCount"] == 1
    assert data["apiaryCount"] == 1
    assert data["hiveCount"] == 8
    assert data["harvestedApiaryCount"] == 1
    assert data["unreadNotificationCount"] == 1
    assert data["totalHarvestBoxes"] == 4
    assert data["weakHiveCount"] == 1
    assert data["queenIssueHiveCount"] == 1
    assert data["swarmingHiveCount"] == 1
    assert data["staleInspectionHiveCount"] == 1
    assert data["attentionHiveCount"] == 1
    assert data["recentHarvestBoxesToday"] == 2


def test_get_statistics_overview(client, auth_headers, test_user, db):
    now = datetime.now()
    apiary = Apiary(
        userId=test_user.id,
        name="Apiario Centro",
        hives=12,
        status="warning",
        honey=20,
        sugar=6,
        levudex=2,
        box=5,
        boxMedium=2,
        boxSmall=1,
    )
    db.add(apiary)
    db.commit()
    db.refresh(apiary)

    db.add(Settings(apiaryId=apiary.id, apiaryUserId=test_user.id))
    db.add(Hive(
        apiaryId=apiary.id,
        userId=test_user.id,
        name="Colmena fuerte",
        hiveStrength="strong",
        queenStatus="present",
        swarming=False,
        lastInspection=now.date().isoformat(),
    ))
    db.add(Hive(
        apiaryId=apiary.id,
        userId=test_user.id,
        name="Colmena debil",
        hiveStrength="weak",
        queenStatus="absent",
        swarming=False,
        lastInspection=(now - timedelta(days=31)).date().isoformat(),
    ))
    db.add(Task(title="Pendiente", completed=False, user_id=test_user.id, due_date=now + timedelta(days=1)))
    db.add(Task(title="Hecha", completed=True, user_id=test_user.id))
    db.add(History(userId=test_user.id, apiaryId=apiary.id, field="box", previousValue="0", newValue="2", changeDate=now - timedelta(days=2)))
    db.add(History(userId=test_user.id, apiaryId=apiary.id, field="boxMedium", previousValue="0", newValue="1", changeDate=now - timedelta(days=1)))
    db.commit()

    response = client.get("/users/statistics-overview?period=month", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["period"] == "month"
    assert data["apiaryCount"] == 1
    assert data["hiveCount"] == 12
    assert data["totalHarvestBoxes"] == 8
    assert data["periodHarvestBoxes"] == 3
    assert data["pendingTaskCount"] == 1
    assert data["completedTaskCount"] == 1
    assert data["weakHiveCount"] == 1
    assert data["queenIssueHiveCount"] == 1
    assert data["staleInspectionHiveCount"] == 1
    assert data["apiaryStatusCounts"]["Warning"] == 1
    assert data["hiveStrengthCounts"]["Fuerte"] == 1
    assert data["hiveStrengthCounts"]["Debil"] == 1
    assert len(data["harvestSeries"]) == 30


def test_get_statistics_overview_day_period(client, auth_headers, test_user, db):
    now = datetime.now()
    apiary = Apiary(
        userId=test_user.id,
        name="Apiario Diario",
        hives=6,
        status="normal",
        box=4,
        boxMedium=0,
        boxSmall=0,
    )
    db.add(apiary)
    db.commit()
    db.refresh(apiary)

    db.add(Settings(apiaryId=apiary.id, apiaryUserId=test_user.id))
    db.add(
        History(
            userId=test_user.id,
            apiaryId=apiary.id,
            field="box",
            previousValue="0",
            newValue="4",
            changeDate=now,
        )
    )
    db.commit()

    response = client.get("/users/statistics-overview?period=day", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["period"] == "day"
    assert data["periodHarvestBoxes"] == 4
    assert len(data["harvestSeries"]) == 24
    assert any(point["total"] == 4 for point in data["harvestSeries"])


def test_statistics_overview_filters_harvest_history_by_current_year(client, auth_headers, test_user, db):
    current_year = datetime.now().year
    previous_year = current_year - 1
    previous_year_date = datetime(previous_year, 6, 15, 10, 0, 0)
    apiary = Apiary(
        userId=test_user.id,
        name="Apiario temporada anterior",
        hives=9,
        status="normal",
        box=36,
        boxMedium=0,
        boxSmall=0,
    )
    db.add(apiary)
    db.commit()
    db.refresh(apiary)

    db.add(
        HarvestSeason(
            userId=test_user.id,
            name=f"Cosecha {previous_year}",
            status="active",
            startedAt=datetime(previous_year, 1, 1),
        )
    )
    db.add(Settings(apiaryId=apiary.id, apiaryUserId=test_user.id))
    db.add(
        History(
            userId=test_user.id,
            apiaryId=apiary.id,
            field="box",
            previousValue="0",
            newValue="36",
            changeDate=previous_year_date,
        )
    )
    db.commit()

    response = client.get("/users/statistics-overview?period=month", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["totalHarvestBoxes"] == 0
    assert data["periodHarvestBoxes"] == 0
    assert data["recentHarvestBoxesToday"] == 0


def test_delete_my_account(client, auth_headers):
    response = client.request(
        "DELETE",
        "/users/me",
        headers=auth_headers,
        json={"currentPassword": "password123"},
    )

    assert response.status_code == 200
    assert response.json()["message"] == "Cuenta eliminada exitosamente"

    profile_response = client.get("/users", headers=auth_headers)
    assert profile_response.status_code == 401


def test_delete_my_account_rejects_invalid_password(client, auth_headers):
    response = client.request(
        "DELETE",
        "/users/me",
        headers=auth_headers,
        json={"currentPassword": "wrongpass"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Current password is incorrect"


def test_account_deletion_page_available(client):
    response = client.get("/users/account-deletion")

    assert response.status_code == 200
    assert "Solicitud de eliminacion de cuenta" in response.text


def test_account_deletion_web_request(client, test_user):
    response = client.post(
        "/users/account-deletion",
        data={"email": test_user.email, "password": "password123"},
    )

    assert response.status_code == 200
    assert "Cuenta eliminada" in response.text

