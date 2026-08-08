"""Orchestrate the deterministic source-to-knowledge candidate pipeline."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

from ..tools.attach_multimodal_evidence import attach_multimodal_evidence
from ..tools.build_chunks import build_semantic_chunks
from ..tools.build_timeline import build_timeline
from ..tools.enrich_chunks import enrich_chunk
from ..tools.extract_events import extract_events
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
    frame_index: Iterable[Mapping[str, Any]] = (),
    ocr_records: Iterable[Mapping[str, Any]] = (),
) -> dict[str, Any]:
    """Create an append-only advisory artifact from a local subtitle source."""

    timeline = build_timeline(
        source_id,
        parse_vtt_subtitles(subtitle_path),
        title=title,
        duration=duration,
        source_locator=source_locator,
    )
    timeline = attach_multimodal_evidence(
        timeline,
        frame_index=frame_index,
        ocr_records=ocr_records,
    )
    timeline["segments"] = [
        {
            **segment,
            "events": extract_events(
                " ".join(
                    [
                        str(segment.get("transcript") or ""),
                        *(
                            str(item.get("text") or item.get("content") or "")
                            if isinstance(item, dict)
                            else str(item)
                            for item in segment.get("ocr_texts", [])
                        ),
                    ]
                ),
                source="transcript_or_ocr",
            ),
        }
        for segment in timeline.get("segments", [])
    ]
    chunks = [enrich_chunk(chunk) for chunk in build_semantic_chunks(timeline)]
    units = extract_knowledge_units(chunks)
    scored_units = [score_knowledge_unit(unit) for unit in units]
    summary = build_knowledge_units_summary(source_id, scored_units)
    return {
        "source_id": source_id,
        "pipeline_version": "1.0.0",
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
