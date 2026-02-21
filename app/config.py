from pydantic_settings import BaseSettings
from pydantic import ConfigDict, Field
import os
import secrets

class Settings(BaseSettings):
    # Database
    db_host: str = Field(default="192.168.1.139", description="Database host")
    db_port: int = Field(default=5432, description="Database port")
    db_user: str = Field(default="bija", description="Database user")
    db_password: str = Field(default="15441109Gordo.", description="Database password")
    db_name: str = Field(default="apitool1", description="Database name")
    
    # Weather API
    weather_api_key: str = Field(default="3389c5ddfc124bf4a1c00055242909", description="Weather API key")
    
    # JWT Configuration
    jwt_secret: str = Field(
        default_factory=lambda: os.getenv("JWT_SECRET") or secrets.token_urlsafe(32),
        description="JWT secret key (should be set via JWT_SECRET env var)"
    )
    jwt_algorithm: str = Field(default="HS256", description="JWT algorithm")
    jwt_expiration_days: int = Field(default=365, description="JWT expiration in days")
    
    # Bcrypt
    bcrypt_salt_rounds: int = Field(default=10, description="Bcrypt salt rounds")
    
    # CORS
    cors_origins: str = Field(
        default="*",
        description="CORS allowed origins (comma-separated, use * for all)"
    )
    
    # Base URL
    base_url: str = Field(
        default="http://apitoolbackend.ddns.net:5173/",
        description="Base URL for the application"
    )

    # IA / Audio (opcional): si no se define, el endpoint /api/audio responde con mensaje informativo
    openai_api_key: str | None = Field(default=None, description="OpenAI API key para transcripción (Whisper) y chat")

    # Configuración de Pydantic v2 para ignorar campos extra
    model_config = ConfigDict(
        env_file=".env",
        extra="ignore"  # Ignora campos extra en lugar de lanzar error
    )
    
    @property
    def cors_origins_list(self) -> list[str]:
        """Parse CORS origins string into list."""
        if self.cors_origins == "*":
            return ["*"]
        return [origin.strip() for origin in self.cors_origins.split(",")]

settings = Settings()

# Warn if using default JWT_SECRET (security risk)
if not os.getenv("JWT_SECRET"):
    import warnings
    warnings.warn(
        "JWT_SECRET not set in environment. Using auto-generated secret. "
        "Set JWT_SECRET in .env file for production!",
        UserWarning
    )

