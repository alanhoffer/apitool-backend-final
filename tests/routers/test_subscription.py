from datetime import datetime, timedelta

import pytest

import app.routers.subscription as subscription_router
from app.models.subscription import Subscription


@pytest.fixture(autouse=True)
def clear_processed_revenuecat_events():
    subscription_router._PROCESSED_REVENUECAT_EVENTS.clear()
    yield
    subscription_router._PROCESSED_REVENUECAT_EVENTS.clear()


def _build_webhook_event(**overrides):
    now = datetime.utcnow()
    event = {
        "id": "evt_123",
        "type": "INITIAL_PURCHASE",
        "app_user_id": "anonymous-user",
        "original_app_user_id": "anonymous-user",
        "aliases": [],
        "product_id": "monthly",
        "event_timestamp_ms": int(now.timestamp() * 1000),
        "expiration_at_ms": int((now + timedelta(days=30)).timestamp() * 1000),
    }
    event.update(overrides)
    return {"event": event}


def test_revenuecat_webhook_fails_closed_without_secret(client, test_user, monkeypatch):
    monkeypatch.delenv("REVENUECAT_WEBHOOK_SECRET", raising=False)

    response = client.post(
        "/subscription/webhook",
        json=_build_webhook_event(aliases=[str(test_user.id)]),
    )

    assert response.status_code == 503
    assert response.json()["detail"] == "Webhook secret not configured"


def test_revenuecat_webhook_rejects_invalid_secret(client, test_user, monkeypatch):
    monkeypatch.setenv("REVENUECAT_WEBHOOK_SECRET", "expected-secret")

    response = client.post(
        "/subscription/webhook",
        json=_build_webhook_event(aliases=[str(test_user.id)]),
        headers={"Authorization": "wrong-secret"},
    )

    assert response.status_code == 401


def test_revenuecat_webhook_uses_alias_user_id_and_stores_customer_id(client, db, test_user, monkeypatch):
    monkeypatch.setenv("REVENUECAT_WEBHOOK_SECRET", "expected-secret")

    response = client.post(
        "/subscription/webhook",
        json=_build_webhook_event(
            app_user_id="$RCAnonymousID:abc123",
            original_app_user_id="$RCAnonymousID:abc123",
            aliases=[str(test_user.id)],
            product_id="monthly:baseplan",
        ),
        headers={"Authorization": "expected-secret"},
    )

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

    subscription = db.query(Subscription).filter(Subscription.userId == test_user.id).first()
    assert subscription is not None
    assert subscription.tier == "maestro"
    assert subscription.status == "active"
    assert subscription.revenuecatCustomerId == "$RCAnonymousID:abc123"


def test_revenuecat_webhook_ignores_duplicate_event_id(client, test_user, monkeypatch):
    monkeypatch.setenv("REVENUECAT_WEBHOOK_SECRET", "expected-secret")
    payload = _build_webhook_event(
        app_user_id=str(test_user.id),
        original_app_user_id=str(test_user.id),
        aliases=[str(test_user.id)],
    )

    first_response = client.post(
        "/subscription/webhook",
        json=payload,
        headers={"Authorization": "expected-secret"},
    )
    second_response = client.post(
        "/subscription/webhook",
        json=payload,
        headers={"Authorization": "expected-secret"},
    )

    assert first_response.status_code == 200
    assert second_response.status_code == 200
    assert second_response.json() == {"status": "ignored", "reason": "duplicate_event"}


def test_subscription_me_does_not_report_expired_premium(client, db, test_user, auth_headers):
    db.add(
        Subscription(
            userId=test_user.id,
            tier="maestro",
            status="active",
            expiresAt=datetime.utcnow() - timedelta(days=1),
        )
    )
    db.commit()

    response = client.get("/subscription/me", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["tier"] == "aprendiz"
    assert data["status"] == "expired"
    assert data["aiAccess"] is False
