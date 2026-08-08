"""Process one ready source from the SourceCatalog."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from modules.data_platform.catalog.source_catalog import SourceCatalog

from ..storage.knowledge_artifact_store import KnowledgeArtifactStore
from ..tools.validate_knowledge_artifact import validate_knowledge_artifact
from .process_source import process_source


SUBTITLE_PREFERENCES = (
    "raw/subtitles.en.vtt",
    "raw/subtitles.en-orig.vtt",
    "raw/transcript.en.vtt",
    "raw/transcript.en-orig.vtt",
    "raw/transcript.vtt",
)


def _artifact_path(artifact_root: Path, source_id: str, relative_path: str) -> Path:
    candidate = (artifact_root / source_id / relative_path).resolve()
    source_root = (artifact_root / source_id).resolve()
    if candidate != source_root and source_root not in candidate.parents:
        raise ValueError("catalog artifact path escapes the artifact root")
    return candidate


def _load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return None


def _records_from_json(value: Any, keys: tuple[str, ...]) -> list[dict[str, Any]]:
    if isinstance(value, list):
        return [dict(item) for item in value if isinstance(item, dict)]
    if isinstance(value, dict):
        for key in keys:
            nested = value.get(key)
            if isinstance(nested, list):
                return [dict(item) for item in nested if isinstance(item, dict)]
    return []


def _available_path(
    artifacts: tuple[Any, ...],
    artifact_root: Path,
    source_id: str,
    *,
    preferred_paths: tuple[str, ...] = (),
    name_fragments: tuple[str, ...] = (),
) -> Path | None:
    available = [item for item in artifacts if item.state == "available"]
    by_path = {item.relative_path: item for item in available}
    for relative_path in preferred_paths:
        if relative_path in by_path:
            return _artifact_path(artifact_root, source_id, relative_path)
    for item in available:
        normalized = item.relative_path.lower()
        if any(fragment in normalized for fragment in name_fragments):
            return _artifact_path(artifact_root, source_id, item.relative_path)
    return None


def process_catalog_source(
    source_id: str,
    catalog: SourceCatalog,
    artifact_root: Path,
    knowledge_store: KnowledgeArtifactStore,
) -> dict[str, Any]:
    """Process one catalog source without changing source or raw artifacts."""

    source = next(
        (item for item in catalog.list_source_records() if item.source_id == source_id),
        None,
    )
    if source is None:
        return {"source_id": source_id, "status": "failed", "error": "source not found"}

    artifacts = catalog.list_artifacts(source_id)
    subtitle_path = _available_path(
        artifacts,
        artifact_root,
        source_id,
        preferred_paths=SUBTITLE_PREFERENCES,
        name_fragments=("subtitle", "transcript"),
    )
    if subtitle_path is None:
        return {
            "source_id": source_id,
            "status": "blocked",
            "reason": "no available subtitle or transcript artifact",
        }

    metadata_path = _available_path(
        artifacts,
        artifact_root,
        source_id,
        name_fragments=("info.json", "metadata", "metadata.json"),
    )
    metadata = _load_json(metadata_path) if metadata_path else {}
    metadata = metadata if isinstance(metadata, dict) else {}

    frame_path = _available_path(
        artifacts,
        artifact_root,
        source_id,
        name_fragments=("frame_index", "frames.json"),
    )
    frame_index = _records_from_json(
        _load_json(frame_path) if frame_path else None,
        ("frames", "items"),
    )
    ocr_path = _available_path(
        artifacts,
        artifact_root,
        source_id,
        name_fragments=("ocr",),
    )
    ocr_records = _records_from_json(
        _load_json(ocr_path) if ocr_path else None,
        ("records", "results", "ocr", "items"),
    )

    artifact = process_source(
        source_id,
        subtitle_path,
        title=source.title or metadata.get("title"),
        duration=metadata.get("duration"),
        source_locator=(
            metadata.get("webpage_url")
            or metadata.get("original_url")
            or source.locator
        ),
        frame_index=frame_index,
        ocr_records=ocr_records,
    )
    quality = validate_knowledge_artifact(artifact)
    quality_payload = {
        "valid": quality.valid,
        "errors": list(quality.errors),
        "warnings": list(quality.warnings),
        "units_count": quality.units_count,
        "chunks_count": quality.chunks_count,
    }
    if not quality.valid:
        return {
            "source_id": source_id,
            "status": "failed",
            "reason": "knowledge artifact failed quality validation",
            "quality": quality_payload,
        }

    receipt = knowledge_store.save(source_id, artifact)
    return {
        "source_id": source_id,
        "status": "processed" if receipt.status == "stored" else receipt.status,
        "knowledge_path": receipt.relative_path,
        "history_path": receipt.history_relative_path,
        "sha256": receipt.sha256,
        "quality": quality_payload,
    }
