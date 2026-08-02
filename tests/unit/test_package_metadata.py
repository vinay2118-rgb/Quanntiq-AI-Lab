"""Package metadata contract tests."""

from dataclasses import FrozenInstanceError
from datetime import UTC, datetime

import pytest

from qal_kernel.packages.metadata import PackageMetadata


def test_package_metadata_preserves_explicit_values() -> None:
    installed_at = datetime(2026, 8, 2, tzinfo=UTC)

    metadata = PackageMetadata(
        package_id="qal.research.market",
        name="Market Research",
        version="1.2.3",
        category="research",
        description="Enterprise market-research capability.",
        author="Quanntiq",
        capabilities=("web-research", "source-validation"),
        dependencies=("qal.knowledge.core",),
        minimum_platform_version="1.0.0",
        installed_at=installed_at,
        verified=False,
    )

    assert metadata.package_id == "qal.research.market"
    assert metadata.name == "Market Research"
    assert metadata.version == "1.2.3"
    assert metadata.category == "research"
    assert metadata.description == "Enterprise market-research capability."
    assert metadata.author == "Quanntiq"
    assert metadata.capabilities == ("web-research", "source-validation")
    assert metadata.dependencies == ("qal.knowledge.core",)
    assert metadata.minimum_platform_version == "1.0.0"
    assert metadata.installed_at is installed_at
    assert metadata.verified is False


def test_package_metadata_applies_safe_defaults() -> None:
    before_creation = datetime.now(UTC)

    metadata = PackageMetadata(
        package_id="qal.engineering.core",
        name="Engineering Core",
        version="1.0.0",
        category="engineering",
        description="Core engineering capability.",
        author="Quanntiq",
    )

    after_creation = datetime.now(UTC)

    assert metadata.capabilities == ()
    assert metadata.dependencies == ()
    assert metadata.minimum_platform_version == "1.0.0"
    assert before_creation <= metadata.installed_at <= after_creation
    assert metadata.installed_at.tzinfo is UTC
    assert metadata.verified is True


def test_package_metadata_is_frozen_and_slotted() -> None:
    metadata = PackageMetadata(
        package_id="qal.qa.core",
        name="Quality Assurance",
        version="1.0.0",
        category="quality",
        description="Quality-assurance capability.",
        author="Quanntiq",
    )

    assert not hasattr(metadata, "__dict__")

    with pytest.raises(FrozenInstanceError):
        metadata.name = "Changed"  # type: ignore[misc]