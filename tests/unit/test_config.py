from typing import Literal

import pytest
from pydantic import PostgresDsn, ValidationError

from qal_kernel.config import Settings


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
