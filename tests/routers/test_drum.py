import pytest
from decimal import Decimal

def test_create_drum(client, auth_headers, test_user):
    """Test creating a new drum."""
    response = client.post(
        "/drums",
        headers=auth_headers,
        json={
            "code": "TAMBOR-001",
            "tare": 15.5,
            "weight": 45.2
        }
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["code"] == "TAMBOR-001"
    # Decimals are serialized as strings in JSON
    assert float(data["tare"]) == 15.5
    assert float(data["weight"]) == 45.2
    assert data["userId"] == test_user.id
    assert data["sold"] is False

def test_create_drum_unauthorized(client):
    """Test creating a drum without authentication."""
    response = client.post(
        "/drums",
        json={
            "code": "TAMBOR-001",
            "tare": 15.5,
            "weight": 45.2
        }
    )
    
    assert response.status_code == 403

def test_create_drum_invalid_data(client, auth_headers):
    """Test creating a drum with invalid data."""
    # Missing required fields
    response = client.post(
        "/drums",
        headers=auth_headers,
        json={
            "code": "TAMBOR-001"
        }
    )
    
    assert response.status_code == 422

def test_get_drum(client, auth_headers, test_drum):
    """Test getting a drum by ID."""
    response = client.get(f"/drums/{test_drum.id}", headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == test_drum.id
    assert data["code"] == test_drum.code

def test_get_drum_not_found(client, auth_headers):
    """Test getting a non-existent drum."""
    response = client.get("/drums/999", headers=auth_headers)
    
    assert response.status_code == 404
    assert "no encontrado" in response.json()["detail"].lower()

def test_get_drum_unauthorized(client, test_drum):
    """Test getting a drum without authentication."""
    response = client.get(f"/drums/{test_drum.id}")
    
    assert response.status_code == 403

def test_get_drums(client, auth_headers, test_drum):
    """Test getting all drums for user."""
    response = client.get("/drums", headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert "pagination" in data
    assert len(data["data"]) > 0
    assert data["pagination"]["total"] > 0

def test_get_drums_with_pagination(client, auth_headers, test_user, db):
    """Test getting drums with pagination."""
    from app.services.drum_service import DrumService
    from app.schemas.drum import DrumCreate
    
    # Create multiple drums using test db session
    service = DrumService(db)
    for i in range(5):
        service.create_drum(test_user.id, DrumCreate(
            code=f"TAMBOR-{i:03d}",
            tare=Decimal("15.5"),
            weight=Decimal("45.2")
        ))
    
    response = client.get("/drums?page=1&limit=2", headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) == 2
    assert data["pagination"]["page"] == 1
    assert data["pagination"]["limit"] == 2

def test_get_drums_filtered_by_sold(client, auth_headers, test_user, db):
    """Test getting drums filtered by sold status."""
    from app.services.drum_service import DrumService
    from app.schemas.drum import DrumCreate
    
    # Create sold and unsold drums using test db session
    service = DrumService(db)
    
    drum1 = service.create_drum(test_user.id, DrumCreate(
        code="TAMBOR-SOLD",
        tare=Decimal("15.5"),
        weight=Decimal("45.2")
    ))
    service.mark_as_sold(drum1.id, test_user.id, True)
    
    service.create_drum(test_user.id, DrumCreate(
        code="TAMBOR-UNSOLD",
        tare=Decimal("15.5"),
        weight=Decimal("45.2")
    ))
    
    # Get only sold drums
    response = client.get("/drums?sold=true", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert all(d["sold"] is True for d in data["data"])

def test_update_drum(client, auth_headers, test_drum):
    """Test updating a drum."""
    response = client.put(
        f"/drums/{test_drum.id}",
        headers=auth_headers,
        json={
            "code": "TAMBOR-UPDATED",
            "tare": 16.0,
            "weight": 46.5
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["code"] == "TAMBOR-UPDATED"
    # Decimals are serialized as strings in JSON
    assert float(data["tare"]) == 16.0
    assert float(data["weight"]) == 46.5

def test_update_drum_partial(client, auth_headers, test_drum):
    """Test partial update of a drum."""
    original_code = test_drum.code
    
    response = client.put(
        f"/drums/{test_drum.id}",
        headers=auth_headers,
        json={
            "weight": 50.0
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["code"] == original_code  # Unchanged
    # Decimals are serialized as strings in JSON
    assert float(data["weight"]) == 50.0

def test_update_drum_not_found(client, auth_headers):
    """Test updating a non-existent drum."""
    response = client.put(
        "/drums/999",
        headers=auth_headers,
        json={
            "code": "NEW-CODE"
        }
    )
    
    assert response.status_code == 404

def test_mark_as_sold(client, auth_headers, test_drum):
    """Test marking a drum as sold."""
    response = client.patch(
        f"/drums/{test_drum.id}/sold",
        headers=auth_headers,
        json={"sold": True}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["sold"] is True

def test_mark_as_unsold(client, auth_headers, test_user, db):
    """Test marking a drum as unsold."""
    from app.services.drum_service import DrumService
    from app.schemas.drum import DrumCreate
    
    # Create a sold drum using test db session
    service = DrumService(db)
    drum = service.create_drum(test_user.id, DrumCreate(
        code="TAMBOR-SOLD",
        tare=Decimal("15.5"),
        weight=Decimal("45.2")
    ))
    service.mark_as_sold(drum.id, test_user.id, True)
    
    response = client.patch(
        f"/drums/{drum.id}/sold",
        headers=auth_headers,
        json={"sold": False}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["sold"] is False

def test_delete_drum(client, auth_headers, test_drum):
    """Test deleting a drum."""
    drum_id = test_drum.id
    
    response = client.delete(f"/drums/{drum_id}", headers=auth_headers)
    
    assert response.status_code == 200
    assert "eliminado" in response.json()["message"].lower()
    
    # Verify it's deleted
    get_response = client.get(f"/drums/{drum_id}", headers=auth_headers)
    assert get_response.status_code == 404

def test_delete_drum_not_found(client, auth_headers):
    """Test deleting a non-existent drum."""
    response = client.delete("/drums/999", headers=auth_headers)
    
    assert response.status_code == 404

def test_delete_all_drums(client, auth_headers, test_user, db):
    """Test deleting all drums for a user."""
    from app.services.drum_service import DrumService
    from app.schemas.drum import DrumCreate
    
    # Create multiple drums using test db session
    service = DrumService(db)
    for i in range(3):
        service.create_drum(test_user.id, DrumCreate(
            code=f"TAMBOR-{i:03d}",
            tare=Decimal("15.5"),
            weight=Decimal("45.2")
        ))
    
    response = client.delete("/drums", headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert data["deleted_count"] == 3
    
    # Verify all are deleted
    get_response = client.get("/drums", headers=auth_headers)
    assert get_response.status_code == 200
    assert get_response.json()["pagination"]["total"] == 0

def test_delete_all_drums_filtered(client, auth_headers, test_user, db):
    """Test deleting drums filtered by sold status."""
    from app.services.drum_service import DrumService
    from app.schemas.drum import DrumCreate
    
    # Create sold and unsold drums using test db session
    service = DrumService(db)
    
    drum1 = service.create_drum(test_user.id, DrumCreate(
        code="TAMBOR-SOLD",
        tare=Decimal("15.5"),
        weight=Decimal("45.2")
    ))
    service.mark_as_sold(drum1.id, test_user.id, True)
    
    drum2 = service.create_drum(test_user.id, DrumCreate(
        code="TAMBOR-UNSOLD",
        tare=Decimal("15.5"),
        weight=Decimal("45.2")
    ))
    
    # Delete only sold drums
    response = client.delete("/drums?sold=true", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["deleted_count"] == 1
    
    # Verify unsold drum still exists
    get_response = client.get(f"/drums/{drum2.id}", headers=auth_headers)
    assert get_response.status_code == 200

def test_get_stats(client, auth_headers, test_user, db):
    """Test getting statistics for drums."""
    from app.services.drum_service import DrumService
    from app.schemas.drum import DrumCreate
    
    # Create drums using test db session
    service = DrumService(db)
    
    service.create_drum(test_user.id, DrumCreate(
        code="TAMBOR-001",
        tare=Decimal("15.5"),
        weight=Decimal("45.2")
    ))
    
    drum2 = service.create_drum(test_user.id, DrumCreate(
        code="TAMBOR-002",
        tare=Decimal("18.3"),
        weight=Decimal("52.7")
    ))
    service.mark_as_sold(drum2.id, test_user.id, True)
    
    response = client.get("/drums/stats", headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert data["sold"] == 1
    assert data["not_sold"] == 1
    # Decimals are serialized as strings/numbers in JSON
    assert abs(float(data["total_tare"]) - 33.8) < 0.01
    assert abs(float(data["total_weight"]) - 97.9) < 0.01
    assert abs(float(data["net_weight"]) - 64.1) < 0.01

def test_get_stats_empty(client, auth_headers, test_user):
    """Test getting statistics when user has no drums."""
    # Delete any existing drums
    client.delete("/drums", headers=auth_headers)
    
    response = client.get("/drums/stats", headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0
    assert data["sold"] == 0
    assert data["not_sold"] == 0
    # Decimals are serialized as strings/numbers in JSON
    assert float(data["total_tare"]) == 0
    assert float(data["total_weight"]) == 0
    assert float(data["net_weight"]) == 0

