"""Import source links without acquiring or interpreting their content."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from urllib.parse import parse_qs, urlparse

from ..contracts.source import SourceKind, SourceRecord
from ..registry.source_registry import SourceRegistry


@dataclass(frozen=True, slots=True)
class SourceLinkImportResult:
    records: tuple[SourceRecord, ...]
    duplicate_source_ids: tuple[str, ...]


def _youtube_video_id(link: str) -> str:
    parsed = urlparse(link.strip())
    host = (parsed.hostname or "").lower()
    if host in {"youtube.com", "www.youtube.com", "m.youtube.com"}:
        video_id = parse_qs(parsed.query).get("v", [""])[0]
    elif host in {"youtu.be", "www.youtu.be"}:
        video_id = parsed.path.strip("/").split("/", 1)[0]
    else:
        video_id = ""
    allowed = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-"
    if not video_id or any(character not in allowed for character in video_id):
        raise ValueError(f"unsupported or invalid YouTube link: {link}")
    return video_id


def import_source_links(
    registry: SourceRegistry,
    links: tuple[str, ...],
    registered_at: datetime,
) -> SourceLinkImportResult:
    records: list[SourceRecord] = []
    duplicates: list[str] = []
    for raw_link in links:
        if not isinstance(raw_link, str) or not raw_link.strip():
            raise ValueError("source links must be non-empty strings")
        video_id = _youtube_video_id(raw_link)
        source = SourceRecord(
            source_id=f"youtube_{video_id}",
            locator=f"https://www.youtube.com/watch?v={video_id}",
            kind=SourceKind.VIDEO,
            registered_at=registered_at,
        )
        if registry.register(source):
            records.append(source)
        else:
            duplicates.append(source.source_id)
    return SourceLinkImportResult(tuple(records), tuple(duplicates))

