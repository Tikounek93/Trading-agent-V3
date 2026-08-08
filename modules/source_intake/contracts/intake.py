"""Manifest and workflow result contracts for source intake."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from .artifacts import ArtifactRecord, ArtifactState
from .source import SourceRecord


class SourceReadiness(str, Enum):
    NOT_READY = "not_ready"
    PARTIAL = "partial"
    READY = "ready"
    BLOCKED = "blocked"


@dataclass(frozen=True, slots=True)
class SourceManifest:
    source: SourceRecord
    artifacts: tuple[ArtifactRecord, ...]
    inspected_at: datetime
    readiness: SourceReadiness

    def __post_init__(self) -> None:
        if not isinstance(self.source, SourceRecord):
            raise TypeError("source must be SourceRecord")
        if self.inspected_at.tzinfo is None or self.inspected_at.utcoffset() is None:
            raise ValueError("inspected_at must be timezone-aware")
        if not all(isinstance(item, ArtifactRecord) for item in self.artifacts):
            raise TypeError("artifacts must contain ArtifactRecord values")
        artifact_ids = [item.artifact_id for item in self.artifacts]
        if len(artifact_ids) != len(set(artifact_ids)):
            raise ValueError("artifacts must not contain duplicate artifact ids")
        if not isinstance(self.readiness, SourceReadiness):
            raise TypeError("readiness must be SourceReadiness")


@dataclass(frozen=True, slots=True)
class IntakeResult:
    manifest: SourceManifest
    registered_new_source: bool

    def __post_init__(self) -> None:
        if not isinstance(self.manifest, SourceManifest):
            raise TypeError("manifest must be SourceManifest")
        if not isinstance(self.registered_new_source, bool):
            raise TypeError("registered_new_source must be boolean")
