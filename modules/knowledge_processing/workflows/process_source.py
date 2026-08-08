"""Orchestrate the deterministic source-to-knowledge candidate pipeline."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ..tools.build_chunks import build_semantic_chunks
from ..tools.build_timeline import build_timeline
from ..tools.enrich_chunks import enrich_chunk
from ..tools.extract_knowledge_units import (
    build_knowledge_units_summary,
    extract_knowledge_units,
)
from ..tools.parse_vtt import parse_vtt_subtitles
from ..tools.score_knowledge_units import score_knowledge_unit


def process_source(
    source_id: str,
    subtitle_path: str | Path,
    *,
    title: str | None = None,
    duration: float | None = None,
    source_locator: str | None = None,
) -> dict[str, Any]:
    """Create an append-only advisory artifact from a local subtitle source."""

    timeline = build_timeline(
        source_id,
        parse_vtt_subtitles(subtitle_path),
        title=title,
        duration=duration,
        source_locator=source_locator,
    )
    chunks = [enrich_chunk(chunk) for chunk in build_semantic_chunks(timeline)]
    units = extract_knowledge_units(chunks)
    scored_units = [score_knowledge_unit(unit) for unit in units]
    summary = build_knowledge_units_summary(source_id, scored_units)
    return {
        "source_id": source_id,
        "pipeline_version": "0.1.0",
        "append_only": True,
        "raw_data_modified": False,
        "timeline": timeline,
        "chunks": chunks,
        "units_count": summary["units_count"],
        "unit_type_counts": summary["unit_type_counts"],
        "concept_counts": summary["concept_counts"],
        "stage_counts": summary["stage_counts"],
        "knowledge_units": scored_units,
    }
