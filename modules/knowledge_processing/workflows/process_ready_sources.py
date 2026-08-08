"""Batch workflow for ready sources in the SourceCatalog."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from modules.data_platform.catalog.source_catalog import SourceCatalog

from ..storage.knowledge_artifact_store import KnowledgeArtifactStore
from .process_catalog_source import process_catalog_source


def process_ready_sources(
    catalog: SourceCatalog,
    artifact_root: Path,
    knowledge_store: KnowledgeArtifactStore,
) -> dict[str, Any]:
    """Process all ready sources and keep failures isolated per source."""

    results: list[dict[str, Any]] = []
    for source in catalog.list_sources():
        if source.readiness != "ready":
            continue
        try:
            result = process_catalog_source(
                source.source_id,
                catalog,
                artifact_root,
                knowledge_store,
            )
        except (OSError, ValueError, TypeError) as exc:
            result = {
                "source_id": source.source_id,
                "status": "failed",
                "error": str(exc),
            }
        results.append(result)

    counts = {"processed": 0, "already_current": 0, "blocked": 0, "failed": 0}
    for result in results:
        status = result.get("status")
        if status in counts:
            counts[status] += 1
    return {
        "ready_source_count": len(results),
        "counts": counts,
        "results": results,
    }
