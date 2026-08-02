"""Package manifest contract tests."""

from dataclasses import FrozenInstanceError

import pytest

from qal_kernel.packages.manifest import PackageManifest


def test_package_manifest_preserves_explicit_values() -> None:
    manifest = PackageManifest(
        package_id="qal.research.market",
        name="Market Research",
        version="1.2.3",
        category="research",
        description="Enterprise market-research capability.",
        author="Quanntiq",
        entry_point="qal_research_market:MarketResearchPackage",
        capabilities=("web-research", "source-validation"),
        dependencies=("qal.knowledge.core",),
        minimum_platform_version="1.0.0",
    )

    assert manifest.package_id == "qal.research.market"
    assert manifest.name == "Market Research"
    assert manifest.version == "1.2.3"
    assert manifest.category == "research"
    assert manifest.description == "Enterprise market-research capability."
    assert manifest.author == "Quanntiq"
    assert manifest.entry_point == (
        "qal_research_market:MarketResearchPackage"
    )
    assert manifest.capabilities == (
        "web-research",
        "source-validation",
    )
    assert manifest.dependencies == ("qal.knowledge.core",)
    assert manifest.minimum_platform_version == "1.0.0"


def test_package_manifest_applies_safe_defaults() -> None:
    manifest = PackageManifest(
        package_id="qal.engineering.core",
        name="Engineering Core",
        version="1.0.0",
        category="engineering",
        description="Core engineering capability.",
        author="Quanntiq",
        entry_point="qal_engineering_core:EngineeringPackage",
    )

    assert manifest.capabilities == ()
    assert manifest.dependencies == ()
    assert manifest.minimum_platform_version == "1.0.0"


def test_package_manifest_is_frozen_and_slotted() -> None:
    manifest = PackageManifest(
        package_id="qal.qa.core",
        name="Quality Assurance",
        version="1.0.0",
        category="quality",
        description="Quality-assurance capability.",
        author="Quanntiq",
        entry_point="qal_qa_core:QualityPackage",
    )

    assert not hasattr(manifest, "__dict__")

    with pytest.raises(FrozenInstanceError):
        manifest.version = "2.0.0"  # type: ignore[misc]