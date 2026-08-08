"""Stable data shapes exchanged inside the knowledge-processing pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class TimelineSegment:
    start: float
    end: float
    transcript: str
    frame_paths: tuple[str, ...] = ()
    ocr_texts: tuple[dict[str, Any], ...] = ()
    events: tuple[dict[str, Any], ...] = ()


@dataclass(frozen=True, slots=True)
class Timeline:
    source_id: str
    title: str | None
    duration: float | None
    source_locator: str | None
    segments: tuple[TimelineSegment, ...] = ()


@dataclass(frozen=True, slots=True)
class KnowledgeArtifact:
    source_id: str
    pipeline_version: str
    timeline: dict[str, Any]
    chunks: tuple[dict[str, Any], ...] = field(default_factory=tuple)
    knowledge_units: tuple[dict[str, Any], ...] = field(default_factory=tuple)
    append_only: bool = True
    raw_data_modified: bool = False
