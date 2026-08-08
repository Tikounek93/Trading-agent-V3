from datetime import UTC, datetime

from modules.data_platform.storage import FileSystemArtifactStore


def test_filesystem_store_copies_reads_and_hashes_artifact(tmp_path) -> None:
    intake_root = tmp_path / "intake"
    source_file = intake_root / "raw" / "video.mp4"
    source_file.parent.mkdir(parents=True)
    source_file.write_bytes(b"video")

    store = FileSystemArtifactStore(tmp_path / "durable")
    receipt = store.put_file(
        artifact_id="video_001:video",
        source_id="video_001",
        relative_path="raw/video.mp4",
        source_path=source_file,
        stored_at=datetime(2026, 8, 8, tzinfo=UTC),
    )

    assert receipt.size_bytes == 5
    assert receipt.sha256 == (
        "0cab1c9617404faf2b24e221e189ca5945813e14d3f766345b09ca13bbe28ffc"
    )
    assert store.exists("video_001", "raw/video.mp4")
    assert store.read_bytes("video_001", "raw/video.mp4") == b"video"


def test_filesystem_store_promotes_without_leaving_staging_copy(tmp_path) -> None:
    source_file = tmp_path / "intake" / "raw" / "video.mp4"
    source_file.parent.mkdir(parents=True)
    source_file.write_bytes(b"video")
    store = FileSystemArtifactStore(tmp_path / "durable")

    receipt = store.promote_file(
        artifact_id="video_002:video",
        source_id="video_002",
        relative_path="raw/video.mp4",
        source_path=source_file,
        stored_at=datetime(2026, 8, 8, tzinfo=UTC),
    )

    assert receipt.size_bytes == 5
    assert not source_file.exists()
    assert store.exists("video_002", "raw/video.mp4")
