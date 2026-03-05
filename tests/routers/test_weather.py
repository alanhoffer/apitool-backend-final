from unittest.mock import Mock, patch, AsyncMock

def test_get_weather_success(client):
    """Test getting weather information."""
    mock_weather_data = {
        "location": {"name": "Test City"},
        "current": {"temp_c": 20, "condition": {"text": "Sunny"}}
    }
    
    with patch("app.services.weather_service.settings.weather_api_key", "test-weather-key"), \
         patch("app.services.weather_service.httpx.AsyncClient") as mock_client:
        mock_response = Mock()
        mock_response.json.return_value = mock_weather_data
        mock_response.raise_for_status = Mock()
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
        
        response = client.get("/weather?lat=40.7128&lon=-74.0060")
        
        assert response.status_code == 200
        assert response.json() == mock_weather_data

def test_get_weather_missing_params(client):
    """Test getting weather without parameters."""
    response = client.get("/weather")
    
    assert response.status_code == 422  # Validation error

