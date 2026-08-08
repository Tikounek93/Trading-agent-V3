"""Read-only health projection for the current runtime."""

from ..contracts.health_status import HealthStatus
from ..runtime.system_runtime import SystemRuntime


def collect_health(runtime: SystemRuntime) -> dict[str, HealthStatus | None]:
    return {
        entry.manifest.module_id: entry.health
        for entry in runtime.registry.all()
    }
