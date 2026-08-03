"""Package loader contract tests."""

from dataclasses import replace
from datetime import UTC

import pytest

from qal_kernel.errors import (
    InvalidEntryPointError,
    KernelError,
    PackageLoadError,
    PackageValidationError,
)
from qal_kernel.packages.loader import PackageLoader
from qal_kernel.packages.manifest import PackageManifest
from qal_kernel.packages.package import PackageState
from qal_kernel.packages.validator import PackageValidator

_VALID_MANIFEST = PackageManifest(
    package_id="quanntiq.analytics",
    name="Quanntiq Analytics",
    version="1.2.3",
    category="analytics",
    description="Enterprise analytics package.",
    author="Quanntiq",
    entry_point="qal_kernel.packages.package:Package",
    capabilities=("analytics.reporting",),
    dependencies=("quanntiq.core",),
    minimum_platform_version="1.0.0",
)


def _loader() -> PackageLoader:
    return PackageLoader(
        validator=PackageValidator(platform_version="1.2.0")
    )


def test_package_load_error_follows_kernel_hierarchy() -> None:
    assert issubclass(PackageLoadError, KernelError)
    assert not issubclass(PackageLoadError, PackageValidationError)


def test_loader_returns_loaded_package_with_manifest_metadata() -> None:
    package = _loader().load(
        _VALID_MANIFEST,
        available_dependencies={"quanntiq.core"},
    )

    assert package.state is PackageState.LOADED
    assert package.metadata.package_id == _VALID_MANIFEST.package_id
    assert package.metadata.name == _VALID_MANIFEST.name
    assert package.metadata.version == _VALID_MANIFEST.version
    assert package.metadata.category == _VALID_MANIFEST.category
    assert package.metadata.description == _VALID_MANIFEST.description
    assert package.metadata.author == _VALID_MANIFEST.author
    assert package.metadata.capabilities == _VALID_MANIFEST.capabilities
    assert package.metadata.dependencies == _VALID_MANIFEST.dependencies
    assert (
        package.metadata.minimum_platform_version
        == _VALID_MANIFEST.minimum_platform_version
    )
    assert package.metadata.installed_at.tzinfo is UTC
    assert package.metadata.verified is True


@pytest.mark.parametrize(
    "entry_point",
    (
        "qal_kernel.packages.missing:Package",
        "qal_kernel.packages.package:MissingPackage",
    ),
)
def test_loader_wraps_runtime_resolution_failures(
    entry_point: str,
) -> None:
    manifest = replace(_VALID_MANIFEST, entry_point=entry_point)

    with pytest.raises(
        PackageLoadError,
        match="Unable to load package entry point",
    ) as error_info:
        _loader().load(
            manifest,
            available_dependencies={"quanntiq.core"},
        )

    assert error_info.value.__cause__ is not None


def test_loader_preserves_validation_errors() -> None:
    manifest = replace(_VALID_MANIFEST, entry_point="invalid")

    with pytest.raises(InvalidEntryPointError):
        _loader().load(
            manifest,
            available_dependencies={"quanntiq.core"},
        )