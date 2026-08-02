"""Immutable package metadata model."""

from dataclasses import dataclass, field
from datetime import UTC, datetime


@dataclass(frozen=True, slots=True)
class PackageMetadata:
    """Descriptive and installation metadata for a platform package."""

    package_id: str
    name: str
    version: str
    category: str
    description: str
    author: str
    capabilities: tuple[str, ...] = ()
    dependencies: tuple[str, ...] = ()
    minimum_platform_version: str = "1.0.0"
    installed_at: datetime = field(
        default_factory=lambda: datetime.now(UTC)
    )
    verified: bool = True