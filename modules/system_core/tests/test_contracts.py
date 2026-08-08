from datetime import UTC, datetime

import pytest

from modules.system_core.contracts import (
    ContractDeclaration,
    ModuleManifest,
    ModuleVersionRecord,
    RunManifest,
    RuntimeMode,
    SemanticVersion,
)


def _manifest(module_id: str = "sample_module") -> ModuleManifest:
    return ModuleManifest(
        module_id=module_id,
        version=SemanticVersion.parse("0.1.0"),
        description="A test module",
        supported_modes=frozenset({RuntimeMode.BACKTEST, RuntimeMode.PAPER}),
        provided_contracts=(
            ContractDeclaration("sample.output", SemanticVersion.parse("0.1.0")),
        ),
    )


def test_semantic_version_is_ordered_and_parseable() -> None:
    assert SemanticVersion.parse("0.2.0") > SemanticVersion.parse("0.1.0")
    assert str(SemanticVersion.parse("1.0.3")) == "1.0.3"


def test_module_manifest_rejects_duplicate_contracts() -> None:
    with pytest.raises(ValueError, match="duplicate"):
        ModuleManifest(
            module_id="sample_module",
            version=SemanticVersion.parse("0.1.0"),
            description="A test module",
            supported_modes=frozenset({RuntimeMode.BACKTEST}),
            provided_contracts=(
                ContractDeclaration("sample.output", SemanticVersion.parse("0.1.0")),
                ContractDeclaration("sample.output", SemanticVersion.parse("0.1.0")),
            ),
        )


def test_run_manifest_is_timezone_aware_and_immutable() -> None:
    manifest = RunManifest(
        run_id="run-001",
        mode=RuntimeMode.BACKTEST,
        started_at=datetime(2026, 8, 7, 12, 0, tzinfo=UTC),
        module_versions=(
            ModuleVersionRecord("sample_module", SemanticVersion.parse("0.1.0")),
        ),
    )

    assert manifest.mode is RuntimeMode.BACKTEST
    with pytest.raises(AttributeError):
        manifest.run_id = "run-002"  # type: ignore[misc]
