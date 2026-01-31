import pytest
from decimal import Decimal
from app.services.drum_service import DrumService
from app.schemas.drum import DrumCreate, DrumUpdate
from app.models.drum import Drum

def test_create_drum(db, test_user):
    """Test creating a new drum."""
    service = DrumService(db)
    drum_data = DrumCreate(
        code="TAMBOR-001",
        tare=Decimal("15.5"),
        weight=Decimal("45.2")
    )
    
    drum = service.create_drum(test_user.id, drum_data)
    
    assert drum is not None
    assert drum.code == "TAMBOR-001"
    assert drum.tare == Decimal("15.5")
    assert drum.weight == Decimal("45.2")
    assert drum.userId == test_user.id
    assert drum.sold is False

def test_get_drum_by_id(db, test_user, test_drum):
    """Test getting a drum by ID."""
    service = DrumService(db)
    drum = service.get_drum_by_id(test_drum.id, test_user.id)
    
    assert drum is not None
    assert drum.id == test_drum.id
    assert drum.code == test_drum.code

def test_get_drum_by_id_not_found(db, test_user):
    """Test getting a non-existent drum."""
    service = DrumService(db)
    drum = service.get_drum_by_id(999, test_user.id)
    
    assert drum is None

def test_get_drum_wrong_user(db, test_user, test_drum):
    """Test getting a drum that belongs to another user."""
    # Create another user
    from passlib.context import CryptContext
    from app.models.user import User, Role
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    other_user = User(
        name="Other",
        surname="User",
        email="other@example.com",
        password=pwd_context.hash("password123"),
        role=Role.USER
    )
    db.add(other_user)
    db.commit()
    db.refresh(other_user)
    
    service = DrumService(db)
    drum = service.get_drum_by_id(test_drum.id, other_user.id)
    
    assert drum is None

def test_get_drums(db, test_user, test_drum):
    """Test getting all drums for a user."""
    service = DrumService(db)
    drums, total = service.get_drums(test_user.id)
    
    assert len(drums) > 0
    assert total > 0
    assert drums[0].id == test_drum.id

def test_get_drums_with_pagination(db, test_user):
    """Test getting drums with pagination."""
    service = DrumService(db)
    
    # Create multiple drums
    for i in range(5):
        drum_data = DrumCreate(
            code=f"TAMBOR-{i:03d}",
            tare=Decimal("15.5"),
            weight=Decimal("45.2")
        )
        service.create_drum(test_user.id, drum_data)
    
    drums, total = service.get_drums(test_user.id, page=1, limit=2)
    
    assert len(drums) == 2
    assert total == 5

def test_get_drums_filtered_by_sold(db, test_user):
    """Test getting drums filtered by sold status."""
    service = DrumService(db)
    
    # Create sold and unsold drums
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
    
    # Get only sold drums
    sold_drums, sold_total = service.get_drums(test_user.id, sold=True)
    assert sold_total == 1
    assert sold_drums[0].sold is True
    
    # Get only unsold drums
    unsold_drums, unsold_total = service.get_drums(test_user.id, sold=False)
    assert unsold_total >= 1
    assert all(d.sold is False for d in unsold_drums)

def test_update_drum(db, test_user, test_drum):
    """Test updating a drum."""
    service = DrumService(db)
    updates = DrumUpdate(
        code="TAMBOR-UPDATED",
        tare=Decimal("16.0"),
        weight=Decimal("46.5")
    )
    
    updated_drum = service.update_drum(test_drum.id, test_user.id, updates)
    
    assert updated_drum is not None
    assert updated_drum.code == "TAMBOR-UPDATED"
    assert updated_drum.tare == Decimal("16.0")
    assert updated_drum.weight == Decimal("46.5")

def test_update_drum_partial(db, test_user, test_drum):
    """Test partial update of a drum."""
    service = DrumService(db)
    original_code = test_drum.code
    updates = DrumUpdate(weight=Decimal("50.0"))
    
    updated_drum = service.update_drum(test_drum.id, test_user.id, updates)
    
    assert updated_drum is not None
    assert updated_drum.code == original_code  # Unchanged
    assert updated_drum.weight == Decimal("50.0")

