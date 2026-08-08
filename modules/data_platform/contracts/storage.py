"""Contracts for durable artifact storage."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


def _source_id(value: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("source_id must be a non-empty string")
    normalized = value.strip()
    allowed = frozenset(
        "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_.-"
    )
    if any(character not in allowed for character in normalized):
        raise ValueError("source_id contains an unsafe character")
    return normalized


def _relative_path(value: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("relative_path must be a non-empty string")
    normalized = value.replace("\\", "/")
    parts = normalized.split("/")
    if normalized.startswith("/") or ".." in parts or any(not part for part in parts):
        raise ValueError("relative_path must remain inside the storage root")
    return normalized


@dataclass(frozen=True, slots=True)
class StorageKey:
    source_id: str
    relative_path: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "source_id", _source_id(self.source_id))
        object.__setattr__(self, "relative_path", _relative_path(self.relative_path))


@dataclass(frozen=True, slots=True)
class StoredArtifact:
    artifact_id: str
    source_id: str
    relative_path: str
    size_bytes: int
    sha256: str
    stored_at: datetime

    def __post_init__(self) -> None:
        if not isinstance(self.artifact_id, str) or not self.artifact_id.strip():
            raise ValueError("artifact_id must be a non-empty string")
        key = StorageKey(self.source_id, self.relative_path)
        object.__setattr__(self, "source_id", key.source_id)
        object.__setattr__(self, "relative_path", key.relative_path)
        if isinstance(self.size_bytes, bool) or self.size_bytes < 0:
            raise ValueError("size_bytes must be a non-negative integer")
        if not isinstance(self.sha256, str) or len(self.sha256) != 64:
            raise ValueError("sha256 must be a 64-character hexadecimal digest")
        try:
            int(self.sha256, 16)
        except ValueError as exc:
            raise ValueError("sha256 must be hexadecimal") from exc
        if self.stored_at.tzinfo is None or self.stored_at.utcoffset() is None:
            raise ValueError("stored_at must be timezone-aware")

