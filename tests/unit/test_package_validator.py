"""Package manifest validator contract tests."""

from dataclasses import replace

import pytest

from qal_kernel.errors import (
    InvalidEntryPointError,
    InvalidManifestError,
    InvalidPackageIdError,
    InvalidVersionError,
    MissingDependencyError,
    UnsupportedPlatformError,
)
from qal_kernel.packages.manifest import PackageManifest
from qal_kernel.packages.validator import PackageValidator

_VALID_MANIFEST = PackageManifest(
    package_id="quanntiq.analytics",
    name="Quanntiq Analytics",
    version="1.2.3",
    category="analytics",
    description="Enterprise analytics package.",
    author="Quanntiq",
    entry_point="qal_plugins.analytics:AnalyticsPackage",
    capabilities=("analytics.reporting",),
    dependencies=("quanntiq.core",),
    minimum_platform_version="1.0.0",
)


def test_validator_accepts_valid_manifest() -> None:
    validator = PackageValidator(platform_version="1.2.0")

    validator.validate(
        _VALID_MANIFEST,
        available_dependencies={"quanntiq.core"},
    )


@pytest.mark.parametrize(
    "field_name",
    ("name", "category", "description", "author"),
)
def test_validator_rejects_blank_required_fields(field_name: str) -> None:
    validator = PackageValidator(platform_version="1.2.0")
    manifest = replace(_VALID_MANIFEST, **{field_name: "   "})

    with pytest.raises(InvalidManifestError):
        validator.validate(
            manifest,
            available_dependencies={"quanntiq.core"},
        )


@pytest.mark.parametrize(
    "package_id",
    ("Quanntiq.Analytics", "quanntiq analytics", ".quanntiq.analytics"),
)
def test_validator_rejects_invalid_package_id(package_id: str) -> None:
    validator = PackageValidator(platform_version="1.2.0")
    manifest = replace(_VALID_MANIFEST, package_id=package_id)

    with pytest.raises(InvalidPackageIdError):
        validator.validate(
            manifest,
            available_dependencies={"quanntiq.core"},
        )


@pytest.mark.parametrize(
    ("field_name", "version"),
    (
        ("version", "1.2"),
        ("version", "v1.2.3"),
        ("minimum_platform_version", "latest"),
    ),
)
def test_validator_rejects_invalid_semantic_versions(
    field_name: str,
    version: str,
) -> None:
    validator = PackageValidator(platform_version="1.2.0")
    manifest = replace(_VALID_MANIFEST, **{field_name: version})

    with pytest.raises(InvalidVersionError):
        validator.validate(
            manifest,
            available_dependencies={"quanntiq.core"},
        )


def test_validator_rejects_invalid_current_platform_version() -> None:
    with pytest.raises(InvalidVersionError):
        PackageValidator(platform_version="1.2")


def test_validator_accepts_semver_prerelease_and_build_metadata() -> None:
    validator = PackageValidator(platform_version="1.2.3")
    manifest = replace(
        _VALID_MANIFEST,
        version="2.0.0-alpha.1+build.5",
        minimum_platform_version="1.2.3-rc.1",
    )

    validator.validate(
        manifest,
        available_dependencies={"quanntiq.core"},
    )


def test_validator_rejects_unsupported_platform_version() -> None:
    validator = PackageValidator(platform_version="1.4.9")
    manifest = replace(_VALID_MANIFEST, minimum_platform_version="2.0.0")

    with pytest.raises(UnsupportedPlatformError):
        validator.validate(
            manifest,
            available_dependencies={"quanntiq.core"},
        )


def test_validator_reports_missing_dependencies() -> None:
    validator = PackageValidator(platform_version="1.2.0")
    manifest = replace(
        _VALID_MANIFEST,
        dependencies=("quanntiq.core", "quanntiq.knowledge"),
    )

    with pytest.raises(MissingDependencyError, match=r"quanntiq\.knowledge"):
        validator.validate(
            manifest,
            available_dependencies={"quanntiq.core"},
        )


@pytest.mark.parametrize(
    "entry_point",
    ("qal_plugins.analytics", "qal-plugins.analytics:Package", ":Package"),
)
def test_validator_rejects_invalid_entry_point(entry_point: str) -> None:
    validator = PackageValidator(platform_version="1.2.0")
    manifest = replace(_VALID_MANIFEST, entry_point=entry_point)

    with pytest.raises(InvalidEntryPointError):
        validator.validate(
            manifest,
            available_dependencies={"quanntiq.core"},
        )