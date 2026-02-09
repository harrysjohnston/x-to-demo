"""Application settings and configuration."""

import json

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def parse_cors_origins(value: str | list[str] | None) -> list[str]:
    """Parse CORS origins from string (comma-separated or JSON) or list."""
    if isinstance(value, list):
        return value
    if not value:
        return ["http://localhost:3000"]
    # Try JSON first
    try:
        parsed = json.loads(value)
        if isinstance(parsed, list):
            return parsed
    except (json.JSONDecodeError, TypeError):
        pass
    # Fall back to comma-separated
    return [origin.strip() for origin in value.split(",") if origin.strip()]


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application metadata
    app_name: str = Field(default="fullstack-template API", description="Application name")
    app_version: str = Field(default="0.0.0", description="Application version")
    app_description: str = Field(
        default="FastAPI + SQLModel API scaffold for the fullstack template",
        description="Application description",
    )
    environment: str = Field(
        default="development",
        description="Environment (development, staging, production)",
    )

    # API server settings
    api_host: str = Field(default="0.0.0.0", description="API server host")
    api_port: int = Field(default=8000, description="API server port")

    # CORS settings
    cors_origins: str | list[str] = Field(
        default="http://localhost:3000",
        description="Allowed CORS origins (comma-separated string or JSON array)",
    )

    @field_validator("cors_origins", mode="before")
    @classmethod
    def validate_cors_origins(cls, value: str | list[str] | None) -> list[str]:
        """Parse CORS origins from various formats."""
        return parse_cors_origins(value)

    # JWT settings
    jwt_secret: str = Field(
        default="dev-change-me",
        description="JWT signing secret (MUST be changed in production)",
    )
    jwt_issuer: str = Field(
        default="fullstack-template",
        description="JWT issuer claim",
    )
    jwt_audience: str = Field(
        default="fullstack-template",
        description="JWT audience claim",
    )
    jwt_algorithm: str = Field(default="HS256", description="JWT signing algorithm")
    jwt_access_token_expire_minutes: int = Field(
        default=30,
        description="JWT access token expiration in minutes",
    )
    jwt_refresh_token_expire_days: int = Field(
        default=7,
        description="JWT refresh token expiration in days",
    )

    # Database settings
    database_url: str | None = Field(
        default=None,
        description="PostgreSQL database URL (overrides individual postgres_* settings)",
    )
    postgres_user: str = Field(default="app", description="PostgreSQL user")
    postgres_password: str = Field(default="app", description="PostgreSQL password")
    postgres_db: str = Field(default="app", description="PostgreSQL database name")
    postgres_host: str = Field(default="localhost", description="PostgreSQL host")
    postgres_port: int = Field(default=5432, description="PostgreSQL port")

    def get_database_url(self) -> str:
        """Get database URL from settings or construct from components."""
        if self.database_url:
            return self.database_url
        return f"postgresql+psycopg://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"

    # Logging
    log_level: str = Field(
        default="INFO",
        description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
    )

    # Email (dev sink)
    email_enabled: bool = Field(
        default=True,
        description="Enable email rendering and dev delivery",
    )
    email_from_address: str = Field(
        default="no-reply@local",
        description="Default from address for emails",
    )
    email_from_name: str = Field(
        default="Fullstack Template",
        description="Default from name for emails",
    )
    email_web_base_url: str = Field(
        default="http://localhost:3000",
        description="Base URL for frontend links in emails",
    )
    email_support_address: str = Field(
        default="support@local",
        description="Support contact for customer emails",
    )
    email_log_payload: bool = Field(
        default=True,
        description="Log rendered email content to the console sink",
    )

    # Storage settings
    storage_provider: str = Field(
        default="s3",
        description="Storage provider (s3 | gcs | azure)",
    )
    s3_bucket: str = Field(default="", description="S3 bucket name")
    s3_region: str = Field(default="us-east-1", description="S3 region")
    s3_endpoint_url: str | None = Field(
        default=None,
        description="S3 endpoint URL (for MinIO: http://localhost:9000)",
    )
    s3_access_key_id: str | None = Field(
        default=None,
        description="S3 access key ID",
    )
    s3_secret_access_key: str | None = Field(
        default=None,
        description="S3 secret access key",
    )
    upload_max_size_bytes: int = Field(
        default=10 * 1024 * 1024,
        description="Maximum upload size in bytes (default: 10 MB)",
    )
    upload_url_expires_seconds: int = Field(
        default=900,
        description="Presigned URL expiration time in seconds (default: 15 minutes)",
    )

    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment.lower() == "development"

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment.lower() == "production"

    @property
    def openapi_url(self) -> str | None:
        """OpenAPI docs URL (disabled in production)."""
        return None if self.is_production else "/openapi.json"

    @property
    def docs_url(self) -> str | None:
        """Swagger UI docs URL (disabled in production)."""
        return None if self.is_production else "/docs"

    @property
    def redoc_url(self) -> str | None:
        """ReDoc docs URL (disabled in production)."""
        return None if self.is_production else "/redoc"


# Global settings instance
settings = Settings()
