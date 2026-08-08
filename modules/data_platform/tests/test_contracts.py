from datetime import UTC, datetime

import pytest

from modules.data_platform.contracts import StoredArtifact, StorageKey


def test_storage_key_rejects_escape_paths() -> None:
    with pytest.raises(ValueError):
        StorageKey("source_1", "../outside.bin")


def test_stored_artifact_keeps_storage_identity() -> None:
    item = StoredArtifact(
        artifact_id="source_1:video",
        source_id="source_1",
        relative_path="raw/video.mp4",
        size_bytes=4,
        sha256="a" * 64,
        stored_at=datetime(2026, 8, 8, tzinfo=UTC),
    )

    assert item.source_id == "source_1"
    assert item.relative_path == "raw/video.mp4"

