import httpx
from fastapi import HTTPException, status
from app.config import settings
from app.utils.cache import cached

class WeatherService:
    def __init__(self):
        self.api_key = settings.weather_api_key
    
    @cached(ttl=600, key_prefix="weather")  # Cache por 10 minutos
    async def get_weather(self, lat: float, lon: float):
        if not self.api_key:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Weather service is not configured"
            )

        url = f"http://api.weatherapi.com/v1/current.json?key={self.api_key}&q={lat},{lon}&aqi=no"
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url)
                response.raise_for_status()
                return response.json()
        except httpx.TimeoutException:
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail="Weather service timeout"
            )
        except httpx.HTTPError as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Weather service error: {str(exc)}"
            )
