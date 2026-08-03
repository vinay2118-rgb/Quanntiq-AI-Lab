"""Deterministic package dependency resolution."""

from qal_kernel.errors import (
    CircularDependencyError,
    MissingDependencyError,
    PackageNotFoundError,
)
from qal_kernel.packages.package import Package
from qal_kernel.packages.registry import PackageRegistry


class PackageDependencyResolver:
    """Resolve registered packages into dependency-first order."""

    def __init__(self, registry: PackageRegistry) -> None:
        self._registry = registry

    def resolve(self, package_id: str) -> tuple[Package, ...]:
        """Resolve one package and all its transitive dependencies."""
        ordered: list[Package] = []
        resolved: set[str] = set()
        visiting: set[str] = set()
        path: list[str] = []

        package = self._registry.get(package_id)
        self._visit(
            package,
            ordered=ordered,
            resolved=resolved,
            visiting=visiting,
            path=path,
        )
        return tuple(ordered)

    def resolve_all(self) -> tuple[Package, ...]:
        """Resolve every registered package into dependency-first order."""
        ordered: list[Package] = []
        resolved: set[str] = set()
        visiting: set[str] = set()
        path: list[str] = []

        for package in self._registry.all():
            self._visit(
                package,
                ordered=ordered,
                resolved=resolved,
                visiting=visiting,
                path=path,
            )

        return tuple(ordered)

    def _visit(
        self,
        package: Package,
        *,
        ordered: list[Package],
        resolved: set[str],
        visiting: set[str],
        path: list[str],
    ) -> None:
        package_id = package.metadata.package_id

        if package_id in resolved:
            return

        if package_id in visiting:
            cycle_start = path.index(package_id)
            cycle = (*path[cycle_start:], package_id)
            raise CircularDependencyError(
                "Circular package dependency: " + " -> ".join(cycle)
            )

        visiting.add(package_id)
        path.append(package_id)

        for dependency_id in sorted(package.metadata.dependencies):
            try:
                dependency = self._registry.get(dependency_id)
            except PackageNotFoundError:
                raise MissingDependencyError(
                    f"Package {package_id} requires missing dependency: "
                    f"{dependency_id}"
                ) from None

            self._visit(
                dependency,
                ordered=ordered,
                resolved=resolved,
                visiting=visiting,
                path=path,
            )

        path.pop()
        visiting.remove(package_id)
        resolved.add(package_id)
        ordered.append(package)
