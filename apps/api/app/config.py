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
    app_name: str = Field(default="x-to-demo API", description="Application name")
    app_version: str = Field(default="0.0.0", description="Application version")
    app_description: str = Field(
        default="Local x-to-demo API", description="Application description"
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

    # Logging
    log_level: str = Field(
        default="INFO",
        description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
    )

    # OpenAI / X-to-Demo pipeline
    openai_api_key: str | None = Field(
        default=None,
        description="OpenAI API key used for X-to-Demo LLM pipeline execution",
    )
    x_to_demo_model: str = Field(
        default="gpt-5.1",
        description=(
            "Default OpenAI model used for X-to-Demo pipeline phases "
            "(supported: gpt-5.2, gpt-5.1, gpt-5-mini, gpt-5-nano, gpt-4.1-nano)"
        ),
    )
    x_to_demo_output_dir: str = Field(
        default="artifacts/x-to-demo",
        description="Directory where generated X-to-Demo artifacts are saved",
    )
    x_to_demo_max_input_chars: int = Field(
        default=60000,
        description="Maximum allowed Input X length in characters",
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
