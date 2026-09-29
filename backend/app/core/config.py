from functools import lru_cache
from typing import Annotated, Literal

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings, loaded from environment variables (and `.env` in development)."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "What Would You Do? API"
    environment: Literal["development", "test", "production"] = "development"

    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/wwyd"

    # NoDecode: read the raw env string ourselves instead of expecting JSON.
    cors_origins: Annotated[list[str], NoDecode] = ["http://localhost:3000"]

    # Auth. No default on purpose: the app refuses to start without a real secret,
    # so a forgotten env var can never silently fall back to a guessable key.
    # SecretStr keeps the value out of logs and reprs.
    jwt_secret: SecretStr = Field(min_length=32)
    # Login lasts 7 days. We have no refresh-token flow in the MVP, so a short
    # lifetime would log players out constantly. The trade-off: a stolen token
    # stays valid until it expires.
    access_token_expire_minutes: int = Field(default=60 * 24 * 7, ge=1)

    # Brute-force protection: attempts per IP per minute on login and register.
    rate_limit_enabled: bool = True
    auth_rate_limit_per_minute: int = Field(default=10, ge=1)

    # Game rules
    round_length: int = Field(default=10, ge=3, le=20)
    min_stats_sample: int = Field(default=20, ge=1)

    @property
    def cookie_secure(self) -> bool:
        """Browsers only send `Secure` cookies over HTTPS, so switch it on in production only."""
        return self.environment == "production"

    @field_validator("database_url")
    @classmethod
    def use_psycopg_driver(cls, value: str) -> str:
        """Hosts like Neon hand out `postgresql://...`; SQLAlchemy needs the driver named."""
        for prefix in ("postgres://", "postgresql://"):
            if value.startswith(prefix):
                return "postgresql+psycopg://" + value.removeprefix(prefix)
        return value

    @field_validator("cors_origins", mode="before")
    @classmethod
    def split_origins(cls, value: object) -> object:
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()
