from pydantic_settings import BaseSettings
from pydantic import ConfigDict

class Settings(BaseSettings):
    # Database
    db_host: str = "192.168.1.139"
    db_port: int = 5432
    db_user: str = "bija"
    db_password: str = "15441109Gordo."
    db_name: str = "apitool1"
    
    # Weather API
    weather_api_key: str = "3389c5ddfc124bf4a1c00055242909"
    
    # Configuración de Pydantic v2 para ignorar campos extra
    model_config = ConfigDict(
        env_file=".env",
        extra="ignore"  # Ignora campos extra en lugar de lanzar error
    )

settings = Settings()

