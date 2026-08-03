"""Immutable author-declared package manifest."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PackageManifest:
    """Installation contract declared by a package author."""

    package_id: str
    name: str
    version: str
    category: str
    description: str
    author: str
    entry_point: str
    capabilities: tuple[str, ...] = ()
    dependencies: tuple[str, ...] = ()
    minimum_platform_version: str = "1.0.0"