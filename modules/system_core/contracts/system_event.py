"""Technical system events emitted by system_core."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from types import MappingProxyType
from typing import Any, Mapping


class EventSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


@dataclass(frozen=True, slots=True)
class SystemEvent:
    event_id: str
    event_type: str
    occurred_at: datetime
    severity: EventSeverity
    module_id: str | None = None
    details: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for name in ("event_id", "event_type"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be a non-empty string")
        if self.module_id is not None and (
            not isinstance(self.module_id, str) or not self.module_id.strip()
        ):
            raise ValueError("module_id must be a non-empty string when provided")
        if self.occurred_at.tzinfo is None or self.occurred_at.utcoffset() is None:
            raise ValueError("occurred_at must be timezone-aware")
        object.__setattr__(self, "details", MappingProxyType(dict(self.details)))
