from fastapi import APIRouter, Query
from app.services.weather_service import WeatherService

router = APIRouter(prefix="/weather", tags=["weather"])

@router.get("")
async def get_weather(lat: float = Query(...), lon: float = Query(...)):
    weather_service = WeatherService()
    return await weather_service.get_weather(lat, lon)

