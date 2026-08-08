from datetime import UTC, datetime
import json

from modules.source_intake.contracts import (
    AcquisitionPlan,
    AcquisitionStatus,
    SourceKind,
    SourceRecord,
)
from modules.source_intake.tools.acquire_metadata import (
    acquire_metadata,
    build_metadata_options,
)
from modules.source_intake.tools.acquire_subtitles import (
    acquire_subtitles,
    build_subtitle_options,
)
from modules.source_intake.tools.acquire_video import acquire_video, build_video_download_options
from modules.source_intake.tests.fixtures import fake_factory


def _source() -> SourceRecord:
    return SourceRecord(
        source_id="video_001",
        locator="https://example.invalid/video_001",
        kind=SourceKind.VIDEO,
        registered_at=datetime(2026, 8, 8, 12, 0, tzinfo=UTC),
    )


def test_acquisition_options_keep_provider_operations_separate(tmp_path) -> None:
    video_options = build_video_download_options(tmp_path / "raw")
    metadata_options = build_metadata_options(tmp_path / "raw")
    subtitle_options = build_subtitle_options(tmp_path / "raw", ("en", "en-orig"))

    assert video_options["skip_download"] is False
    assert metadata_options["skip_download"] is True
    assert subtitle_options["writesubtitles"] is True
    assert subtitle_options["skip_download"] is True


def test_video_acquisition_writes_only_video_artifact(tmp_path) -> None:
    result = acquire_video(_source(), tmp_path, fake_factory)

    assert result.status is AcquisitionStatus.PREPARED
    assert (tmp_path / "raw" / "video.mp4").read_bytes() == b"video"
    assert [artifact.relative_path for artifact in result.artifacts] == ["raw/video.mp4"]


def test_metadata_acquisition_writes_json_without_media(tmp_path) -> None:
    result = acquire_metadata(_source(), tmp_path, fake_factory)

    assert result.status is AcquisitionStatus.PREPARED
    payload = json.loads((tmp_path / "raw" / "info.json").read_text(encoding="utf-8"))
    assert payload["title"] == "Example"
    assert not (tmp_path / "raw" / "video.mp4").exists()


def test_subtitle_acquisition_normalizes_provider_filenames(tmp_path) -> None:
    result = acquire_subtitles(_source(), tmp_path, ("en", "en-orig"), fake_factory)

    assert result.status is AcquisitionStatus.PREPARED
    assert (tmp_path / "raw" / "subtitles.en.vtt").exists()
    assert (tmp_path / "raw" / "subtitles.en-orig.vtt").exists()
    assert len(result.artifacts) == 2


def test_acquisition_plan_requires_explicit_operation() -> None:
    try:
        AcquisitionPlan()
    except ValueError as exc:
        assert "at least one" in str(exc)
    else:
        raise AssertionError("empty acquisition plan must be rejected")
