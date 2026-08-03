"""Package registry contract tests."""

import pytest

from qal_kernel.errors import (
    DuplicateRegistrationError,
    PackageNotFoundError,
)
from qal_kernel.packages.metadata import PackageMetadata
from qal_kernel.packages.package import Package
from qal_kernel.packages.registry import PackageRegistry


def _package(package_id: str) -> Package:
    metadata = PackageMetadata(
        package_id=package_id,
        name=package_id,
        version="1.0.0",
        category="platform",
        description=f"Test package: {package_id}",
        author="Quanntiq",
    )
    return Package(metadata=metadata)


def test_registry_registers_and_retrieves_package() -> None:
    registry = PackageRegistry()
    package = _package("quanntiq.analytics")

    registry.register(package)

    assert registry.get("quanntiq.analytics") is package
    assert registry.contains("quanntiq.analytics")
    assert registry.count() == 1


def test_registry_rejects_duplicate_package_id() -> None:
    registry = PackageRegistry()
    original = _package("quanntiq.analytics")
    duplicate = _package("quanntiq.analytics")
    registry.register(original)

    with pytest.raises(
        DuplicateRegistrationError,
        match=r"quanntiq\.analytics",
    ):
        registry.register(duplicate)

    assert registry.get("quanntiq.analytics") is original
    assert registry.count() == 1


def test_registry_get_rejects_missing_package() -> None:
    registry = PackageRegistry()

    with pytest.raises(
        PackageNotFoundError,
        match=r"quanntiq\.missing",
    ):
        registry.get("quanntiq.missing")


def test_registry_unregisters_and_returns_package() -> None:
    registry = PackageRegistry()
    package = _package("quanntiq.analytics")
    registry.register(package)

    removed = registry.unregister("quanntiq.analytics")

    assert removed is package
    assert not registry.contains("quanntiq.analytics")
    assert registry.count() == 0


def test_registry_unregister_rejects_missing_package() -> None:
    registry = PackageRegistry()

    with pytest.raises(
        PackageNotFoundError,
        match=r"quanntiq\.missing",
    ):
        registry.unregister("quanntiq.missing")


def test_registry_all_returns_packages_sorted_by_id() -> None:
    registry = PackageRegistry()
    analytics = _package("quanntiq.analytics")
    core = _package("quanntiq.core")
    workflows = _package("quanntiq.workflows")

    registry.register(workflows)
    registry.register(core)
    registry.register(analytics)

    assert registry.all() == (analytics, core, workflows)


def test_registry_starts_empty() -> None:
    registry = PackageRegistry()

    assert registry.count() == 0
    assert registry.all() == ()
    assert not registry.contains("quanntiq.analytics")