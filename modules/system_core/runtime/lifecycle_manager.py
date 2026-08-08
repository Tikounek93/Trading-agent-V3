"""Explicit lifecycle operations for registered modules."""

from ..contracts.health_status import HealthStatus
from ..contracts.lifecycle import ModuleStatus
from ..registry.module_registry import ModuleRegistry, RegisteredModule


class LifecycleManager:
    def __init__(self, registry: ModuleRegistry) -> None:
        self._registry = registry

    def begin_start(self, module_id: str) -> RegisteredModule:
        return self._registry.set_status(module_id, ModuleStatus.STARTING)

    def mark_ready(self, module_id: str) -> RegisteredModule:
        return self._registry.set_status(module_id, ModuleStatus.READY)

    def mark_degraded(self, module_id: str) -> RegisteredModule:
        return self._registry.set_status(module_id, ModuleStatus.DEGRADED)

    def mark_failed(self, module_id: str) -> RegisteredModule:
        return self._registry.set_status(module_id, ModuleStatus.FAILED)

    def begin_stop(self, module_id: str) -> RegisteredModule:
        return self._registry.set_status(module_id, ModuleStatus.STOPPING)

    def mark_stopped(self, module_id: str) -> RegisteredModule:
        return self._registry.set_status(module_id, ModuleStatus.STOPPED)

    def set_health(self, module_id: str, health: HealthStatus) -> RegisteredModule:
        return self._registry.set_health(module_id, health)
