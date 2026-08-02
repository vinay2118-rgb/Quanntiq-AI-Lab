"""Package lifecycle manager contract tests."""

from dataclasses import replace

import pytest

from qal_kernel.errors import InvalidLifecycleTransitionError
from qal_kernel.packages.loader import PackageLoader
from qal_kernel.packages.manager import PackageManager
from qal_kernel.packages.manifest import PackageManifest
from qal_kernel.packages.package import PackageState
from qal_kernel.packages.registry import PackageRegistry
from qal_kernel.packages.validator import PackageValidator


def _manifest(
    package_id: str,
    *,
    dependencies: tuple[str, ...] = (),
) -> PackageManifest:
    return PackageManifest(
        package_id=package_id,
        name=package_id,
        version="1.0.0",
        category="platform",
        description=f"Test package: {package_id}",
        author="Quanntiq",
        entry_point="qal_kernel.packages.package:Package",
        dependencies=dependencies,
    )


def _manager() -> tuple[PackageManager, PackageRegistry]:
    registry = PackageRegistry()
    loader = PackageLoader(validator=PackageValidator(platform_version="1.0.0"))
    return PackageManager(loader=loader, registry=registry), registry


async def test_manager_installs_and_registers_loaded_package() -> None:
    manager, registry = _manager()

    package = await manager.install(_manifest("quanntiq.core"))

    assert package.state is PackageState.LOADED
    assert registry.get("quanntiq.core") is package


async def test_manager_runs_complete_package_lifecycle() -> None:
    manager, registry = _manager()
    await manager.install(_manifest("quanntiq.core"))

    activated = await manager.activate("quanntiq.core")
    running = await manager.start("quanntiq.core")
    deactivated = await manager.deactivate("quanntiq.core")
    uninstalled = await manager.uninstall("quanntiq.core")

    assert activated.state is PackageState.ACTIVATED
    assert running.state is PackageState.RUNNING
    assert deactivated.state is PackageState.DEACTIVATED
    assert uninstalled.state is PackageState.UNINSTALLED
    assert not registry.contains("quanntiq.core")


async def test_manager_activates_dependencies_first() -> None:
    manager, registry = _manager()
    await manager.install(_manifest("quanntiq.core"))
    await manager.install(
        _manifest(
            "quanntiq.analytics",
            dependencies=("quanntiq.core",),
        )
    )

    package = await manager.activate("quanntiq.analytics")

    assert package.state is PackageState.ACTIVATED
    assert registry.get("quanntiq.core").state is PackageState.ACTIVATED
    assert registry.get("quanntiq.analytics").state is PackageState.ACTIVATED


async def test_manager_starts_dependencies_before_package() -> None:
    manager, registry = _manager()
    await manager.install(_manifest("quanntiq.core"))
    await manager.install(
        _manifest(
            "quanntiq.analytics",
            dependencies=("quanntiq.core",),
        )
    )
    await manager.activate("quanntiq.analytics")

    package = await manager.start("quanntiq.analytics")

    assert package.state is PackageState.RUNNING
    assert registry.get("quanntiq.core").state is PackageState.RUNNING
    assert registry.get("quanntiq.analytics").state is PackageState.RUNNING


async def test_manager_deactivates_package_and_dependencies() -> None:
    manager, registry = _manager()
    await manager.install(_manifest("quanntiq.core"))
    await manager.install(
        _manifest(
            "quanntiq.analytics",
            dependencies=("quanntiq.core",),
        )
    )
    await manager.activate("quanntiq.analytics")
    await manager.start("quanntiq.analytics")

    package = await manager.deactivate("quanntiq.analytics")

    assert package.state is PackageState.DEACTIVATED
    assert registry.get("quanntiq.core").state is PackageState.DEACTIVATED
    assert registry.get("quanntiq.analytics").state is PackageState.DEACTIVATED


async def test_manager_rejects_invalid_transition() -> None:
    manager, registry = _manager()
    installed = await manager.install(_manifest("quanntiq.core"))

    with pytest.raises(
        InvalidLifecycleTransitionError,
        match=r"quanntiq\.core",
    ):
        await manager.start("quanntiq.core")

    assert registry.get("quanntiq.core") is installed
    assert installed.state is PackageState.LOADED


async def test_manager_keeps_multi_package_transition_atomic() -> None:
    manager, registry = _manager()
    core = await manager.install(_manifest("quanntiq.core"))
    analytics = await manager.install(
        _manifest(
            "quanntiq.analytics",
            dependencies=("quanntiq.core",),
        )
    )
    registry.unregister("quanntiq.analytics")
    registry.register(replace(analytics, state=PackageState.RUNNING))

    with pytest.raises(InvalidLifecycleTransitionError):
        await manager.activate("quanntiq.analytics")

    assert registry.get("quanntiq.core") is core
    assert registry.get("quanntiq.core").state is PackageState.LOADED
    assert registry.get("quanntiq.analytics").state is PackageState.RUNNING


async def test_manager_blocks_deactivation_with_active_dependent() -> None:
    manager, registry = _manager()
    core = await manager.install(_manifest("quanntiq.core"))
    analytics = await manager.install(
        _manifest(
            "quanntiq.analytics",
            dependencies=("quanntiq.core",),
        )
    )
    registry.unregister("quanntiq.core")
    registry.register(replace(core, state=PackageState.RUNNING))
    registry.unregister("quanntiq.analytics")
    registry.register(replace(analytics, state=PackageState.RUNNING))

    with pytest.raises(
        InvalidLifecycleTransitionError,
        match=r"quanntiq\.analytics",
    ):
        await manager.deactivate("quanntiq.core")

    assert registry.get("quanntiq.core").state is PackageState.RUNNING
    assert registry.get("quanntiq.analytics").state is PackageState.RUNNING


async def test_manager_blocks_uninstall_with_active_dependent() -> None:
    manager, registry = _manager()
    core = await manager.install(_manifest("quanntiq.core"))
    analytics = await manager.install(
        _manifest(
            "quanntiq.analytics",
            dependencies=("quanntiq.core",),
        )
    )
    registry.unregister("quanntiq.core")
    registry.register(replace(core, state=PackageState.DEACTIVATED))
    registry.unregister("quanntiq.analytics")
    registry.register(replace(analytics, state=PackageState.RUNNING))

    with pytest.raises(
        InvalidLifecycleTransitionError,
        match=r"quanntiq\.analytics",
    ):
        await manager.uninstall("quanntiq.core")

    assert registry.contains("quanntiq.core")
    assert registry.get("quanntiq.core").state is PackageState.DEACTIVATED
