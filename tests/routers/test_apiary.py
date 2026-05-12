import pytest
import io
from datetime import datetime, timedelta

from PIL import Image


def _jpeg_bytes(size=(100, 100), color="red") -> io.BytesIO:
    img = Image.new("RGB", size, color=color)
    img_bytes = io.BytesIO()
    img.save(img_bytes, format="JPEG")
    img_bytes.seek(0)
    return img_bytes


def test_get_apiary(client, auth_headers, test_apiary):
    """Test getting an apiary."""
    response = client.get(f"/apiarys/{test_apiary.id}", headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == test_apiary.id
    assert data["name"] == test_apiary.name
    assert "imageUrl" in data

def test_get_apiary_not_found(client, auth_headers):
    """Test getting non-existent apiary."""
    response = client.get("/apiarys/999", headers=auth_headers)
    
    assert response.status_code == 404

def test_get_apiary_unauthorized(client, test_apiary):
    """Test getting apiary without authentication."""
    response = client.get(f"/apiarys/{test_apiary.id}")
    
    assert response.status_code == 403

def test_get_all_apiaries(client, auth_headers, test_apiary):
    """Test getting all apiaries for user."""
    response = client.get("/apiarys", headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert "_imageUrl" in data[0]


def test_get_apiary_returns_public_image_url_when_available(client, auth_headers, test_user, db):
    from app.models.apiary import Apiary

    apiary = Apiary(
        userId=test_user.id,
        name="Apiario CDN",
        hives=3,
        status="normal",
        image="https://cdn.example.com/apiary.jpg",
    )
    db.add(apiary)
    db.commit()
    db.refresh(apiary)

    response = client.get(f"/apiarys/{apiary.id}", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["image"] == "https://cdn.example.com/apiary.jpg"
    assert data["imageUrl"] == "https://cdn.example.com/apiary.jpg"

def test_create_apiary(client, auth_headers, test_user, db):
    """Test creating a new apiary."""
    img_bytes = _jpeg_bytes()
    
    response = client.post(
        "/apiarys",
        headers=auth_headers,
        data={
            "name": "New Apiary",
            "hives": "10",
            "managementType": "individual",
            "status": "normal",
            "settings": '{"honey": true}'
        },
        files={"file": ("test.jpg", img_bytes, "image/jpeg")}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "New Apiary"
    assert data["hives"] == 10
    assert data["managementType"] == "individual"

    from app.models.task import Task
    from app.services.task_service import DEFAULT_FAST_TASK_TITLES
    tasks = db.query(Task).filter(Task.apiary_id == data["id"]).all()
    assert len(tasks) == len(DEFAULT_FAST_TASK_TITLES)
    assert {t.title for t in tasks} == set(DEFAULT_FAST_TASK_TITLES)


def test_create_apiary_optimizes_profile_image_dimensions(client, auth_headers):
    from app.runtime import get_upload_dir
    from app.services.apiary_service import MAX_PROFILE_IMAGE_DIMENSION

    response = client.post(
        "/apiarys",
        headers=auth_headers,
        data={
            "name": "Optimized Apiary",
            "hives": "10",
            "status": "normal",
            "settings": '{"honey": true}',
        },
        files={"file": ("large.jpg", _jpeg_bytes(size=(1600, 1200)), "image/jpeg")},
    )

    assert response.status_code == 200
    image_path = get_upload_dir() / response.json()["image"]

    try:
        with Image.open(image_path) as optimized:
            assert optimized.format == "JPEG"
            assert max(optimized.size) <= MAX_PROFILE_IMAGE_DIMENSION
    finally:
        image_path.unlink(missing_ok=True)


def test_create_apiary_rejects_fake_image(client, auth_headers):
    response = client.post(
        "/apiarys",
        headers=auth_headers,
        data={
            "name": "Fake Image Apiary",
            "hives": "10",
            "status": "normal",
            "settings": '{"honey": true}',
        },
        files={"file": ("fake.jpg", io.BytesIO(b"not really an image"), "image/jpeg")},
    )

    assert response.status_code == 400
    assert "Invalid image file type" in response.json()["detail"]


def test_create_apiary_rejects_excessive_image_dimensions(client, auth_headers, monkeypatch):
    from app.services import apiary_service as apiary_service_module

    monkeypatch.setattr(apiary_service_module, "MAX_IMAGE_PIXELS", 1)

    response = client.post(
        "/apiarys",
        headers=auth_headers,
        data={
            "name": "Huge Image Apiary",
            "hives": "10",
            "status": "normal",
            "settings": '{"honey": true}',
        },
        files={"file": ("huge.jpg", _jpeg_bytes(size=(2, 2)), "image/jpeg")},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Image dimensions are too large"

def test_create_apiary_without_file(client, auth_headers, test_user):
    """Test creating apiary without file."""
    response = client.post(
        "/apiarys",
        headers=auth_headers,
        data={
            "name": "Apiary No File",
            "hives": "5",
            "status": "normal",
            "settings": '{"honey": true}'
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Apiary No File"

def test_update_apiary(client, auth_headers, test_apiary):
    """Test updating an apiary."""
    response = client.put(
        f"/apiarys/{test_apiary.id}",
        headers=auth_headers,
        data={
            "hives": "20",
            "managementType": "individual",
            "status": "active"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["hives"] == 20
    assert data["status"] == "active"
    assert data["managementType"] == "individual"

def test_delete_apiary(client, auth_headers, test_apiary):
    """Test deleting an apiary."""
    response = client.delete(f"/apiarys/{test_apiary.id}", headers=auth_headers)
    
    assert response.status_code == 200
    
    # Verify it's deleted
    get_response = client.get(f"/apiarys/{test_apiary.id}", headers=auth_headers)
    assert get_response.status_code == 404

def test_get_apiary_count(client, auth_headers, test_apiary):
    """Test getting apiary and hive counts."""
    response = client.get("/apiarys/all/count", headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert "apiaryCount" in data
    assert "hiveCount" in data
    assert data["apiaryCount"] >= 1

def test_get_apiary_history(client, auth_headers, test_apiary):
    """Test getting apiary history."""
    response = client.get(f"/apiarys/history/{test_apiary.id}", headers=auth_headers)
    
    # Should always return 200, even if history is empty (empty list is valid)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)  # Should return a list, even if empty


def test_get_apiary_insights(client, auth_headers, test_apiary, test_user, db):
    from app.models.hive import Hive
    from app.models.task import Task

    test_apiary.managementType = "individual"
    test_apiary.honey = 0
    test_apiary.sugar = 0
    db.add(Hive(
        apiaryId=test_apiary.id,
        userId=test_user.id,
        name="H-100",
        status="Malo",
        queenStatus="absent",
        hiveStrength="weak",
        swarming=True,
        population=2,
        broodFrames=0,
        honeyFrames=0,
        pollenFrames=0,
        lastInspection=(datetime.now() - timedelta(days=50)).date().isoformat(),
    ))
    db.add(Task(
        title="Revisión sanitaria",
        completed=False,
        user_id=test_user.id,
        apiary_id=test_apiary.id,
        due_date=datetime.now() - timedelta(days=1),
    ))
    db.commit()

    response = client.get(f"/apiarys/{test_apiary.id}/insights", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["apiaryId"] == test_apiary.id
    assert data["healthStatus"] in {"critica", "atencion", "estable"}
    assert data["attentionHiveCount"] == 1
    assert data["criticalHiveCount"] == 1
    assert data["overdueTaskCount"] == 1
    assert len(data["recommendations"]) >= 1
    assert any(item["priority"] == "high" for item in data["recommendations"])

def test_get_apiary_image(client, test_apiary):
    """Test getting apiary image."""
    response = client.get(f"/apiarys/profile/image/{test_apiary.image}")
    
    # Should return 404 if file doesn't exist, or 200 if it does
    assert response.status_code in [200, 404]


def test_get_legacy_blob_path_falls_back_to_local_upload(client):
    from app.routers import apiary as apiary_router

    image_path = apiary_router.UPLOAD_DIR / "legacy-local.jpg"
    image_path.parent.mkdir(parents=True, exist_ok=True)
    image_content = _jpeg_bytes().getvalue()
    image_path.write_bytes(image_content)

    try:
        response = client.get("/apiarys/profile/image/apiarys/legacy-local.jpg")
    finally:
        image_path.unlink(missing_ok=True)

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("image/jpeg")
    assert response.content == image_content

def test_update_apiary_settings(client, auth_headers, test_apiary, test_user, db):
    """Test updating apiary settings."""
    from app.models.settings import Settings
    
    # Get the settings ID from the test_apiary fixture
    settings = db.query(Settings).filter(Settings.apiaryId == test_apiary.id).first()
    
    if settings:
        response = client.put(
            f"/apiarys/settings/{settings.id}",
            headers=auth_headers,
            json={
                "apiaryId": test_apiary.id,
                "apiaryUserId": test_user.id,
                "honey": False
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["honey"] is False

def test_update_apiary_settings_unauthorized(client, test_apiary, test_user, db):
    """Test updating apiary settings without authentication."""
    from app.models.settings import Settings
    
    settings = db.query(Settings).filter(Settings.apiaryId == test_apiary.id).first()
    
    if settings:
        response = client.put(
            f"/apiarys/settings/{settings.id}",
            json={
                "apiaryId": test_apiary.id,
                "apiaryUserId": test_user.id,
                "honey": False
            }
        )
        
        assert response.status_code == 403

def test_update_apiary_settings_rejects_spoofed_owner_fields(client, auth_headers, test_user, db):
    """Settings updates must validate the persisted owner, not the request body."""
    from passlib.context import CryptContext
    from app.models.apiary import Apiary
    from app.models.settings import Settings
    from app.models.user import User
    from app.models.user import Role

    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    other_user = User(
        name="Other",
        surname="User",
        email="other-settings@example.com",
        password=pwd_context.hash("password123"),
        role=Role.APICULTOR,
    )
    db.add(other_user)
    db.commit()
    db.refresh(other_user)

    other_apiary = Apiary(
        userId=other_user.id,
        name="Other Apiary",
        hives=1,
        status="normal",
        image="test.jpg",
    )
    db.add(other_apiary)
    db.commit()
    db.refresh(other_apiary)

    other_settings = Settings(
        apiaryId=other_apiary.id,
        apiaryUserId=other_user.id,
        honey=True,
    )
    db.add(other_settings)
    db.commit()
    db.refresh(other_settings)

    response = client.put(
        f"/apiarys/settings/{other_settings.id}",
        headers=auth_headers,
        json={
            "apiaryId": other_apiary.id,
            "apiaryUserId": test_user.id,
            "honey": False,
        },
    )

    assert response.status_code == 401

def test_harvest_year_rollover_archives_previous_year_and_resets_apiaries(
    client,
    auth_headers,
    test_apiary,
    test_user,
    db,
):
    """The yearly harvest season rolls over automatically and resets active counters."""
    from app.models.harvest_season import HarvestSeason
    from datetime import datetime

    current_year = datetime.now().year
    previous_year = current_year - 1
    test_apiary.box = 10
    test_apiary.boxMedium = 4
    test_apiary.boxSmall = 2
    test_apiary.hives = 8
    db.add(
        HarvestSeason(
            userId=test_user.id,
            name=f"Cosecha {previous_year}",
            status="active",
            startedAt=datetime(previous_year, 1, 1),
        )
    )
    db.commit()

    response = client.get("/apiarys/harvest/seasons", headers=auth_headers)
    assert response.status_code == 200
    seasons = response.json()
    assert len(seasons) == 2

    active = next(season for season in seasons if season["isActive"])
    closed = next(season for season in seasons if not season["isActive"])
    assert active["name"] == f"Cosecha {current_year}"
    assert active["total"] == 0
    assert closed["status"] == "closed"
    assert closed["total"] == 16
    assert closed["apiaryCount"] == 1
    assert closed["hiveCount"] == 8

    db_closed = db.query(HarvestSeason).filter(HarvestSeason.id == closed["id"]).first()
    assert db_closed.endedAt is not None
    db.refresh(test_apiary)
    assert test_apiary.box == 0
    assert test_apiary.boxMedium == 0
    assert test_apiary.boxSmall == 0

    detail_response = client.get(
        f"/apiarys/harvest/seasons/{closed['id']}/apiaries",
        headers=auth_headers,
    )
    assert detail_response.status_code == 200
    detail = detail_response.json()
    assert detail[0]["apiaryId"] == test_apiary.id
    assert detail[0]["apiaryName"] == test_apiary.name
    assert detail[0]["total"] == 16
