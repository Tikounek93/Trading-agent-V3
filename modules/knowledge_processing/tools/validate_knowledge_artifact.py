"""Quality and boundary checks for persisted advisory knowledge."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


FORBIDDEN_KEY_FRAGMENTS = (
    "approval",
    "approved",
    "execute",
    "execution",
    "broker",
    "activate_strategy",
    "strategy_mutation",
    "submit_order",
)


@dataclass(frozen=True, slots=True)
class ValidationReport:
    valid: bool
    errors: tuple[str, ...]
    warnings: tuple[str, ...]
    units_count: int
    chunks_count: int


def validate_knowledge_artifact(artifact: dict[str, Any]) -> ValidationReport:
    errors: list[str] = []
    warnings: list[str] = []
    if not artifact.get("source_id"):
        errors.append("source_id is missing")
    if artifact.get("append_only") is not True:
        errors.append("append_only must be true")
    if artifact.get("raw_data_modified") is not False:
        errors.append("raw_data_modified must be false")

    timeline = artifact.get("timeline")
    chunks = artifact.get("chunks")
    units = artifact.get("knowledge_units")
    if not isinstance(timeline, dict) or not isinstance(timeline.get("segments"), list):
        errors.append("timeline.segments must be a list")
    if not isinstance(chunks, list):
        errors.append("chunks must be a list")
    if not isinstance(units, list):
        errors.append("knowledge_units must be a list")

    if isinstance(timeline, dict) and isinstance(timeline.get("segments"), list):
        previous_start = -1.0
        for index, segment in enumerate(timeline["segments"]):
            try:
                start = float(segment["start"])
                end = float(segment["end"])
            except (KeyError, TypeError, ValueError):
                errors.append(f"timeline segment {index} has invalid timing")
                continue
            if start < previous_start or end < start:
                errors.append(f"timeline segment {index} is out of order")
            previous_start = start

    chunk_ids = set()
    if isinstance(chunks, list):
        for index, chunk in enumerate(chunks):
            chunk_id = chunk.get("chunk_id") if isinstance(chunk, dict) else None
            if not chunk_id:
                errors.append(f"chunk {index} has no chunk_id")
            else:
                chunk_ids.add(chunk_id)

    if isinstance(units, list):
        for index, unit in enumerate(units):
            if not isinstance(unit, dict):
                errors.append(f"knowledge unit {index} is not an object")
                continue
            for key in (
                "unit_id",
                "source_chunk_id",
                "text",
                "concepts",
                "setup_stages",
                "knowledge_score",
                "relevance",
            ):
                if key not in unit:
                    errors.append(f"knowledge unit {index} is missing {key}")
            source_chunk_id = unit.get("source_chunk_id")
            if source_chunk_id and source_chunk_id not in chunk_ids:
                errors.append(f"knowledge unit {index} references an unknown chunk")

    keys = set(artifact)
    if isinstance(units, list):
        keys.update(key for unit in units if isinstance(unit, dict) for key in unit)
    forbidden = [
        key
        for key in keys
        if any(fragment in key.lower() for fragment in FORBIDDEN_KEY_FRAGMENTS)
    ]
    if forbidden:
        errors.append(f"forbidden authority fields present: {', '.join(sorted(forbidden))}")
    if isinstance(units, list) and not units:
        warnings.append("no knowledge units were extracted")

    return ValidationReport(
        valid=not errors,
        errors=tuple(errors),
        warnings=tuple(warnings),
        units_count=len(units) if isinstance(units, list) else 0,
        chunks_count=len(chunks) if isinstance(chunks, list) else 0,
    )
