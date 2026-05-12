import pytest


@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("get", "/cache/stats"),
        ("delete", "/cache"),
        ("post", "/cache/cleanup"),
    ],
)
def test_cache_endpoints_require_admin(client, auth_headers, method, path):
    """Regular authenticated users should not manage cache endpoints."""
    response = getattr(client, method)(path, headers=auth_headers)

    assert response.status_code == 403
    assert response.json()["detail"] == "Not enough permissions"


@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("get", "/cache/stats"),
        ("delete", "/cache"),
        ("post", "/cache/cleanup"),
    ],
)
def test_cache_endpoints_allow_admin(client, admin_headers, method, path):
    """Admin users should retain access to cache endpoints."""
    response = getattr(client, method)(path, headers=admin_headers)

    assert response.status_code == 200
