from pathlib import Path
from typing import Literal

import pytest
from pydantic import PostgresDsn, ValidationError

from qal_kernel.config import Settings, get_settings, redact_database_url


def test_settings_load_defaults(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.chdir(tmp_path)
    for variable in (
        "QAL_ENVIRONMENT",
        "QAL_SERVICE_NAME",
        "QAL_SERVICE_VERSION",
        "QAL_HOST",
        "QAL_PORT",
        "QAL_LOG_LEVEL",
        "QAL_DATABASE_URL",
    ):
        monkeypatch.delenv(variable, raising=False)

    settings = Settings()

    assert settings.environment == "development"
    assert settings.service_name == "qal-platform-kernel"
    assert settings.port == 8080
    assert settings.log_level == "INFO"


def test_settings_load_qal_environment_variables(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("QAL_ENVIRONMENT", "testing")
    monkeypatch.setenv("QAL_PORT", "9091")
    monkeypatch.setenv("QAL_LOG_LEVEL", "DEBUG")

    settings = Settings()

    assert settings.environment == "testing"
    assert settings.port == 9091
    assert settings.log_level == "DEBUG"


def test_explicit_values_override_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("QAL_PORT", "9091")

    settings = Settings(port=9092)

    assert settings.port == 9092


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("port", 0),
        ("port", 65_536),
        ("environment", "invalid"),
        ("log_level", "TRACE"),
        ("database_url", "not-a-postgres-url"),
    ],
)
def test_settings_reject_invalid_values(field: str, value: object) -> None:
    with pytest.raises(ValidationError):
        Settings.model_validate({field: value})


@pytest.mark.parametrize("environment", ["staging", "production"])
def test_settings_reject_placeholder_database_credentials(
    environment: Literal["staging", "production"],
) -> None:
    with pytest.raises(ValidationError):
        Settings(
            environment=environment,
            database_url=PostgresDsn("postgresql+asyncpg://qal:change-me@localhost:5432/qal"),
        )


def test_redact_database_url_masks_password() -> None:
    database_url = PostgresDsn("postgresql+asyncpg://qal:secret-pass@localhost:5432/qal")

    redacted = redact_database_url(database_url)

    assert "secret-pass" not in redacted
    assert "qal:***@localhost:5432/qal" in redacted


def test_settings_repr_and_str_redact_database_credentials() -> None:
    settings = Settings(
        database_url=PostgresDsn("postgresql+asyncpg://qal:secret-pass@localhost:5432/qal"),
    )

    for representation in (repr(settings), str(settings)):
        assert "secret-pass" not in representation
        assert "***" in representation


def test_settings_diagnostics_redact_database_credentials() -> None:
    settings = Settings(
        database_url=PostgresDsn("postgresql+asyncpg://qal:secret-pass@localhost:5432/qal"),
    )

    snapshot = settings.diagnostics()

    assert snapshot["database_url"] == "postgresql+asyncpg://qal:***@localhost:5432/qal"
    assert "secret-pass" not in str(snapshot)


def test_settings_are_immutable() -> None:
    settings = Settings()

    with pytest.raises(ValidationError):
        settings.port = 9090


def test_get_settings_returns_cached_instance(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.chdir(tmp_path)
    get_settings.cache_clear()

    first = get_settings()
    second = get_settings()

    assert first is second
