from datetime import UTC, datetime

from modules.source_intake.contracts import ArtifactKind, SourceKind, SourceReadiness, SourceRecord
from modules.source_intake.registry import SourceRegistry
from modules.source_intake.workflows import intake_source
from modules.source_intake import build_module_manifest
from modules.system_core.contracts import ModuleStatus, RuntimeMode
from modules.system_core.runtime import SystemRuntime


def test_intake_workflow_registers_source_and_builds_manifest(tmp_path) -> None:
    source = SourceRecord(
        source_id="video_001",
        locator="https://example.invalid/video_001",
        kind=SourceKind.VIDEO,
        registered_at=datetime(2026, 8, 8, 12, 0, tzinfo=UTC),
    )
    registry = SourceRegistry()

    result = intake_source(
        registry,
        source,
        tmp_path,
        {ArtifactKind.METADATA: "raw/info.json"},
        datetime(2026, 8, 8, 12, 1, tzinfo=UTC),
    )

    assert result.registered_new_source is True
    assert result.manifest.source.source_id == "video_001"
    assert result.manifest.readiness is SourceReadiness.PARTIAL


def test_intake_workflow_is_idempotent_for_same_source(tmp_path) -> None:
    source = SourceRecord(
        source_id="video_001",
        locator="https://example.invalid/video_001",
        kind=SourceKind.VIDEO,
        registered_at=datetime(2026, 8, 8, 12, 0, tzinfo=UTC),
    )
    registry = SourceRegistry()
    paths = {ArtifactKind.METADATA: "raw/info.json"}
    inspected_at = datetime(2026, 8, 8, 12, 1, tzinfo=UTC)

    first = intake_source(registry, source, tmp_path, paths, inspected_at)
    second = intake_source(registry, source, tmp_path, paths, inspected_at)

    assert first.registered_new_source is True
    assert second.registered_new_source is False
    assert second.manifest == first.manifest


def test_source_intake_registers_with_system_core() -> None:
    runtime = SystemRuntime()

    runtime.register_module(build_module_manifest())
    runtime.set_mode(RuntimeMode.BACKTEST)
    runtime.start_module("source_intake")

    assert runtime.registry.get("source_intake").status is ModuleStatus.STARTING
