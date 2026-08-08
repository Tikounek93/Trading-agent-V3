"""Registry of explicitly registered knowledge sources."""

from __future__ import annotations

from ..contracts.source import SourceRecord


class DuplicateSourceError(ValueError):
    """Raised when one source id is registered with conflicting data."""


class SourceRegistry:
    def __init__(self) -> None:
        self._sources: dict[str, SourceRecord] = {}

    def register(self, source: SourceRecord) -> bool:
        existing = self._sources.get(source.source_id)
        if existing is not None:
            if (existing.locator, existing.kind) != (source.locator, source.kind):
                raise DuplicateSourceError(source.source_id)
            return False
        self._sources[source.source_id] = source
        return True

    def get(self, source_id: str) -> SourceRecord:
        try:
            return self._sources[source_id]
        except KeyError as exc:
            raise KeyError(f"Unknown source: {source_id}") from exc

    def all(self) -> tuple[SourceRecord, ...]:
        return tuple(self._sources[key] for key in sorted(self._sources))
