"""Immutable package runtime model."""

from dataclasses import dataclass
from enum import StrEnum

from qal_kernel.packages.metadata import PackageMetadata


class PackageState(StrEnum):
    """Supported package lifecycle states."""

    DISCOVERED = "discovered"
    VALIDATED = "validated"
    INSTALLED = "installed"
    LOADED = "loaded"
    ACTIVATED = "activated"
    RUNNING = "running"
    DEACTIVATED = "deactivated"
    FAILED = "failed"
    UNINSTALLED = "uninstalled"


@dataclass(frozen=True, slots=True)
class Package:
    """Immutable representation of a package and its current state."""

    metadata: PackageMetadata
    state: PackageState = PackageState.DISCOVERED