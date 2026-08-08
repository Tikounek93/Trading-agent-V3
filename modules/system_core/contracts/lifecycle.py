"""Module lifecycle states and allowed transitions."""

from __future__ import annotations

from enum import Enum


class ModuleStatus(str, Enum):
    REGISTERED = "registered"
    STARTING = "starting"
    READY = "ready"
    DEGRADED = "degraded"
    FAILED = "failed"
    STOPPING = "stopping"
    STOPPED = "stopped"


_ALLOWED_TRANSITIONS: dict[ModuleStatus, frozenset[ModuleStatus]] = {
    ModuleStatus.REGISTERED: frozenset({ModuleStatus.STARTING, ModuleStatus.STOPPED}),
    ModuleStatus.STARTING: frozenset(
        {ModuleStatus.READY, ModuleStatus.DEGRADED, ModuleStatus.FAILED, ModuleStatus.STOPPING}
    ),
    ModuleStatus.READY: frozenset(
        {ModuleStatus.DEGRADED, ModuleStatus.FAILED, ModuleStatus.STOPPING}
    ),
    ModuleStatus.DEGRADED: frozenset(
        {ModuleStatus.READY, ModuleStatus.FAILED, ModuleStatus.STOPPING}
    ),
    ModuleStatus.FAILED: frozenset({ModuleStatus.STARTING, ModuleStatus.STOPPING}),
    ModuleStatus.STOPPING: frozenset({ModuleStatus.STOPPED, ModuleStatus.FAILED}),
    ModuleStatus.STOPPED: frozenset({ModuleStatus.STARTING}),
}


class InvalidLifecycleTransition(ValueError):
    """Raised when a module tries to make an unsafe state transition."""


def can_transition(current: ModuleStatus, target: ModuleStatus) -> bool:
    return target in _ALLOWED_TRANSITIONS.get(current, frozenset())


def assert_transition(current: ModuleStatus, target: ModuleStatus) -> None:
    if not can_transition(current, target):
        raise InvalidLifecycleTransition(
            f"Cannot transition module from {current.value} to {target.value}"
        )
