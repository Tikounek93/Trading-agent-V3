"""Source identity and registration contract."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class SourceKind(str, Enum):
    VIDEO = "video"
    DOCUMENT = "document"
    NOTE = "note"
    IMAGE = "image"
    URL = "url"
    UNKNOWN = "unknown"


class SourceState(str, Enum):
    REGISTERED = "registered"
    AVAILABLE = "available"
    BLOCKED = "blocked"
    UNAVAILABLE = "unavailable"


def _text(value: str, field_name: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field_name} must not be empty")
    return normalized


def _validate_source_id(value: str) -> str:
    normalized = _text(value, "source_id")
    allowed = frozenset("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_.-")
    if any(character not in allowed for character in normalized):
        raise ValueError("source_id may contain only letters, numbers, dot, underscore and hyphen")
    return normalized


@dataclass(frozen=True, slots=True)
class SourceRecord:
    source_id: str
    locator: str
    kind: SourceKind
    registered_at: datetime
    title: str | None = None
    state: SourceState = SourceState.REGISTERED
    tags: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        object.__setattr__(self, "source_id", _validate_source_id(self.source_id))
        object.__setattr__(self, "locator", _text(self.locator, "locator"))
        if not isinstance(self.kind, SourceKind):
            raise TypeError("kind must be SourceKind")
        if not isinstance(self.state, SourceState):
            raise TypeError("state must be SourceState")
        if self.registered_at.tzinfo is None or self.registered_at.utcoffset() is None:
            raise ValueError("registered_at must be timezone-aware")
        if self.title is not None:
            object.__setattr__(self, "title", _text(self.title, "title"))
        normalized_tags = tuple(_text(tag, "tag") for tag in self.tags)
        if len(normalized_tags) != len(set(normalized_tags)):
            raise ValueError("tags must not contain duplicates")
        object.__setattr__(self, "tags", normalized_tags)
