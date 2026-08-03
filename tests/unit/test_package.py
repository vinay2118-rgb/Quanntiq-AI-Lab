"""Package runtime-model contract tests."""

from dataclasses import FrozenInstanceError

import pytest

from qal_kernel.packages.metadata import PackageMetadata
from qal_kernel.packages.package import Package, PackageState


def _metadata() -> PackageMetadata:
    return PackageMetadata(
        package_id="qal.research.market",
        name="Market Research",
        version="1.2.3",
        category="research",
        description="Enterprise market-research capability.",
        author="Quanntiq",
    )


def test_package_state_contract_is_complete() -> None:
    assert {state.name: state.value for state in PackageState} == {
        "DISCOVERED": "discovered",
        "VALIDATED": "validated",
        "INSTALLED": "installed",
        "LOADED": "loaded",
        "ACTIVATED": "activated",
        "RUNNING": "running",
        "DEACTIVATED": "deactivated",
        "FAILED": "failed",
        "UNINSTALLED": "uninstalled",
    }


def test_package_defaults_to_discovered() -> None:
    metadata = _metadata()

    package = Package(metadata=metadata)

    assert package.metadata is metadata
    assert package.state is PackageState.DISCOVERED


def test_package_preserves_explicit_state() -> None:
    metadata = _metadata()

    package = Package(
        metadata=metadata,
        state=PackageState.RUNNING,
    )

    assert package.metadata is metadata
    assert package.state is PackageState.RUNNING


def test_package_is_frozen_and_slotted() -> None:
    package = Package(metadata=_metadata())

    assert not hasattr(package, "__dict__")

    with pytest.raises(FrozenInstanceError):
        package.state = PackageState.FAILED  # type: ignore[misc]