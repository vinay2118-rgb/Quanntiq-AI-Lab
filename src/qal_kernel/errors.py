"""Kernel-specific exception hierarchy."""


class KernelError(RuntimeError):
    """Base exception for deterministic kernel failures."""


class DependencyNotFoundError(KernelError):
    """Raised when a requested dependency has not been registered."""


class DuplicateRegistrationError(KernelError):
    """Raised when registration would silently replace an existing entry."""


class CircularDependencyError(KernelError):
    """Raised when dependency resolution encounters a circular graph."""


class InvalidDependencyError(KernelError):
    """Raised when a factory returns an incompatible dependency instance."""


class InvalidLifecycleTransitionError(KernelError):
    """Raised when a lifecycle transition violates the state machine."""


class InvalidEventTopicError(KernelError):
    """Raised when an event topic violates the required routing format."""


class PackageValidationError(KernelError):
    """Base exception for package-validation failures."""


class InvalidManifestError(PackageValidationError):
    """Raised when a package manifest is incomplete or invalid."""


class InvalidPackageIdError(PackageValidationError):
    """Raised when a package identifier violates the required format."""


class InvalidVersionError(PackageValidationError):
    """Raised when a package or platform version is invalid."""


class UnsupportedPlatformError(PackageValidationError):
    """Raised when the platform version cannot support a package."""


class MissingDependencyError(PackageValidationError):
    """Raised when a required package dependency is unavailable."""


class InvalidEntryPointError(PackageValidationError):
    """Raised when a package entry point is invalid."""
