"""Validated package entry-point loading."""

from collections.abc import Collection
from importlib import import_module

from qal_kernel.errors import PackageLoadError
from qal_kernel.packages.manifest import PackageManifest
from qal_kernel.packages.metadata import PackageMetadata
from qal_kernel.packages.package import Package, PackageState
from qal_kernel.packages.validator import PackageValidator


class PackageLoader:
    """Validate and load package entry points deterministically."""

    __slots__ = ("_validator",)

    def __init__(self, *, validator: PackageValidator) -> None:
        self._validator = validator

    def load(
        self,
        manifest: PackageManifest,
        *,
        available_dependencies: Collection[str],
    ) -> Package:
        """Validate and load a package or raise a typed error."""
        self._validator.validate(
            manifest,
            available_dependencies=available_dependencies,
        )
        _resolve_entry_point(manifest.entry_point)

        metadata = PackageMetadata(
            package_id=manifest.package_id,
            name=manifest.name,
            version=manifest.version,
            category=manifest.category,
            description=manifest.description,
            author=manifest.author,
            capabilities=manifest.capabilities,
            dependencies=manifest.dependencies,
            minimum_platform_version=manifest.minimum_platform_version,
        )

        return Package(
            metadata=metadata,
            state=PackageState.LOADED,
        )


def _resolve_entry_point(entry_point: str) -> object:
    module_name, attribute_path = entry_point.split(":", maxsplit=1)

    try:
        resolved: object = import_module(module_name)
        for attribute_name in attribute_path.split("."):
            resolved = getattr(resolved, attribute_name)
    except Exception as error:
        raise PackageLoadError(
            f"Unable to load package entry point: {entry_point!r}"
        ) from error

    return resolved