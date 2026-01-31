import pytest

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

def test_profile_unauthorized(client):
    """Test getting profile without authentication."""
    response = client.get("/auth/profile")
    
    assert response.status_code == 403

def test_logout(client, auth_headers):
    """Test logout."""
    response = client.post("/auth/logout", headers=auth_headers)
    
    assert response.status_code == 200

