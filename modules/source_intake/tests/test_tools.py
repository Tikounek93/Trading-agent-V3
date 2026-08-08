from datetime import UTC, datetime

from modules.source_intake.contracts import ArtifactKind, SourceKind, SourceReadiness, SourceRecord
from modules.source_intake.tools.build_source_manifest import build_source_manifest
from modules.source_intake.tools.inspect_artifacts import inspect_artifacts


def _source() -> SourceRecord:
    return SourceRecord(
        source_id="video_001",
        locator="https://example.invalid/video_001",
        kind=SourceKind.VIDEO,
        registered_at=datetime(2026, 8, 8, 12, 0, tzinfo=UTC),
    )


def test_artifact_inspection_is_read_only_and_reports_missing_files(tmp_path) -> None:
    records = inspect_artifacts(
        _source(),
        tmp_path,
        {ArtifactKind.VIDEO: "raw/video.mp4", ArtifactKind.METADATA: "raw/info.json"},
    )

    assert [record.state.value for record in records] == ["missing", "missing"]
    assert not list(tmp_path.iterdir())


def test_artifact_inspection_reports_available_file(tmp_path) -> None:
    video_path = tmp_path / "raw" / "video.mp4"
    video_path.parent.mkdir()
    video_path.write_bytes(b"video")

    records = inspect_artifacts(_source(), tmp_path, {ArtifactKind.VIDEO: "raw/video.mp4"})

    assert records[0].state.value == "available"
    assert records[0].size_bytes == 5


def test_manifest_readiness_is_derived_from_artifact_states(tmp_path) -> None:
    records = inspect_artifacts(_source(), tmp_path, {ArtifactKind.VIDEO: "raw/video.mp4"})
    manifest = build_source_manifest(
        _source(),
        records,
        datetime(2026, 8, 8, 12, 1, tzinfo=UTC),
    )

    assert manifest.readiness is SourceReadiness.PARTIAL
