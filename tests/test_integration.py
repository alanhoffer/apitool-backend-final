import pytest

def test_full_user_flow(client):
    """Test complete user flow: register -> login -> get profile."""
    # Register
    register_response = client.post(
        "/auth/register",
        json={
            "name": "Integration",
            "surname": "Test",
            "email": "integration@test.com",
            "password": "password123"
        }
    )
    assert register_response.status_code == 200
    register_data = register_response.json()
    token = register_data["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Get profile
    profile_response = client.get("/auth/profile", headers=headers)
    assert profile_response.status_code == 200
    
    # Get user
    user_response = client.get("/users", headers=headers)
    assert user_response.status_code == 200
    assert user_response.json()["email"] == "integration@test.com"

def test_apiary_crud_flow(client, auth_headers, test_user):
    """Test complete CRUD flow for apiaries."""
    import io
    
    # Create
    file_content = b"fake image"
    file = io.BytesIO(file_content)
    
    create_response = client.post(
        "/apiarys",
        headers=auth_headers,
        data={
            "name": "CRUD Apiary",
            "hives": "15",
            "status": "normal",
            "settings": '{"honey": true, "levudex": true}'
        },
        files={"file": ("test.jpg", file, "image/jpeg")}
    )
    assert create_response.status_code == 200
    apiary_id = create_response.json()["id"]
    
    # Read
    get_response = client.get(f"/apiarys/{apiary_id}", headers=auth_headers)
    assert get_response.status_code == 200
    assert get_response.json()["name"] == "CRUD Apiary"
    
    # Update
    update_response = client.put(
        f"/apiarys/{apiary_id}",
        headers=auth_headers,
        data={
            "hives": "20",
            "status": "active"
        }
    )
    assert update_response.status_code == 200
    assert update_response.json()["hives"] == 20
    
    # Delete
    delete_response = client.delete(f"/apiarys/{apiary_id}", headers=auth_headers)
    assert delete_response.status_code == 200
    
    # Verify deleted
    verify_response = client.get(f"/apiarys/{apiary_id}", headers=auth_headers)
    assert verify_response.status_code == 404

def test_news_crud_flow(client, auth_headers):
    """Test complete CRUD flow for news."""
    # Create
    create_response = client.post(
        "/news",
        headers=auth_headers,
        json={
            "title": "Test News",
            "content": "Content here",
            "image": None
        }
    )
    assert create_response.status_code == 200
    news_id = create_response.json()["id"]
    
    # Read
    get_response = client.get(f"/news/{news_id}", headers=auth_headers)
    assert get_response.status_code == 200
    
    # Update
    update_response = client.put(
        f"/news/{news_id}",
        headers=auth_headers,
        json={
            "title": "Updated News"
        }
    )
    assert update_response.status_code == 200
    
    # Delete
    delete_response = client.delete(f"/news/{news_id}", headers=auth_headers)
    assert delete_response.status_code == 200

