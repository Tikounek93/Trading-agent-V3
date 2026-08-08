"""Small in-memory system runtime for system_core v0.1.0."""

from __future__ import annotations

from datetime import datetime

from ..contracts.health_status import HealthStatus
from ..contracts.lifecycle import ModuleStatus
from ..contracts.module_manifest import ModuleManifest
from ..contracts.run_manifest import ModuleVersionRecord, RunManifest
from ..contracts.runtime_mode import RuntimeMode
from ..contracts.system_event import SystemEvent
from ..contracts.versioning import SemanticVersion
from ..policies.approval_policy import LiveApproval, require_live_approval
from ..policies.runtime_mode_policy import RuntimeModePolicy
from ..registry.dependency_registry import DependencyRegistry
from ..registry.module_registry import ModuleRegistry
from .health_state import HealthStateStore
from .lifecycle_manager import LifecycleManager


class SystemRuntime:
    """Coordinates basic system state without owning business decisions."""

    def __init__(self) -> None:
        self.registry = ModuleRegistry()
        self.dependencies = DependencyRegistry()
        self.health = HealthStateStore()
        self.lifecycle = LifecycleManager(self.registry)
        self.mode: RuntimeMode | None = None
        self._events: list[SystemEvent] = []

    def register_module(self, manifest: ModuleManifest) -> None:
        self.registry.register(manifest)
        self.dependencies.register(manifest.module_id, manifest.dependencies)

    def set_mode(self, mode: RuntimeMode, approval: LiveApproval | None = None) -> None:
        require_live_approval(mode, approval)
        policy = RuntimeModePolicy()
        for entry in self.registry.all():
            policy.validate_module(entry.manifest, mode)
        self.mode = mode

    def start_module(self, module_id: str) -> None:
        if self.mode is None:
            raise RuntimeError("runtime mode must be selected before starting modules")
        entry = self.registry.get(module_id)
        RuntimeModePolicy().validate_module(entry.manifest, self.mode)
        for dependency in entry.manifest.dependencies:
            dependency_entry = self.registry.get(dependency)
            if dependency_entry.status is not ModuleStatus.READY:
                raise RuntimeError(f"dependency is not ready: {dependency}")
        self.lifecycle.begin_start(module_id)

    def mark_module_ready(self, module_id: str) -> None:
        self.lifecycle.mark_ready(module_id)

    def stop_module(self, module_id: str) -> None:
        self.lifecycle.begin_stop(module_id)
        self.lifecycle.mark_stopped(module_id)

    def update_health(self, module_id: str, status: HealthStatus) -> None:
        self.lifecycle.set_health(module_id, status)
        self.health.update(module_id, status)

    def record_event(self, event: SystemEvent) -> None:
        self._events.append(event)

    @property
    def events(self) -> tuple[SystemEvent, ...]:
        return tuple(self._events)

    def create_run_manifest(
        self,
        run_id: str,
        started_at: datetime,
        strategy_version: SemanticVersion | None = None,
        configuration_version: SemanticVersion | None = None,
    ) -> RunManifest:
        if self.mode is None:
            raise RuntimeError("runtime mode must be selected before creating a run")
        return RunManifest(
            run_id=run_id,
            mode=self.mode,
            started_at=started_at,
            module_versions=tuple(
                ModuleVersionRecord(entry.manifest.module_id, entry.manifest.version)
                for entry in self.registry.all()
            ),
            strategy_version=strategy_version,
            configuration_version=configuration_version,
        )
