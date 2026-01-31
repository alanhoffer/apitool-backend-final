import pytest

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

