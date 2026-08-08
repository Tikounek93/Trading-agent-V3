from datetime import UTC, datetime

from modules.source_intake.contracts import (
    AcquisitionPlan,
    AcquisitionStatus,
    ArtifactKind,
    SourceKind,
    SourceReadiness,
    SourceRecord,
)
from modules.source_intake.registry import SourceRegistry
from modules.source_intake.workflows import acquire_source
from modules.source_intake.tests.fixtures import fake_factory


def test_acquisition_workflow_runs_selected_operations_and_builds_manifest(tmp_path) -> None:
    source = SourceRecord(
        source_id="video_001",
        locator="https://example.invalid/video_001",
        kind=SourceKind.VIDEO,
        registered_at=datetime(2026, 8, 8, 12, 0, tzinfo=UTC),
    )

    result = acquire_source(
        SourceRegistry(),
        source,
        tmp_path,
        AcquisitionPlan(download_video=True, fetch_metadata=True, fetch_subtitles=True),
        datetime(2026, 8, 8, 12, 1, tzinfo=UTC),
        fake_factory,
    )

    assert [item.status for item in result.acquisitions] == [
        AcquisitionStatus.PREPARED,
        AcquisitionStatus.PREPARED,
        AcquisitionStatus.PREPARED,
    ]
    assert result.intake_result.manifest.readiness is SourceReadiness.READY
    assert {item.kind for item in result.intake_result.manifest.artifacts} == {
        ArtifactKind.VIDEO,
        ArtifactKind.METADATA,
        ArtifactKind.SUBTITLE,
    }


def test_acquisition_workflow_can_fetch_metadata_without_video(tmp_path) -> None:
    source = SourceRecord(
        source_id="video_001",
        locator="https://example.invalid/video_001",
        kind=SourceKind.VIDEO,
        registered_at=datetime(2026, 8, 8, 12, 0, tzinfo=UTC),
    )

    result = acquire_source(
        SourceRegistry(),
        source,
        tmp_path,
        AcquisitionPlan(fetch_metadata=True),
        datetime(2026, 8, 8, 12, 1, tzinfo=UTC),
        fake_factory,
    )

    assert result.intake_result.manifest.readiness is SourceReadiness.READY
    assert not (tmp_path / "raw" / "video.mp4").exists()
