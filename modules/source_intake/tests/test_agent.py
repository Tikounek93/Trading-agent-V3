from datetime import UTC, datetime

from modules.source_intake.agents import SourceAcquisitionAgent
from modules.source_intake.contracts import AcquisitionPlan, SourceKind, SourceRecord
from modules.source_intake.registry import SourceRegistry
from modules.source_intake.tests.fixtures import fake_factory


def test_source_acquisition_agent_coordinates_selected_tools(tmp_path) -> None:
    source = SourceRecord(
        source_id="video_001",
        locator="https://example.invalid/video_001",
        kind=SourceKind.VIDEO,
        registered_at=datetime(2026, 8, 8, 12, 0, tzinfo=UTC),
    )

    result = SourceAcquisitionAgent(SourceRegistry(), fake_factory).run(
        source,
        tmp_path,
        AcquisitionPlan(fetch_metadata=True),
        inspected_at=datetime(2026, 8, 8, 12, 1, tzinfo=UTC),
    )

    assert result.acquisitions[0].operation == "fetch_metadata"
    assert result.intake_result.manifest.readiness.value == "ready"

