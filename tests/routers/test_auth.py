import pytest

from app.models.user import Role
from app.services.auth_service import AuthService

def test_register_success(client):
    """Test successful user registration."""
    response = client.post(
        "/auth/register",
        json={
            "name": "New",
            "surname": "User",
            "email": "newuser@example.com",
            "password": "password123"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "user_id" in data

def test_register_duplicate_email(client, test_user):
    """Test registration with duplicate email."""
    response = client.post(
        "/auth/register",
        json={
            "name": "Duplicate",
            "surname": "User",
            "email": test_user.email,
            "password": "password123"
        }
    )
    
    assert response.status_code == 409

def test_login_success(client, test_user):
    """Test successful login."""
    response = client.post(
        "/auth/login",
        json={
            "email": test_user.email,
            "password": "password123"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "user_id" in data

def test_login_wrong_password(client, test_user):
    """Test login with wrong password."""
    response = client.post(
        "/auth/login",
        json={
            "email": test_user.email,
            "password": "wrongpassword"
        }
    )
    
    assert response.status_code == 401

def test_login_user_not_found(client):
    """Test login with non-existent user."""
    response = client.post(
        "/auth/login",
        json={
            "email": "nonexistent@example.com",
            "password": "password123"
        }
    )
    
    assert response.status_code == 401

def test_profile(client, auth_headers):
    """Test getting user profile."""
    response = client.get("/auth/profile", headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert "sub" in data
    assert "username" in data
    assert "role" in data

def test_profile_revalidates_current_role_from_db(client, auth_headers, test_user, db):
    """Profile should reflect the latest role stored in DB."""
    test_user.role = Role.APICULTOR_PREMIUM
    db.commit()
    db.refresh(test_user)

    response = client.get("/auth/profile", headers=auth_headers)

    assert response.status_code == 200
    assert response.json()["role"] == Role.APICULTOR_PREMIUM.value

def test_profile_rejects_old_token_after_password_change(client, auth_headers, test_user, db):
    """Changing the password should invalidate existing JWTs with password fingerprint."""
    auth_service = AuthService(db)
    test_user.password = auth_service.hash_password("newpassword123")
    db.commit()
    db.refresh(test_user)

    response = client.get("/auth/profile", headers=auth_headers)

    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials"

def test_profile_unauthorized(client):
    """Test getting profile without authentication."""
    response = client.get("/auth/profile")
    
    assert response.status_code == 403

def test_logout(client, auth_headers):
    """Test logout."""
    response = client.post("/auth/logout", headers=auth_headers)
    
    assert response.status_code == 200

def test_forgot_password_disabled(client, test_user):
    """Password reset endpoints should be disabled until configured."""
    response = client.post(
        "/auth/forgot-password",
        json={"email": test_user.email}
    )

    assert response.status_code == 503
    assert response.json()["detail"] == "Password reset is not available"

def test_reset_password_disabled(client):
    """Password reset completion should be disabled until configured."""
    response = client.post(
        "/auth/reset-password",
        json={"token": "invalid-token", "newPassword": "newpassword123"}
    )

    assert response.status_code == 503
    assert response.json()["detail"] == "Password reset is not available"

