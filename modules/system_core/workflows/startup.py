"""Begin startup without claiming modules are ready prematurely."""

from ..policies.approval_policy import LiveApproval
from ..runtime.system_runtime import SystemRuntime
from ..contracts.runtime_mode import RuntimeMode


def begin_startup(
    runtime: SystemRuntime,
    mode: RuntimeMode,
    approval: LiveApproval | None = None,
) -> tuple[str, ...]:
    """Validate startup and return a dependency-safe start order.

    This workflow does not mark modules ready. Each module must be started and
    report readiness explicitly after its own initialization is complete.
    """

    runtime.set_mode(mode, approval)
    module_ids = {entry.manifest.module_id for entry in runtime.registry.all()}
    unresolved = runtime.dependencies.unresolved(module_ids)
    if unresolved:
        raise RuntimeError(f"unresolved module dependencies: {unresolved}")

    pending = {
        entry.manifest.module_id: set(entry.manifest.dependencies)
        for entry in runtime.registry.all()
    }
    order: list[str] = []
    while pending:
        ready = sorted(module_id for module_id, deps in pending.items() if not deps)
        if not ready:
            raise RuntimeError("module dependency cycle detected")
        order.extend(ready)
        for module_id in ready:
            pending.pop(module_id)
        for deps in pending.values():
            deps.difference_update(ready)
    return tuple(order)
