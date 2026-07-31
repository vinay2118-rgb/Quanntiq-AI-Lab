"""Kernel-specific exception hierarchy."""


class KernelError(RuntimeError):
    """Base exception for deterministic kernel failures."""


class DependencyNotFoundError(KernelError):
    """Raised when a requested dependency has not been registered."""


class DuplicateRegistrationError(KernelError):
    """Raised when registration would silently replace an existing entry."""


class InvalidLifecycleTransitionError(KernelError):
    """Raised when a lifecycle transition violates the state machine."""
