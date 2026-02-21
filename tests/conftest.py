import pytest
import os
os.environ["TESTING"] = "1"  # Set testing mode before imports

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient
from app.database import Base, get_db
from app.main import app
from app.models import User, Apiary, Settings, History, News, Drum
from app.models.user import Role

# Use in-memory SQLite for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db():
    """Create a fresh database for each test."""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def client(db):
    """Create a test client with database override."""
    def override_get_db():
        try:
            yield db
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

@pytest.fixture
def test_user(db):
    """Create a test user."""
    from passlib.context import CryptContext
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    user = User(
        name="Test",
        surname="User",
        email="test@example.com",
        password=pwd_context.hash("password123"),
        role=Role.APICULTOR
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@pytest.fixture
def test_admin(db):
    """Create a test admin user."""
    from passlib.context import CryptContext
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    admin = User(
        name="Admin",
        surname="User",
        email="admin@example.com",
        password=pwd_context.hash("password123"),
        role=Role.ADMIN
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)
    return admin

@pytest.fixture
def auth_headers(client, test_user):
    """Get authentication headers for test user."""
    response = client.post(
        "/auth/login",
        json={"email": "test@example.com", "password": "password123"}
    )
    assert response.status_code == 200, f"Login failed: {response.status_code} - {response.text}"
    data = response.json()
    assert "access_token" in data, f"Missing access_token in response: {data}"
    token = data["access_token"]
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def admin_headers(client, test_admin):
    """Get authentication headers for admin user."""
    response = client.post(
        "/auth/login",
        json={"email": "admin@example.com", "password": "password123"}
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def test_apiary(db, test_user):
    """Create a test apiary."""
    apiary = Apiary(
        userId=test_user.id,
        name="Test Apiary",
        hives=5,
        status="normal",
        image="test.jpg"
    )
    db.add(apiary)
    db.commit()
    db.refresh(apiary)
    
    settings = Settings(
        apiaryId=apiary.id,
        apiaryUserId=test_user.id,
        honey=True,
        levudex=True
    )
    db.add(settings)
    db.commit()
    
    return apiary

@pytest.fixture
def test_drum(db, test_user):
    """Create a test drum."""
    from decimal import Decimal
    drum = Drum(
        userId=test_user.id,
        code="TAMBOR-001",
        tare=Decimal("15.5"),
        weight=Decimal("45.2"),
        sold=False
    )
    db.add(drum)
    db.commit()
    db.refresh(drum)
    return drum

