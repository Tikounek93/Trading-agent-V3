"""Registry for module manifests and their current runtime state."""

from __future__ import annotations

from dataclasses import dataclass

from ..contracts.health_status import HealthStatus
from ..contracts.lifecycle import ModuleStatus, assert_transition
from ..contracts.module_manifest import ModuleManifest


class DuplicateModuleError(ValueError):
    """Raised when a module is registered more than once."""


class UnknownModuleError(KeyError):
    """Raised when a caller references an unregistered module."""


@dataclass(frozen=True, slots=True)
class RegisteredModule:
    manifest: ModuleManifest
    status: ModuleStatus = ModuleStatus.REGISTERED
    health: HealthStatus | None = None


class ModuleRegistry:
    """Small in-memory registry; persistence belongs to data_platform later."""

    def __init__(self) -> None:
        self._entries: dict[str, RegisteredModule] = {}

    def register(self, manifest: ModuleManifest) -> RegisteredModule:
        if manifest.module_id in self._entries:
            raise DuplicateModuleError(manifest.module_id)
        entry = RegisteredModule(manifest=manifest)
        self._entries[manifest.module_id] = entry
        return entry

    def get(self, module_id: str) -> RegisteredModule:
        try:
            return self._entries[module_id]
        except KeyError as exc:
            raise UnknownModuleError(module_id) from exc

    def all(self) -> tuple[RegisteredModule, ...]:
        return tuple(self._entries[key] for key in sorted(self._entries))

    def set_status(self, module_id: str, target: ModuleStatus) -> RegisteredModule:
        entry = self.get(module_id)
        assert_transition(entry.status, target)
        updated = RegisteredModule(
            manifest=entry.manifest,
            status=target,
            health=entry.health,
        )
        self._entries[module_id] = updated
        return updated

    def set_health(self, module_id: str, health: HealthStatus) -> RegisteredModule:
        entry = self.get(module_id)
        updated = RegisteredModule(
            manifest=entry.manifest,
            status=entry.status,
            health=health,
        )
        self._entries[module_id] = updated
        return updated
