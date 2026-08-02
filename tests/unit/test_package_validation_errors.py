"""Package-validation exception contract tests."""

from qal_kernel.errors import (
    InvalidEntryPointError,
    InvalidManifestError,
    InvalidPackageIdError,
    InvalidVersionError,
    KernelError,
    MissingDependencyError,
    PackageValidationError,
    UnsupportedPlatformError,
)


def test_package_validation_errors_follow_kernel_hierarchy() -> None:
    assert issubclass(PackageValidationError, KernelError)

    specific_errors = (
        InvalidManifestError,
        InvalidPackageIdError,
        InvalidVersionError,
        UnsupportedPlatformError,
        MissingDependencyError,
        InvalidEntryPointError,
    )

    for error_type in specific_errors:
        assert issubclass(error_type, PackageValidationError)