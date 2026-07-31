from pathlib import Path
from typing import Literal

import pytest
from pydantic import PostgresDsn, ValidationError

from qal_kernel.config import Settings


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


@pytest.mark.parametrize("environment", ["staging", "production"])
def test_settings_reject_placeholder_database_credentials(
    environment: Literal["staging", "production"],
) -> None:
    with pytest.raises(ValidationError):
        Settings(
            environment=environment,
            database_url=PostgresDsn(
                "postgresql+asyncpg://qal:change-me@localhost:5432/qal"
            ),
        )
