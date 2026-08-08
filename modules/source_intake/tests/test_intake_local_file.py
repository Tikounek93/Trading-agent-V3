from datetime import UTC, datetime

import pytest

from modules.source_intake.contracts import ArtifactKind, SourceKind, SourceRecord
from modules.source_intake.registry import SourceRegistry
from modules.source_intake.workflows import intake_local_file


def test_intake_local_document_creates_available_artifact(tmp_path) -> None:
    source = SourceRecord(
        source_id="notes_001",
        locator="local://lesson.pdf",
        kind=SourceKind.DOCUMENT,
        registered_at=datetime(2026, 8, 8, tzinfo=UTC),
    )

    result = intake_local_file(
        SourceRegistry(),
        source,
        tmp_path,
        "lesson.pdf",
        b"document content",
        datetime(2026, 8, 8, 12, 1, tzinfo=UTC),
    )

    assert result.artifact.kind is ArtifactKind.DOCUMENT
    assert result.intake_result.manifest.readiness.value == "ready"
    assert (tmp_path / "raw" / "lesson.pdf").read_bytes() == b"document content"


def test_intake_local_file_rejects_url_source_kind(tmp_path) -> None:
    source = SourceRecord(
        source_id="link_001",
        locator="https://example.invalid",
        kind=SourceKind.URL,
        registered_at=datetime(2026, 8, 8, tzinfo=UTC),
    )

    with pytest.raises(ValueError):
        intake_local_file(
            SourceRegistry(),
            source,
            tmp_path,
            "source.txt",
            b"content",
            datetime(2026, 8, 8, tzinfo=UTC),
        )

