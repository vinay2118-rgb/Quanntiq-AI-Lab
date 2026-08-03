"""Atomic package lifecycle coordination."""

import asyncio
from dataclasses import replace

from qal_kernel.errors import InvalidLifecycleTransitionError
from qal_kernel.packages.loader import PackageLoader
from qal_kernel.packages.manifest import PackageManifest
from qal_kernel.packages.package import Package, PackageState
from qal_kernel.packages.registry import PackageRegistry
from qal_kernel.packages.resolver import PackageDependencyResolver

_ACTIVE_STATES = frozenset(
    {
        PackageState.ACTIVATED,
        PackageState.RUNNING,
    }
)


class PackageManager:
    """Coordinate package installation and lifecycle transitions."""

    def __init__(
        self,
        *,
        loader: PackageLoader,
        registry: PackageRegistry,
    ) -> None:
        self._loader = loader
        self._registry = registry
        self._resolver = PackageDependencyResolver(registry)
        self._lock = asyncio.Lock()

    async def install(self, manifest: PackageManifest) -> Package:
        """Load and register a validated package."""
        async with self._lock:
            available_dependencies = {
                package.metadata.package_id for package in self._registry.all()
            }
            package = self._loader.load(
                manifest,
                available_dependencies=available_dependencies,
            )
            self._registry.register(package)
            return package

    async def activate(self, package_id: str) -> Package:
        """Activate a package after activating its dependencies."""
        async with self._lock:
            packages = self._resolver.resolve(package_id)
            plan: list[tuple[Package, PackageState]] = []

            for package in packages:
                is_target = package.metadata.package_id == package_id

                if package.state in {
                    PackageState.LOADED,
                    PackageState.DEACTIVATED,
                }:
                    plan.append((package, PackageState.ACTIVATED))
                    continue

                if not is_target and package.state in _ACTIVE_STATES:
                    continue

                self._raise_invalid_transition(
                    operation="activate",
                    package=package,
                )

            self._apply(plan)
            return self._registry.get(package_id)

    async def start(self, package_id: str) -> Package:
        """Start an activated package after starting its dependencies."""
        async with self._lock:
            packages = self._resolver.resolve(package_id)
            plan: list[tuple[Package, PackageState]] = []

            for package in packages:
                is_target = package.metadata.package_id == package_id

                if package.state is PackageState.ACTIVATED:
                    plan.append((package, PackageState.RUNNING))
                    continue

                if not is_target and package.state is PackageState.RUNNING:
                    continue

                self._raise_invalid_transition(
                    operation="start",
                    package=package,
                )

            self._apply(plan)
            return self._registry.get(package_id)

    async def deactivate(self, package_id: str) -> Package:
        """Deactivate a package and its dependencies in reverse order."""
        async with self._lock:
            packages = self._resolver.resolve(package_id)
            package_ids = {package.metadata.package_id for package in packages}

            self._ensure_no_active_external_dependents(
                operation="deactivate",
                package_ids=package_ids,
            )

            plan: list[tuple[Package, PackageState]] = []

            for package in reversed(packages):
                is_target = package.metadata.package_id == package_id

                if package.state in _ACTIVE_STATES:
                    plan.append((package, PackageState.DEACTIVATED))
                    continue

                if not is_target and package.state is PackageState.DEACTIVATED:
                    continue

                self._raise_invalid_transition(
                    operation="deactivate",
                    package=package,
                )

            self._apply(plan)
            return self._registry.get(package_id)

    async def uninstall(self, package_id: str) -> Package:
        """Remove an inactive package that has no registered dependents."""
        async with self._lock:
            package = self._registry.get(package_id)

            if package.state not in {
                PackageState.LOADED,
                PackageState.DEACTIVATED,
            }:
                self._raise_invalid_transition(
                    operation="uninstall",
                    package=package,
                )

            dependent = self._find_dependent(package_id)
            if dependent is not None:
                raise InvalidLifecycleTransitionError(
                    f"Cannot uninstall {package_id}; "
                    f"package {dependent.metadata.package_id} depends on it"
                )

            uninstalled = replace(
                package,
                state=PackageState.UNINSTALLED,
            )
            self._registry.unregister(package_id)
            return uninstalled

    def _apply(
        self,
        plan: list[tuple[Package, PackageState]],
    ) -> None:
        """Apply a fully validated immutable transition plan."""
        for package, state in plan:
            package_id = package.metadata.package_id
            transitioned = replace(package, state=state)
            self._registry.unregister(package_id)
            self._registry.register(transitioned)

    def _ensure_no_active_external_dependents(
        self,
        *,
        operation: str,
        package_ids: set[str],
    ) -> None:
        for candidate in self._registry.all():
            candidate_id = candidate.metadata.package_id

            if candidate_id in package_ids or candidate.state not in _ACTIVE_STATES:
                continue

            resolved_ids = {
                package.metadata.package_id for package in self._resolver.resolve(candidate_id)
            }

            if resolved_ids.intersection(package_ids):
                raise InvalidLifecycleTransitionError(
                    f"Cannot {operation}; active dependent {candidate_id} would be affected"
                )

    def _find_dependent(self, package_id: str) -> Package | None:
        for candidate in self._registry.all():
            candidate_id = candidate.metadata.package_id

            if candidate_id == package_id:
                continue

            resolved_ids = {
                package.metadata.package_id for package in self._resolver.resolve(candidate_id)
            }

            if package_id in resolved_ids:
                return candidate

        return None

    @staticmethod
    def _raise_invalid_transition(
        *,
        operation: str,
        package: Package,
    ) -> None:
        raise InvalidLifecycleTransitionError(
            f"Cannot {operation} package {package.metadata.package_id} from {package.state}"
        )
