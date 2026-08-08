from datetime import UTC, datetime

from modules.data_platform.storage import FileSystemArtifactStore
from modules.data_platform.workflows import persist_source_manifest
from modules.source_intake.contracts import (
    ArtifactKind,
    ArtifactRecord,
    ArtifactState,
    SourceKind,
    SourceManifest,
    SourceReadiness,
    SourceRecord,
)


def test_persist_source_manifest_keeps_partial_artifacts_in_staging(tmp_path) -> None:
    source = SourceRecord(
        source_id="video_001",
        locator="https://example.invalid/video_001",
        kind=SourceKind.VIDEO,
        registered_at=datetime(2026, 8, 8, 12, 0, tzinfo=UTC),
    )
    root = tmp_path / "intake"
    video = root / "raw" / "video.mp4"
    video.parent.mkdir(parents=True)
    video.write_bytes(b"video")
    manifest = SourceManifest(
        source=source,
        artifacts=(
            ArtifactRecord(
                artifact_id="video_001:video",
                source_id="video_001",
                kind=ArtifactKind.VIDEO,
                relative_path="raw/video.mp4",
                state=ArtifactState.AVAILABLE,
                size_bytes=5,
            ),
            ArtifactRecord(
                artifact_id="video_001:subtitle:en",
                source_id="video_001",
                kind=ArtifactKind.SUBTITLE,
                relative_path="raw/subtitles.en.vtt",
                state=ArtifactState.MISSING,
            ),
        ),
        inspected_at=datetime(2026, 8, 8, 12, 1, tzinfo=UTC),
        readiness=SourceReadiness.PARTIAL,
    )

    result = persist_source_manifest(
        manifest,
        root,
        FileSystemArtifactStore(tmp_path / "durable"),
        stored_at=datetime(2026, 8, 8, 12, 2, tzinfo=UTC),
    )

    assert result.stored_artifacts == ()
    assert result.skipped_artifact_ids == ("video_001:subtitle:en",)
    assert video.exists()


def test_persist_source_manifest_moves_complete_artifact(tmp_path) -> None:
    source = SourceRecord(
        source_id="video_002",
        locator="https://example.invalid/video_002",
        kind=SourceKind.VIDEO,
        registered_at=datetime(2026, 8, 8, 12, 0, tzinfo=UTC),
    )
    root = tmp_path / "intake"
    video = root / "raw" / "video.mp4"
    video.parent.mkdir(parents=True)
    video.write_bytes(b"video")
    manifest = SourceManifest(
        source=source,
        artifacts=(
            ArtifactRecord(
                artifact_id="video_002:video",
                source_id="video_002",
                kind=ArtifactKind.VIDEO,
                relative_path="raw/video.mp4",
                state=ArtifactState.AVAILABLE,
                size_bytes=5,
            ),
        ),
        inspected_at=datetime(2026, 8, 8, 12, 1, tzinfo=UTC),
        readiness=SourceReadiness.READY,
    )

    result = persist_source_manifest(
        manifest,
        root,
        FileSystemArtifactStore(tmp_path / "durable"),
        stored_at=datetime(2026, 8, 8, 12, 2, tzinfo=UTC),
    )

    assert len(result.stored_artifacts) == 1
    assert not video.exists()
