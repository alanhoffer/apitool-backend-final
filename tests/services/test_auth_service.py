import pytest
from app.services.auth_service import AuthService
from app.schemas.user import CreateUser, LoginUser
from app.models.user import User

def test_hash_password(db):
    """Test password hashing."""
    service = AuthService(db)
    password = "testpassword123"
    hashed = service.hash_password(password)
    
    assert hashed != password
    assert len(hashed) > 0

def test_verify_password(db):
    """Test password verification."""
    service = AuthService(db)
    password = "testpassword123"
    hashed = service.hash_password(password)
    
    assert service.verify_password(password, hashed) is True
    assert service.verify_password("wrongpassword", hashed) is False

def test_create_access_token(db):
    """Test JWT token creation."""
    service = AuthService(db)
    data = {"sub": 1, "username": "test@example.com", "role": "apicultor"}
    token = service.create_access_token(data)
    
    assert token is not None
    assert isinstance(token, str)
    assert len(token) > 0

@pytest.mark.asyncio
async def test_sign_in_success(db, test_user):
    """Test successful sign in."""
    service = AuthService(db)
    login_data = LoginUser(
        email="test@example.com",
        password="password123"
    )
    
    result = await service.sign_in(login_data)
    
    assert result is not None
    assert result.user_id == test_user.id
    assert result.access_token is not None

@pytest.mark.asyncio
async def test_sign_in_wrong_password(db, test_user):
    """Test sign in with wrong password."""
    service = AuthService(db)
    login_data = LoginUser(
        email="test@example.com",
        password="wrongpassword"
    )
    
    with pytest.raises(Exception):
        await service.sign_in(login_data)

@pytest.mark.asyncio
async def test_sign_in_user_not_found(db):
    """Test sign in with non-existent user."""
    service = AuthService(db)
    login_data = LoginUser(
        email="nonexistent@example.com",
        password="password123"
    )
    
    with pytest.raises(Exception):
        await service.sign_in(login_data)

@pytest.mark.asyncio
async def test_sign_up_success(db):
    """Test successful sign up."""
    service = AuthService(db)
    signup_data = CreateUser(
        name="New",
        surname="User",
        email="newuser@example.com",
        password="password123"
    )
    
    result = await service.sign_up(signup_data)
    
    assert result is not None
    assert result.user_id is not None
    assert result.access_token is not None

@pytest.mark.asyncio
async def test_sign_up_duplicate_email(db, test_user):
    """Test sign up with duplicate email."""
    service = AuthService(db)
    signup_data = CreateUser(
        name="Duplicate",
        surname="User",
        email=test_user.email,
        password="password123"
    )
    
    with pytest.raises(Exception):
        await service.sign_up(signup_data)

