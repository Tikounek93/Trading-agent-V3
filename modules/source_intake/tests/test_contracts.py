from datetime import UTC, datetime

import pytest

from modules.source_intake.contracts import (
    ArtifactKind,
    ArtifactRecord,
    ArtifactState,
    SourceKind,
    SourceReadiness,
    SourceRecord,
)


def _source() -> SourceRecord:
    return SourceRecord(
        source_id="video_001",
        locator="https://example.invalid/video_001",
        kind=SourceKind.VIDEO,
        registered_at=datetime(2026, 8, 8, 12, 0, tzinfo=UTC),
        title="Example source",
    )


def test_source_record_rejects_unsafe_identifier() -> None:
    with pytest.raises(ValueError):
        SourceRecord(
            source_id="../video",
            locator="https://example.invalid/video",
            kind=SourceKind.VIDEO,
            registered_at=datetime(2026, 8, 8, 12, 0, tzinfo=UTC),
        )


def test_artifact_record_rejects_absolute_or_parent_paths() -> None:
    for path in ("/tmp/video.mp4", "nested/../video.mp4"):
        with pytest.raises(ValueError):
            ArtifactRecord(
                artifact_id="video_001:video",
                source_id="video_001",
                kind=ArtifactKind.VIDEO,
                relative_path=path,
                state=ArtifactState.MISSING,
            )


def test_source_contracts_are_immutable() -> None:
    source = _source()
    assert source.source_id == "video_001"
    assert SourceReadiness.NOT_READY.value == "not_ready"
    with pytest.raises((AttributeError, TypeError)):
        source.source_id = "changed"  # type: ignore[misc]
