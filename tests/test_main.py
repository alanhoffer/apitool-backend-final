import pytest

def test_root_endpoint(client):
    """Test root endpoint."""
    response = client.get("/")
    
    assert response.status_code == 200
    assert response.json() == {"message": "UnAuthorized"}

def test_openapi_docs(client):
    """Test OpenAPI documentation endpoint."""
    response = client.get("/docs")
    
    assert response.status_code == 200

def test_openapi_json(client):
    """Test OpenAPI JSON schema."""
    response = client.get("/openapi.json")
    
    assert response.status_code == 200
    data = response.json()
    assert "openapi" in data
    assert "info" in data
    assert "paths" in data

