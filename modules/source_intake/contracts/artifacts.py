"""Source artifact identity and local availability contract."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ArtifactKind(str, Enum):
    VIDEO = "video"
    METADATA = "metadata"
    TRANSCRIPT = "transcript"
    SUBTITLE = "subtitle"
    IMAGE = "image"
    DOCUMENT = "document"
    NOTE = "note"
    OTHER = "other"


class ArtifactState(str, Enum):
    MISSING = "missing"
    AVAILABLE = "available"
    INVALID = "invalid"


@dataclass(frozen=True, slots=True)
class ArtifactRecord:
    artifact_id: str
    source_id: str
    kind: ArtifactKind
    relative_path: str
    state: ArtifactState
    size_bytes: int | None = None

    def __post_init__(self) -> None:
        for name in ("artifact_id", "source_id", "relative_path"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be a non-empty string")
        if not isinstance(self.kind, ArtifactKind):
            raise TypeError("kind must be ArtifactKind")
        if not isinstance(self.state, ArtifactState):
            raise TypeError("state must be ArtifactState")
        path_parts = self.relative_path.replace("\\", "/").split("/")
        if self.relative_path.startswith(("/", "\\")) or ".." in path_parts:
            raise ValueError("relative_path must remain inside the selected artifact root")
        if self.size_bytes is not None:
            if isinstance(self.size_bytes, bool) or self.size_bytes < 0:
                raise ValueError("size_bytes must be a non-negative integer")
