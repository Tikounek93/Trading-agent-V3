"""Tool for registering one explicit source."""

from ..contracts.source import SourceRecord
from ..registry.source_registry import SourceRegistry


def register_source(registry: SourceRegistry, source: SourceRecord) -> bool:
    return registry.register(source)
