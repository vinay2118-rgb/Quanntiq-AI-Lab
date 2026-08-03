"""In-memory package registry."""

from qal_kernel.errors import (
    DuplicateRegistrationError,
    PackageNotFoundError,
)
from qal_kernel.packages.package import Package


class PackageRegistry:
    """Central inventory of registered packages."""

    def __init__(self) -> None:
        self._packages: dict[str, Package] = {}

    def register(self, package: Package) -> None:
        """Register a package without silently replacing an existing one."""
        package_id = package.metadata.package_id

        if package_id in self._packages:
            raise DuplicateRegistrationError(
                f"Package already registered: {package_id}"
            )

        self._packages[package_id] = package

    def unregister(self, package_id: str) -> Package:
        """Remove and return a registered package."""
        try:
            return self._packages.pop(package_id)
        except KeyError:
            raise PackageNotFoundError(
                f"Package not registered: {package_id}"
            ) from None

    def get(self, package_id: str) -> Package:
        """Return a registered package by identifier."""
        try:
            return self._packages[package_id]
        except KeyError:
            raise PackageNotFoundError(
                f"Package not registered: {package_id}"
            ) from None

    def contains(self, package_id: str) -> bool:
        """Return whether a package identifier is registered."""
        return package_id in self._packages

    def count(self) -> int:
        """Return the number of registered packages."""
        return len(self._packages)

    def all(self) -> tuple[Package, ...]:
        """Return all packages ordered by package identifier."""
        return tuple(
            self._packages[package_id]
            for package_id in sorted(self._packages)
        )