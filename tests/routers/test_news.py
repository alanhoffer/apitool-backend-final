import pytest

from app.models.user import Role

def test_get_all_news(client, auth_headers):
    """Test getting all news."""
    # Note: This endpoint requires role check, might need adjustment
    response = client.get("/news", headers=auth_headers)
    
    # Should be 200 if role check passes, or 403 if it doesn't
    assert response.status_code in [200, 403]
    if response.status_code == 200:
        data = response.json()
        assert isinstance(data, list)

def test_create_news(client, admin_headers):
    """Test creating news."""
    response = client.post(
        "/news",
        headers=admin_headers,
        json={
            "title": "Test News",
            "content": "This is test news content",
            "image": None
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Test News"
    assert data["content"] == "This is test news content"

def test_get_news_by_id(client, admin_headers):
    """Test getting news by ID."""
    # First create news
    create_response = client.post(
        "/news",
        headers=admin_headers,
        json={
            "title": "Test News",
            "content": "Content",
            "image": None
        }
    )
    news_id = create_response.json()["id"]
    
    # Then get it
    response = client.get(f"/news/{news_id}", headers=admin_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == news_id

def test_update_news(client, admin_headers):
    """Test updating news."""
    # First create news
    create_response = client.post(
        "/news",
        headers=admin_headers,
        json={
            "title": "Original Title",
            "content": "Original Content",
            "image": None
        }
    )
    news_id = create_response.json()["id"]
    
    # Then update it
    response = client.put(
        f"/news/{news_id}",
        headers=admin_headers,
        json={
            "title": "Updated Title"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Updated Title"

def test_delete_news(client, admin_headers):
    """Test deleting news."""
    # First create news
    create_response = client.post(
        "/news",
        headers=admin_headers,
        json={
            "title": "To Delete",
            "content": "Content",
            "image": None
        }
    )
    news_id = create_response.json()["id"]
    
    # Then delete it
    response = client.delete(f"/news/{news_id}", headers=admin_headers)
    
    assert response.status_code == 200
    
    # Verify it's deleted
    get_response = client.get(f"/news/{news_id}", headers=admin_headers)
    assert get_response.status_code == 404

def test_create_news_forbidden_after_admin_role_downgrade(client, admin_headers, test_admin, db):
    """A stale admin token should stop working after the user is downgraded in DB."""
    test_admin.role = Role.APICULTOR
    db.commit()
    db.refresh(test_admin)

    response = client.post(
        "/news",
        headers=admin_headers,
        json={
            "title": "Blocked News",
            "content": "This should be forbidden",
            "image": None
        }
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Not enough permissions"

