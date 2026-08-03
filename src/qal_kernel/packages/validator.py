"""Package manifest validation."""

import re
from collections.abc import Collection

from qal_kernel.errors import (
    InvalidEntryPointError,
    InvalidManifestError,
    InvalidPackageIdError,
    InvalidVersionError,
    MissingDependencyError,
    UnsupportedPlatformError,
)
from qal_kernel.packages.manifest import PackageManifest

_PACKAGE_ID_PATTERN = re.compile(
    r"[a-z0-9]+(?:[._-][a-z0-9]+)*"
)

_ENTRY_POINT_PATTERN = re.compile(
    r"[A-Za-z_][A-Za-z0-9_]*"
    r"(?:\.[A-Za-z_][A-Za-z0-9_]*)*"
    r":[A-Za-z_][A-Za-z0-9_]*"
    r"(?:\.[A-Za-z_][A-Za-z0-9_]*)*"
)

_PRERELEASE_IDENTIFIER = (
    r"(?:0|[1-9]\d*|[0-9A-Za-z-]*[A-Za-z-][0-9A-Za-z-]*)"
)

_SEMVER_PATTERN = re.compile(
    rf"(?P<major>0|[1-9]\d*)"
    rf"\.(?P<minor>0|[1-9]\d*)"
    rf"\.(?P<patch>0|[1-9]\d*)"
    rf"(?:-(?P<prerelease>{_PRERELEASE_IDENTIFIER}"
    rf"(?:\.{_PRERELEASE_IDENTIFIER})*))?"
    rf"(?:\+[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?"
)

_ParsedVersion = tuple[int, int, int, tuple[str, ...]]


class PackageValidator:
    """Validate package manifests against platform requirements."""

    __slots__ = ("_platform_version",)

    def __init__(self, *, platform_version: str) -> None:
        self._platform_version = _parse_semver(
            platform_version,
            field_name="platform_version",
        )

    def validate(
        self,
        manifest: PackageManifest,
        *,
        available_dependencies: Collection[str],
    ) -> None:
        """Validate a package manifest or raise a typed validation error."""
        required_fields = {
            "name": manifest.name,
            "category": manifest.category,
            "description": manifest.description,
            "author": manifest.author,
        }

        for field_name, value in required_fields.items():
            if not value.strip():
                raise InvalidManifestError(
                    f"{field_name} must not be blank"
                )

        if _PACKAGE_ID_PATTERN.fullmatch(manifest.package_id) is None:
            raise InvalidPackageIdError(
                f"Invalid package identifier: {manifest.package_id!r}"
            )

        package_version = _parse_semver(
            manifest.version,
            field_name="version",
        )
        minimum_platform_version = _parse_semver(
            manifest.minimum_platform_version,
            field_name="minimum_platform_version",
        )

        if not _is_at_least(
            self._platform_version,
            minimum_platform_version,
        ):
            raise UnsupportedPlatformError(
                "Package requires platform version "
                f"{manifest.minimum_platform_version} or later"
            )

        missing_dependencies = tuple(
            dependency
            for dependency in manifest.dependencies
            if dependency not in available_dependencies
        )
        if missing_dependencies:
            raise MissingDependencyError(
                "Missing package dependencies: "
                + ", ".join(missing_dependencies)
            )

        if _ENTRY_POINT_PATTERN.fullmatch(manifest.entry_point) is None:
            raise InvalidEntryPointError(
                f"Invalid package entry point: {manifest.entry_point!r}"
            )

        # Parsing validates the package version even though compatibility
        # depends only on the minimum platform version.
        _ = package_version


def _parse_semver(
    value: str,
    *,
    field_name: str,
) -> _ParsedVersion:
    match = _SEMVER_PATTERN.fullmatch(value)
    if match is None:
        raise InvalidVersionError(
            f"{field_name} must be a valid semantic version: {value!r}"
        )

    prerelease_text = match.group("prerelease")
    prerelease = (
        tuple(prerelease_text.split("."))
        if prerelease_text is not None
        else ()
    )

    return (
        int(match.group("major")),
        int(match.group("minor")),
        int(match.group("patch")),
        prerelease,
    )


def _is_at_least(
    current: _ParsedVersion,
    minimum: _ParsedVersion,
) -> bool:
    current_core = (current[0], current[1], current[2])
    minimum_core = (minimum[0], minimum[1], minimum[2])

    if current_core != minimum_core:
        return current_core > minimum_core

    return _compare_prerelease(current[3], minimum[3]) >= 0


def _compare_prerelease(
    left: tuple[str, ...],
    right: tuple[str, ...],
) -> int:
    if not left:
        return 0 if not right else 1
    if not right:
        return -1

    for left_identifier, right_identifier in zip(left, right, strict=False):
        if left_identifier == right_identifier:
            continue

        left_is_numeric = left_identifier.isdigit()
        right_is_numeric = right_identifier.isdigit()

        if left_is_numeric and right_is_numeric:
            return (
                1
                if int(left_identifier) > int(right_identifier)
                else -1
            )

        if left_is_numeric != right_is_numeric:
            return -1 if left_is_numeric else 1

        return 1 if left_identifier > right_identifier else -1

    return (len(left) > len(right)) - (len(left) < len(right))