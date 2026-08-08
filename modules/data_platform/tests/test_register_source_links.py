from datetime import UTC, datetime

from modules.data_platform.catalog import SourceCatalog
from modules.data_platform.workflows import register_source_links
from modules.source_intake.registry import SourceRegistry


def test_register_source_links_populates_not_ready_catalog(tmp_path) -> None:
    result = register_source_links(
        SourceRegistry(),
        SourceCatalog(tmp_path / "catalog.sqlite3"),
        ("https://www.youtube.com/watch?v=abc_DEF12345",),
        datetime(2026, 8, 8, tzinfo=UTC),
    )

    assert result.imported_source_ids == ("youtube_abc_DEF12345",)
    [summary] = SourceCatalog(tmp_path / "catalog.sqlite3").list_sources()
    assert summary.readiness == "not_ready"
    assert summary.artifact_count == 0

