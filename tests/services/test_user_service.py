import pytest
from app.services.user_service import UserService
from app.schemas.user import CreateUser
from app.models.user import User

def test_get_user(db, test_user):
    """Test getting a user by ID."""
    service = UserService(db)
    user = service.get_user(test_user.id)
    
    assert user is not None
    assert user.id == test_user.id
    assert user.email == test_user.email

def test_get_user_not_found(db):
    """Test getting a non-existent user."""
    service = UserService(db)
    user = service.get_user(999)
    
    assert user is None

def test_get_user_by_email(db, test_user):
    """Test getting a user by email."""
    service = UserService(db)
    user = service.get_user_by_email(test_user.email)
    
    assert user is not None
    assert user.email == test_user.email

def test_get_user_by_email_not_found(db):
    """Test getting a user by non-existent email."""
    service = UserService(db)
    user = service.get_user_by_email("nonexistent@example.com")
    
    assert user is None

def test_create_user(db):
    """Test creating a new user."""
    service = UserService(db)
    user_data = CreateUser(
        name="New",
        surname="User",
        email="newuser@example.com",
        password="hashedpassword"
    )
    
    user = service.create_user(user_data)
    
    assert user is not None
    assert user.email == "newuser@example.com"
    assert user.name == "New"

def test_create_user_duplicate_email(db, test_user):
    """Test creating a user with duplicate email."""
    service = UserService(db)
    user_data = CreateUser(
        name="Duplicate",
        surname="User",
        email=test_user.email,
        password="password"
    )
    
    user = service.create_user(user_data)
    
    assert user is None

def test_delete_user(db, test_user):
    """Test deleting a user."""
    service = UserService(db)
    result = service.delete_user(test_user.id)
    
    assert result is True
    deleted_user = service.get_user(test_user.id)
    assert deleted_user is None

def test_delete_user_not_found(db):
    """Test deleting a non-existent user."""
    service = UserService(db)
    result = service.delete_user(999)
    
    assert result is False