def test_update_drum_not_found(db, test_user):
    """Test updating a non-existent drum."""
    service = DrumService(db)
    updates = DrumUpdate(code="NEW-CODE")
    
    result = service.update_drum(999, test_user.id, updates)
    
    assert result is None

def test_mark_as_sold(db, test_user, test_drum):
    """Test marking a drum as sold."""
    service = DrumService(db)
    
    updated_drum = service.mark_as_sold(test_drum.id, test_user.id, True)
    
    assert updated_drum is not None
    assert updated_drum.sold is True

def test_mark_as_unsold(db, test_user):
    """Test marking a drum as unsold."""
    service = DrumService(db)
    
    # Create a sold drum
    drum = service.create_drum(test_user.id, DrumCreate(
        code="TAMBOR-SOLD",
        tare=Decimal("15.5"),
        weight=Decimal("45.2")
    ))
    service.mark_as_sold(drum.id, test_user.id, True)
    
    # Mark as unsold
    updated_drum = service.mark_as_sold(drum.id, test_user.id, False)
    
    assert updated_drum is not None
    assert updated_drum.sold is False

def test_delete_drum(db, test_user, test_drum):
    """Test deleting a drum."""
    service = DrumService(db)
    drum_id = test_drum.id
    
    result = service.delete_drum(drum_id, test_user.id)
    
    assert result is True
    
    # Verify it's deleted
    deleted_drum = service.get_drum_by_id(drum_id, test_user.id)
    assert deleted_drum is None

def test_delete_drum_not_found(db, test_user):
    """Test deleting a non-existent drum."""
    service = DrumService(db)
    
    result = service.delete_drum(999, test_user.id)
    
    assert result is False

def test_delete_all_drums(db, test_user):
    """Test deleting all drums for a user."""
    service = DrumService(db)
    
    # Create multiple drums
    for i in range(3):
        service.create_drum(test_user.id, DrumCreate(
            code=f"TAMBOR-{i:03d}",
            tare=Decimal("15.5"),
            weight=Decimal("45.2")
        ))
    
    deleted_count = service.delete_all_drums(test_user.id)
    
    assert deleted_count == 3
    
    # Verify all are deleted
    drums, total = service.get_drums(test_user.id)
    assert total == 0

def test_delete_all_drums_filtered(db, test_user):
    """Test deleting drums filtered by sold status."""
    service = DrumService(db)
    
    # Create sold and unsold drums
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
    deleted_count = service.delete_all_drums(test_user.id, sold=True)
    assert deleted_count == 1
    
    # Verify unsold drum still exists
    remaining_drum = service.get_drum_by_id(drum2.id, test_user.id)
    assert remaining_drum is not None

def test_get_stats(db, test_user):
    """Test getting statistics for drums."""
    service = DrumService(db)
    
    # Create drums with different weights
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
    
    stats = service.get_stats(test_user.id)
    
    assert stats["total"] == 2
    assert stats["sold"] == 1
    assert stats["not_sold"] == 1
    assert stats["total_tare"] == Decimal("33.8")  # 15.5 + 18.3
    assert stats["total_weight"] == Decimal("97.9")  # 45.2 + 52.7
    # Allow for floating point precision
    assert abs(float(stats["net_weight"]) - 64.1) < 0.01  # 97.9 - 33.8

def test_get_stats_empty(db, test_user):
    """Test getting statistics when user has no drums."""
    service = DrumService(db)
    
    stats = service.get_stats(test_user.id)
    
    assert stats["total"] == 0
    assert stats["sold"] == 0
    assert stats["not_sold"] == 0
    assert stats["total_tare"] == Decimal("0")
    assert stats["total_weight"] == Decimal("0")
    assert stats["net_weight"] == Decimal("0")

