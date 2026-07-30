from functools import lru_cache

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings loaded from environment only; secrets are not persisted."""

    model_config = SettingsConfigDict(env_file=None, extra="ignore")
    database_url: str = "sqlite:///./pipeline_guardian.db"
    airflow_base_url: str | None = None
    anthropic_api_key: SecretStr | None = Field(default=None, repr=False)
    anthropic_model: str | None = None
    verification_timeout_seconds: int = 300

    @field_validator("database_url")
    @classmethod
    def require_sqlite(cls, value: str) -> str:
        if not value.startswith("sqlite:///"):
            raise ValueError("DATABASE_URL must use a local sqlite:/// URL in v0.1")
        return value

    @field_validator("airflow_base_url")
    @classmethod
    def require_loopback_airflow(cls, value: str | None) -> str | None:
        if value is not None and not value.startswith(("http://127.0.0.1", "http://localhost")):
            raise ValueError("AIRFLOW_BASE_URL must be loopback-only in v0.1")
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()
