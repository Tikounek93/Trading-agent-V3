from datetime import UTC, datetime

import pytest

from modules.source_intake.contracts import SourceKind
from modules.source_intake.registry import SourceRegistry
from modules.source_intake.tools import import_source_links


def test_import_source_links_registers_urls_only() -> None:
    result = import_source_links(
        SourceRegistry(),
        (
            "https://www.youtube.com/watch?v=abc_DEF12345",
            "https://youtu.be/xyz-XYZ12345",
        ),
        datetime(2026, 8, 8, tzinfo=UTC),
    )

    assert [item.source_id for item in result.records] == [
        "youtube_abc_DEF12345",
        "youtube_xyz-XYZ12345",
    ]
    assert all(item.kind is SourceKind.VIDEO for item in result.records)
    assert all(item.title is None for item in result.records)


def test_import_source_links_rejects_non_youtube_url() -> None:
    with pytest.raises(ValueError):
        import_source_links(
            SourceRegistry(),
            ("https://example.invalid/video",),
            datetime(2026, 8, 8, tzinfo=UTC),
        )

