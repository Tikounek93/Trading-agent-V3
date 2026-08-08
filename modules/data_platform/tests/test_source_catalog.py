from datetime import UTC, datetime

from modules.data_platform.catalog import SourceCatalog
from modules.source_intake.contracts import (
    ArtifactKind,
    ArtifactRecord,
    ArtifactState,
    SourceKind,
    SourceManifest,
    SourceReadiness,
    SourceRecord,
)


def test_catalog_keeps_latest_manifest_and_source_status(tmp_path) -> None:
    source = SourceRecord(
        source_id="video_001",
        locator="https://example.invalid/video_001",
        kind=SourceKind.VIDEO,
        registered_at=datetime(2026, 8, 8, 12, 0, tzinfo=UTC),
        title="Example video",
    )
    manifest = SourceManifest(
        source=source,
        artifacts=(
            ArtifactRecord(
                artifact_id="video_001:metadata",
                source_id="video_001",
                kind=ArtifactKind.METADATA,
                relative_path="raw/info.json",
                state=ArtifactState.AVAILABLE,
                size_bytes=10,
            ),
        ),
        inspected_at=datetime(2026, 8, 8, 12, 1, tzinfo=UTC),
        readiness=SourceReadiness.READY,
    )

    catalog = SourceCatalog(tmp_path / "catalog.sqlite3")
    catalog.upsert_manifest(manifest)
    [summary] = catalog.list_sources()

    assert summary.source_id == "video_001"
    assert summary.readiness == "ready"
    assert summary.artifact_count == 1
    assert summary.available_artifact_count == 1
    [artifact] = catalog.list_artifacts("video_001")
    assert artifact.state == "available"
    assert artifact.relative_path == "raw/info.json"
