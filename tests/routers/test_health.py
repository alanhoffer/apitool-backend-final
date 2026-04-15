from fastapi.testclient import TestClient

from app.database import get_db
from app.main import app


class FailingDB:
    def execute(self, *_args, **_kwargs):
        raise RuntimeError("db-down")


def test_readiness_check_returns_503_without_internal_error():
    def override_get_db():
        yield FailingDB()

    app.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(app) as client:
            response = client.get("/health/ready")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 503
    assert response.json() == {
        "status": "not_ready",
        "database": "disconnected",
    }
