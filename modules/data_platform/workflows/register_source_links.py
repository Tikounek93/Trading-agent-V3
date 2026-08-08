"""Register source links in the durable catalog without downloading them."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from modules.source_intake.contracts.intake import SourceManifest, SourceReadiness
from modules.source_intake.registry import SourceRegistry
from modules.source_intake.tools.import_source_links import import_source_links

from ..catalog.source_catalog import SourceCatalog


@dataclass(frozen=True, slots=True)
class SourceCatalogImportResult:
    imported_source_ids: tuple[str, ...]
    duplicate_source_ids: tuple[str, ...]


def register_source_links(
    registry: SourceRegistry,
    catalog: SourceCatalog,
    links: tuple[str, ...],
    registered_at: datetime,
) -> SourceCatalogImportResult:
    result = import_source_links(registry, links, registered_at)
    for source in result.records:
        catalog.upsert_manifest(
            SourceManifest(
                source=source,
                artifacts=(),
                inspected_at=registered_at,
                readiness=SourceReadiness.NOT_READY,
            )
        )
    return SourceCatalogImportResult(
        imported_source_ids=tuple(source.source_id for source in result.records),
        duplicate_source_ids=result.duplicate_source_ids,
    )

