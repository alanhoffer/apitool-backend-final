from pydantic import ConfigDict, Field, field_validator
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
    jwt_expiration_days: int = Field(default=30, description="JWT expiration in days")

    # Password reset
    password_reset_enabled: bool = Field(
        default=False,
        description="Enable password reset endpoints only when a real delivery flow exists"
    )
    password_reset_token_ttl_minutes: int = Field(
        default=60,
        description="Password reset token expiration in minutes"
    )

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

    # Rate limiting
    rate_limit_enabled: bool = Field(default=True, description="Enable in-process rate limiting middleware")
    rate_limit_trust_proxy_headers: bool = Field(
        default=True,
        description="Trust proxy headers such as X-Forwarded-For to identify clients"
    )
    rate_limit_default_requests: int = Field(default=100, description="Default requests per window")
    rate_limit_default_window_seconds: int = Field(default=60, description="Default rate limit window in seconds")
    rate_limit_auth_requests: int = Field(default=10, description="Requests per auth prefix per window")
    rate_limit_auth_window_seconds: int = Field(default=60, description="Rate limit window for auth endpoints")
    rate_limit_login_requests: int = Field(default=5, description="Login requests per window")
    rate_limit_register_requests: int = Field(default=3, description="Register requests per window")
    rate_limit_forgot_password_requests: int = Field(default=3, description="Forgot password requests per window")

    model_config = ConfigDict(
        env_file=".env",
        extra="ignore"
    )

    @field_validator(
        "environment",
        "database_url",
        "db_host",
        "db_user",
        "db_password",
        "db_name",
        "weather_api_key",
        "jwt_secret",
        "jwt_algorithm",
        "cors_origins",
        "base_url",
        "openai_api_key",
        mode="before",
    )
    @classmethod
    def strip_string_fields(cls, value):
        if isinstance(value, str):
            return value.strip()
        return value

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
            return _normalize_database_url(postgres_url.strip())
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

if settings.environment in {"production", "staging"} and settings.cors_origins == "*":
    warnings.warn(
        "CORS_ORIGINS is set to '*' outside development/testing. Restrict it to known frontend origins.",
        UserWarning
    )

if settings.jwt_expiration_days > 90:
    warnings.warn(
        "JWT_EXPIRATION_DAYS is greater than 90 days. Consider reducing token lifetime for production.",
        UserWarning
    )
