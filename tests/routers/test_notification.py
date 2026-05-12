import pytest
from app.models.notification import Notification


def test_get_notifications_empty(client, auth_headers):
    """Returns empty list when no notifications exist."""
    response = client.get("/notifications", headers=auth_headers)
    assert response.status_code == 200
    assert response.json() == []


def test_get_notifications_unauthorized(client):
    """Requires authentication."""
    response = client.get("/notifications")
    assert response.status_code == 403


def test_notification_data_field_is_null_by_default(client, auth_headers, test_user, db):
    """Notification created without push_data has data=None."""
    notif = Notification(
        userId=test_user.id,
        title="Sin datos",
        message="Notificacion sin contexto",
        type="INFO",
        data=None,
    )
    db.add(notif)
    db.commit()

    response = client.get("/notifications", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["data"] is None


def test_notification_data_field_with_apiary_context(client, auth_headers, test_user, db):
    """Notification stores and returns apiaryId in data field."""
    notif = Notification(
        userId=test_user.id,
        title="Apiario sin visitar",
        message="Hace 30 dias que no registras actividad.",
        type="ALERT",
        data={"apiaryId": 42},
    )
    db.add(notif)
    db.commit()

    response = client.get("/notifications", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["data"] == {"apiaryId": 42}
    assert data[0]["type"] == "ALERT"


def test_notification_data_field_with_hive_context(client, auth_headers, test_user, db):
    """Notification stores and returns hiveId + apiaryId in data field."""
    notif = Notification(
        userId=test_user.id,
        title="Alerta de colmena",
        message="Revisar colmena 7.",
        type="WARNING",
        data={"apiaryId": 1, "hiveId": 7},
    )
    db.add(notif)
    db.commit()

    response = client.get("/notifications", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data[0]["data"]["hiveId"] == 7
    assert data[0]["data"]["apiaryId"] == 1


def test_notification_data_field_with_task_context(client, auth_headers, test_user, db):
    """Notification stores and returns taskId in data field."""
    notif = Notification(
        userId=test_user.id,
        title="Tarea vencida",
        message="Tienes una tarea pendiente.",
        type="INFO",
        data={"taskId": 99},
    )
    db.add(notif)
    db.commit()

    response = client.get("/notifications", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data[0]["data"] == {"taskId": 99}


def test_mark_notification_as_read(client, auth_headers, test_user, db):
    """Mark a notification as read."""
    notif = Notification(
        userId=test_user.id,
        title="Test",
        message="Mensaje",
        type="INFO",
        data=None,
    )
    db.add(notif)
    db.commit()
    db.refresh(notif)

    response = client.put(f"/notifications/{notif.id}/read", headers=auth_headers)
    assert response.status_code == 200

    # Verify it is now marked as read
    list_response = client.get("/notifications", headers=auth_headers)
    assert list_response.json()[0]["isRead"] is True


def test_get_notification_summary(client, auth_headers, test_user, db):
    db.add_all([
        Notification(
            userId=test_user.id,
            title="No leida",
            message="Pendiente",
            type="INFO",
            isRead=False,
        ),
        Notification(
            userId=test_user.id,
            title="Leida",
            message="Vista",
            type="INFO",
            isRead=True,
        ),
    ])
    db.commit()

    response = client.get("/notifications/summary", headers=auth_headers)

    assert response.status_code == 200
    assert response.json() == {"totalCount": 2, "unreadCount": 1}


def test_mark_all_notifications_as_read(client, auth_headers, test_user, db):
    db.add_all([
        Notification(
            userId=test_user.id,
            title="N1",
            message="M1",
            type="INFO",
            isRead=False,
        ),
        Notification(
            userId=test_user.id,
            title="N2",
            message="M2",
            type="WARNING",
            isRead=False,
        ),
    ])
    db.commit()

    response = client.put("/notifications/read-all", headers=auth_headers)

    assert response.status_code == 200
    assert response.json() == {"markedCount": 2}

    summary_response = client.get("/notifications/summary", headers=auth_headers)
    assert summary_response.json() == {"totalCount": 2, "unreadCount": 0}


def test_mark_notification_read_unauthorized(client, test_user, db):
    """Cannot mark notification as read without auth."""
    notif = Notification(
        userId=test_user.id,
        title="Test",
        message="Mensaje",
        type="INFO",
    )
    db.add(notif)
    db.commit()
    db.refresh(notif)

    response = client.put(f"/notifications/{notif.id}/read")
    assert response.status_code == 403


def test_notifications_only_own_user(client, auth_headers, test_user, test_admin, db):
    """User only sees their own notifications."""
    # Notification for test_user
    notif_user = Notification(
        userId=test_user.id,
        title="Para usuario",
        message="Solo tuya",
        type="INFO",
    )
    # Notification for admin (should not appear for test_user)
    notif_admin = Notification(
        userId=test_admin.id,
        title="Para admin",
        message="Solo del admin",
        type="INFO",
    )
    db.add_all([notif_user, notif_admin])
    db.commit()

    response = client.get("/notifications", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["title"] == "Para usuario"
