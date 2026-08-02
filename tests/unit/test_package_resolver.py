"""Package dependency resolver contract tests."""

import pytest

from qal_kernel.errors import (
    CircularDependencyError,
    MissingDependencyError,
    PackageNotFoundError,
)
from qal_kernel.packages.metadata import PackageMetadata
from qal_kernel.packages.package import Package
from qal_kernel.packages.registry import PackageRegistry
from qal_kernel.packages.resolver import PackageDependencyResolver


def _package(
    package_id: str,
    *,
    dependencies: tuple[str, ...] = (),
) -> Package:
    metadata = PackageMetadata(
        package_id=package_id,
        name=package_id,
        version="1.0.0",
        category="platform",
        description=f"Test package: {package_id}",
        author="Quanntiq",
        dependencies=dependencies,
    )
    return Package(metadata=metadata)


def test_resolve_returns_requested_package() -> None:
    registry = PackageRegistry()
    package = _package("quanntiq.analytics")
    registry.register(package)
    resolver = PackageDependencyResolver(registry)

    assert resolver.resolve("quanntiq.analytics") == (package,)


def test_resolve_orders_transitive_dependencies_first() -> None:
    registry = PackageRegistry()
    core = _package("quanntiq.core")
    services = _package(
        "quanntiq.services",
        dependencies=("quanntiq.core",),
    )
    workflows = _package(
        "quanntiq.workflows",
        dependencies=("quanntiq.services",),
    )
    registry.register(workflows)
    registry.register(core)
    registry.register(services)
    resolver = PackageDependencyResolver(registry)

    assert resolver.resolve("quanntiq.workflows") == (
        core,
        services,
        workflows,
    )


def test_resolve_orders_dependencies_deterministically() -> None:
    registry = PackageRegistry()
    alpha = _package("quanntiq.alpha")
    zeta = _package("quanntiq.zeta")
    application = _package(
        "quanntiq.application",
        dependencies=("quanntiq.zeta", "quanntiq.alpha"),
    )
    registry.register(zeta)
    registry.register(application)
    registry.register(alpha)
    resolver = PackageDependencyResolver(registry)

    assert resolver.resolve("quanntiq.application") == (
        alpha,
        zeta,
        application,
    )


def test_resolve_includes_shared_dependency_once() -> None:
    registry = PackageRegistry()
    core = _package("quanntiq.core")
    analytics = _package(
        "quanntiq.analytics",
        dependencies=("quanntiq.core",),
    )
    workflows = _package(
        "quanntiq.workflows",
        dependencies=("quanntiq.core",),
    )
    application = _package(
        "quanntiq.application",
        dependencies=("quanntiq.workflows", "quanntiq.analytics"),
    )
    for package in (application, workflows, analytics, core):
        registry.register(package)
    resolver = PackageDependencyResolver(registry)

    assert resolver.resolve("quanntiq.application") == (
        core,
        analytics,
        workflows,
        application,
    )


def test_resolve_rejects_missing_dependency() -> None:
    registry = PackageRegistry()
    package = _package(
        "quanntiq.analytics",
        dependencies=("quanntiq.missing",),
    )
    registry.register(package)
    resolver = PackageDependencyResolver(registry)

    with pytest.raises(
        MissingDependencyError,
        match=r"quanntiq\.analytics.*quanntiq\.missing",
    ):
        resolver.resolve("quanntiq.analytics")


def test_resolve_rejects_circular_dependency() -> None:
    registry = PackageRegistry()
    alpha = _package(
        "quanntiq.alpha",
        dependencies=("quanntiq.beta",),
    )
    beta = _package(
        "quanntiq.beta",
        dependencies=("quanntiq.alpha",),
    )
    registry.register(alpha)
    registry.register(beta)
    resolver = PackageDependencyResolver(registry)

    with pytest.raises(
        CircularDependencyError,
        match=(
            r"quanntiq\.alpha -> quanntiq\.beta -> "
            r"quanntiq\.alpha"
        ),
    ):
        resolver.resolve("quanntiq.alpha")


def test_resolve_rejects_unregistered_root_package() -> None:
    registry = PackageRegistry()
    resolver = PackageDependencyResolver(registry)

    with pytest.raises(
        PackageNotFoundError,
        match=r"quanntiq\.missing",
    ):
        resolver.resolve("quanntiq.missing")


def test_resolve_all_orders_complete_registry() -> None:
    registry = PackageRegistry()
    core = _package("quanntiq.core")
    analytics = _package(
        "quanntiq.analytics",
        dependencies=("quanntiq.core",),
    )
    workflows = _package("quanntiq.workflows")
    registry.register(workflows)
    registry.register(core)
    registry.register(analytics)
    resolver = PackageDependencyResolver(registry)

    assert resolver.resolve_all() == (
        core,
        analytics,
        workflows,
    )


def test_resolve_all_returns_empty_tuple_for_empty_registry() -> None:
    registry = PackageRegistry()
    resolver = PackageDependencyResolver(registry)

    assert resolver.resolve_all() == ()
