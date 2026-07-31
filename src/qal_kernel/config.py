"""Validated, environment-backed application configuration."""

from functools import lru_cache
from typing import Literal, Self

from pydantic import Field, PostgresDsn, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Immutable runtime configuration loaded from QAL-prefixed variables."""

    model_config = SettingsConfigDict(
        env_prefix="QAL_", env_file=".env", extra="ignore", frozen=True
    )

    environment: Literal["development", "testing", "staging", "production"] = "development"
    service_name: str = "qal-platform-kernel"
    service_version: str = "0.1.0"
    # Container networking requires an all-interface bind; exposure is controlled at ingress.
    host: str = "0.0.0.0"  # noqa: S104  # nosec B104
    port: int = Field(default=8080, ge=1, le=65535)
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    database_url: PostgresDsn = PostgresDsn(
        "postgresql+asyncpg://qal:change-me@localhost:5432/qal"
    )

    @model_validator(mode="after")
    def reject_placeholder_database_credentials(self) -> Self:
        """Reject placeholder database credentials in deployment profiles."""

        if self.environment not in {"staging", "production"}:
            return self

        for host in self.database_url.hosts():
            database_password = host["password"]
            if database_password is not None and database_password.casefold() == "change-me":
                raise ValueError(
                    "Placeholder database credentials are forbidden in staging and production"
                )

        return self


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the process-wide validated settings object."""

    return Settings()
