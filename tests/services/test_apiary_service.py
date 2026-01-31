import pytest
from decimal import Decimal
from app.services.apiary_service import ApiaryService
from app.schemas.apiary import CreateApiary, UpdateApiary
from app.models.apiary import Apiary

def test_get_apiary(db, test_apiary):
    """Test getting an apiary by ID."""
    service = ApiaryService(db)
    apiary = service.get_apiary(test_apiary.id)
    
    assert apiary is not None
    assert apiary.id == test_apiary.id
    assert apiary.name == test_apiary.name

def test_get_apiary_not_found(db):
    """Test getting a non-existent apiary."""
    service = ApiaryService(db)
    apiary = service.get_apiary(999)
    
    assert apiary is None

def test_get_all_by_user_id(db, test_user, test_apiary):
    """Test getting all apiaries for a user."""
    service = ApiaryService(db)
    apiaries = service.get_all_by_user_id(test_user.id)
    
    assert len(apiaries) > 0
    # In Pydantic v2, access private attributes using getattr or model_dump with include
    apiary_data = apiaries[0].model_dump(include={"_id"})
    assert apiary_data["_id"] == test_apiary.id

def test_create_apiary(db, test_user):
    """Test creating a new apiary."""
    service = ApiaryService(db)
    apiary_data = CreateApiary(
        name="New Apiary",
        hives=10,
        status="normal",
        settings='{"honey": true, "levudex": true}'
    )
    
    apiary = service.create_apiary(test_user.id, apiary_data)
    
    assert apiary is not None
    assert apiary.name == "New Apiary"
    assert apiary.hives == 10
    assert apiary.userId == test_user.id

def test_update_apiary(db, test_apiary):
    """Test updating an apiary."""
    service = ApiaryService(db)
    update_data = UpdateApiary(
        hives=15,
        status="active"
    )
    
    updated = service.update_apiary(test_apiary.id, update_data)
    
    assert updated is not None
    assert updated.hives == 15
    assert updated.status == "active"

def test_delete_apiary(db, test_apiary):
    """Test deleting an apiary."""
    service = ApiaryService(db)
    result = service.delete_apiary(test_apiary.id)
    
    assert result is True
    deleted = service.get_apiary(test_apiary.id)
    assert deleted is None

def test_count_apiaries_by_user_id(db, test_user, test_apiary):
    """Test counting apiaries for a user."""
    service = ApiaryService(db)
    count = service.count_apiaries_by_user_id(test_user.id)
    
    assert count >= 1

def test_count_hives_by_user_id(db, test_user, test_apiary):
    """Test counting hives for a user."""
    service = ApiaryService(db)
    count = service.count_hives_by_user_id(test_user.id)
    
    assert count >= test_apiary.hives

