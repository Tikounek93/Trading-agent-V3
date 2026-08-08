"""Controlled shutdown workflow."""

from ..contracts.lifecycle import ModuleStatus
from ..runtime.system_runtime import SystemRuntime


def shutdown_modules(runtime: SystemRuntime) -> tuple[str, ...]:
    stopped: list[str] = []
    for entry in reversed(runtime.registry.all()):
        if entry.status in {
            ModuleStatus.STARTING,
            ModuleStatus.READY,
            ModuleStatus.DEGRADED,
            ModuleStatus.FAILED,
        }:
            runtime.stop_module(entry.manifest.module_id)
            stopped.append(entry.manifest.module_id)
    return tuple(stopped)
