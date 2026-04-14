from pydantic import ConfigDict, Field
from pydantic_settings import BaseSettings
import os
import warnings


def _is_testing() -> bool:
    return os.getenv("TESTING") == "1"


def _environment_name() -> str:
    return os.getenv("APP_ENV") or os.getenv("ENVIRONMENT") or ("testing" if _is_testing() else "development")


def _normalize_database_url(url: str) -> str:
    if url.startswith("postgres://"):
        return "postgresql://" + url[len("postgres://"):]
    return url


class Settings(BaseSettings):
    environment: str = Field(default_factory=_environment_name, description="Current runtime environment")

    # Database
    database_url: str | None = Field(default=None, description="Full database connection URL")
    db_host: str = Field(default="localhost", description="Database host")
    db_port: int = Field(default=5432, description="Database port")
    db_user: str = Field(default="postgres", description="Database user")
    db_password: str = Field(default="change-me", description="Database password")
    db_name: str = Field(default="apitool1", description="Database name")

    # Weather API
    weather_api_key: str | None = Field(default=None, description="Weather API key")

    # JWT Configuration
    jwt_secret: str | None = Field(
        default=None,
        description="JWT secret key. Required outside testing unless you explicitly accept insecure development defaults."
    )
    jwt_algorithm: str = Field(default="HS256", description="JWT algorithm")
    jwt_expiration_days: int = Field(default=365, description="JWT expiration in days")

    # Bcrypt
    bcrypt_salt_rounds: int = Field(default=10, description="Bcrypt salt rounds")

    # CORS
    cors_origins: str = Field(
        default="*",
        description="CORS allowed origins (comma-separated, use * only for local development)"
    )

    # Base URL
    base_url: str = Field(
        default="http://localhost:3000/",
        description="Base URL for the application"
    )

    # IA / Audio
    openai_api_key: str | None = Field(default=None, description="OpenAI API key para transcripcion y chat")

    model_config = ConfigDict(
        env_file=".env",
        extra="ignore"
    )

    @property
    def cors_origins_list(self) -> list[str]:
        if self.cors_origins == "*":
            return ["*"]
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def is_testing(self) -> bool:
        return self.environment == "testing" or _is_testing()

    @property
    def is_development(self) -> bool:
        return self.environment == "development"

    @property
    def effective_database_url(self) -> str:
        if self.database_url:
            return _normalize_database_url(self.database_url)
        postgres_url = os.getenv("POSTGRES_URL")
        if postgres_url:
            return _normalize_database_url(postgres_url)
        return f"postgresql://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"

    @property
    def effective_jwt_secret(self) -> str:
        if self.jwt_secret:
            return self.jwt_secret
        if self.is_testing:
            return "test-only-jwt-secret"
        raise RuntimeError(
            "JWT_SECRET is required. Define it in the environment or .env before starting the API."
        )


settings = Settings()


if settings.db_password == "change-me" and not settings.is_testing and not settings.database_url and not os.getenv("POSTGRES_URL"):
    warnings.warn(
        "DB_PASSWORD is using the placeholder value 'change-me'. Configure real database credentials in .env.",
        UserWarning
    )

if settings.weather_api_key is None:
    warnings.warn(
        "WEATHER_API_KEY is not configured. /weather will fail until you define it in .env or the environment.",
        UserWarning
    )

if not settings.jwt_secret:
    if settings.is_testing:
        warnings.warn(
            "JWT_SECRET not set. Using a fixed testing secret because TESTING=1.",
            UserWarning
        )
    else:
        warnings.warn(
            "JWT_SECRET is not configured. The API will refuse to start auth-dependent paths until you define it.",
            UserWarning
        )
