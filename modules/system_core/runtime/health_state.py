"""In-memory health state for the first system_core release."""

from __future__ import annotations

from ..contracts.health_status import HealthStatus


class HealthStateStore:
    def __init__(self) -> None:
        self._states: dict[str, HealthStatus] = {}

    def update(self, module_id: str, status: HealthStatus) -> None:
        self._states[module_id] = status

    def get(self, module_id: str) -> HealthStatus | None:
        return self._states.get(module_id)

    def all(self) -> dict[str, HealthStatus]:
        return dict(self._states)
