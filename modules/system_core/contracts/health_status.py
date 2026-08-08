"""Health result returned by system modules."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from types import MappingProxyType
from typing import Any, Mapping


class HealthState(str, Enum):
    UNKNOWN = "unknown"
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


@dataclass(frozen=True, slots=True)
class HealthStatus:
    state: HealthState
    checked_at: datetime
    message: str = ""
    details: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.checked_at.tzinfo is None or self.checked_at.utcoffset() is None:
            raise ValueError("checked_at must be timezone-aware")
        if not isinstance(self.message, str):
            raise TypeError("message must be a string")
        copied = dict(self.details)
        if not all(isinstance(key, str) and key.strip() for key in copied):
            raise ValueError("health detail keys must be non-empty strings")
        object.__setattr__(self, "details", MappingProxyType(copied))
