"""Validated, environment-backed application configuration."""

from functools import lru_cache
from typing import Any, Literal, Self
from urllib.parse import urlparse, urlunparse

from pydantic import Field, PostgresDsn, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_REDACTED_CREDENTIAL = "***"


def redact_database_url(url: PostgresDsn) -> str:
    """Return a database URL with its password redacted."""

    parsed = urlparse(str(url))
    if parsed.password is None:
        return str(url)

    redacted_netloc = parsed.netloc.replace(
        f":{parsed.password}@",
        f":{_REDACTED_CREDENTIAL}@",
        1,
    )
    return urlunparse(parsed._replace(netloc=redacted_netloc))


class Settings(BaseSettings):
    """Immutable runtime configuration loaded from QAL-prefixed variables."""

    model_config = SettingsConfigDict(
        env_prefix="QAL_",
        env_file=".env",
        extra="ignore",
        frozen=True,
    )

    environment: Literal[
        "development",
        "testing",
        "staging",
        "production",
    ] = "development"
    service_name: str = "qal-platform-kernel"
    service_version: str = "0.1.0"
    host: str = "0.0.0.0"  # noqa: S104  # nosec B104
    port: int = Field(default=8080, ge=1, le=65535)
    log_level: Literal[
        "DEBUG",
        "INFO",
        "WARNING",
        "ERROR",
        "CRITICAL",
    ] = "INFO"
    database_url: PostgresDsn = PostgresDsn("postgresql+asyncpg://qal:change-me@localhost:5432/qal")

    @model_validator(mode="after")
    def reject_placeholder_database_credentials(self) -> Self:
        """Reject placeholder credentials in deployment profiles."""

        if self.environment not in {"staging", "production"}:
            return self

        for host in self.database_url.hosts():
            database_password = host["password"]
            if database_password is not None and database_password.casefold() == "change-me":
                raise ValueError(
                    "Placeholder database credentials are forbidden in staging and production"
                )

        return self

    def diagnostics(self) -> dict[str, Any]:
        """Return a secret-safe configuration snapshot."""

        return {
            "environment": self.environment,
            "service_name": self.service_name,
            "service_version": self.service_version,
            "host": self.host,
            "port": self.port,
            "log_level": self.log_level,
            "database_url": redact_database_url(self.database_url),
        }

    def __repr__(self) -> str:
        return (
            f"Settings(environment={self.environment!r}, "
            f"service_name={self.service_name!r}, "
            f"service_version={self.service_version!r}, "
            f"host={self.host!r}, "
            f"port={self.port}, "
            f"log_level={self.log_level!r}, "
            f"database_url={redact_database_url(self.database_url)!r})"
        )

    def __str__(self) -> str:
        return self.__repr__()


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the process-wide validated settings object."""

    return Settings()
