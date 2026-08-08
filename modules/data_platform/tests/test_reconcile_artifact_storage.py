from datetime import UTC, datetime

from modules.data_platform.catalog import SourceCatalog
from modules.data_platform.storage import FileSystemArtifactStore
from modules.data_platform.workflows import reconcile_artifact_storage
from modules.source_intake.contracts import (
    ArtifactKind,
    ArtifactRecord,
    ArtifactState,
    SourceKind,
    SourceManifest,
    SourceReadiness,
    SourceRecord,
)


def test_reconcile_moves_ready_and_removes_partial_duplicates(tmp_path) -> None:
    catalog = SourceCatalog(tmp_path / "catalog.sqlite3")
    staging_root = tmp_path / "staging"
    store = FileSystemArtifactStore(tmp_path / "durable")
    for source_id, readiness in (("ready_001", SourceReadiness.READY), ("partial_001", SourceReadiness.PARTIAL)):
        source = SourceRecord(
            source_id=source_id,
            locator=f"local://{source_id}.txt",
            kind=SourceKind.DOCUMENT,
            registered_at=datetime(2026, 8, 8, tzinfo=UTC),
        )
        source_file = staging_root / source_id / "raw" / "source.txt"
        source_file.parent.mkdir(parents=True)
        source_file.write_bytes(source_id.encode())
        manifest = SourceManifest(
            source=source,
            artifacts=(
                ArtifactRecord(
                    artifact_id=f"{source_id}:document",
                    source_id=source_id,
                    kind=ArtifactKind.DOCUMENT,
                    relative_path="raw/source.txt",
                    state=ArtifactState.AVAILABLE,
                    size_bytes=len(source_id),
                ),
            ),
            inspected_at=datetime(2026, 8, 8, 12, 1, tzinfo=UTC),
            readiness=readiness,
        )
        catalog.upsert_manifest(manifest)
        if readiness is SourceReadiness.PARTIAL:
            store.put_file(
                f"{source_id}:document",
                source_id,
                "raw/source.txt",
                source_file,
            )

    result = reconcile_artifact_storage(catalog, staging_root, store)

    assert result.promoted_source_ids == ("ready_001",)
    assert result.staging_source_ids == ("partial_001",)
    assert result.removed_duplicate_count == 1
    assert store.exists("ready_001", "raw/source.txt")
    assert not (staging_root / "ready_001" / "raw" / "source.txt").exists()
    assert not store.exists("partial_001", "raw/source.txt")
    assert (staging_root / "partial_001" / "raw" / "source.txt").exists()

