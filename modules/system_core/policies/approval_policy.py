"""Human approval gate for live operation."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from ..contracts.runtime_mode import RuntimeMode


@dataclass(frozen=True, slots=True)
class LiveApproval:
    approval_id: str
    approved_by: str
    approved_at: datetime

    def __post_init__(self) -> None:
        for name in ("approval_id", "approved_by"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be a non-empty string")
        if self.approved_at.tzinfo is None or self.approved_at.utcoffset() is None:
            raise ValueError("approved_at must be timezone-aware")


def require_live_approval(mode: RuntimeMode, approval: LiveApproval | None) -> None:
    if mode is RuntimeMode.LIVE and approval is None:
        raise PermissionError("live mode requires explicit human approval")
