import pytest
import io

def test_get_apiary(client, auth_headers, test_apiary):
    """Test getting an apiary."""
    response = client.get(f"/apiarys/{test_apiary.id}", headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == test_apiary.id
    assert data["name"] == test_apiary.name

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

def test_create_apiary(client, auth_headers, test_user):
    """Test creating a new apiary."""
    # Create a real JPEG image for testing
    from PIL import Image
    img = Image.new('RGB', (100, 100), color='red')
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='JPEG')
    img_bytes.seek(0)
    
    response = client.post(
        "/apiarys",
        headers=auth_headers,
        data={
            "name": "New Apiary",
            "hives": "10",
            "status": "normal",
            "settings": '{"honey": true}'
        },
        files={"file": ("test.jpg", img_bytes, "image/jpeg")}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "New Apiary"
    assert data["hives"] == 10

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
            "status": "active"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["hives"] == 20
    assert data["status"] == "active"

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

def test_get_apiary_image(client, test_apiary):
    """Test getting apiary image."""
    response = client.get(f"/apiarys/profile/image/{test_apiary.image}")
    
    # Should return 404 if file doesn't exist, or 200 if it does
    assert response.status_code in [200, 404]

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
                "honey": False,
                "harvesting": True
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["honey"] is False
        assert data["harvesting"] is True

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

def test_set_harvesting_for_all(client, auth_headers, test_apiary):
    """Test setting harvesting status for all apiaries."""
    response = client.put(
        "/apiarys/harvest/all",
        headers=auth_headers,
        json={"harvesting": True}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "message" in data

def test_set_harvesting_for_all_unauthorized(client):
    """Test setting harvesting status without authentication."""
    response = client.put(
        "/apiarys/harvest/all",
        json={"harvesting": True}
    )
    
    assert response.status_code == 403

