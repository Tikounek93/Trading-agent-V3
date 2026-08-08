from datetime import UTC, datetime

import pytest

from modules.system_core.contracts import (
    HealthState,
    HealthStatus,
    ModuleManifest,
    ModuleStatus,
    RuntimeMode,
    SemanticVersion,
)
from modules.system_core.runtime import SystemRuntime


def _manifest(module_id: str, dependencies: tuple[str, ...] = ()) -> ModuleManifest:
    return ModuleManifest(
        module_id=module_id,
        version=SemanticVersion.parse("0.1.0"),
        description=f"{module_id} test module",
        supported_modes=frozenset({RuntimeMode.BACKTEST, RuntimeMode.PAPER}),
        dependencies=dependencies,
    )


def test_runtime_registers_module_and_requires_explicit_readiness() -> None:
    runtime = SystemRuntime()
    runtime.register_module(_manifest("sample_module"))
    runtime.set_mode(RuntimeMode.BACKTEST)

    runtime.start_module("sample_module")
    assert runtime.registry.get("sample_module").status is ModuleStatus.STARTING

    runtime.mark_module_ready("sample_module")
    assert runtime.registry.get("sample_module").status is ModuleStatus.READY


def test_runtime_blocks_module_until_dependency_is_ready() -> None:
    runtime = SystemRuntime()
    runtime.register_module(_manifest("provider"))
    runtime.register_module(_manifest("consumer", ("provider",)))
    runtime.set_mode(RuntimeMode.BACKTEST)

    with pytest.raises(RuntimeError, match="dependency is not ready"):
        runtime.start_module("consumer")


def test_runtime_records_health_and_builds_run_manifest() -> None:
    runtime = SystemRuntime()
    runtime.register_module(_manifest("sample_module"))
    runtime.set_mode(RuntimeMode.BACKTEST)
    checked_at = datetime(2026, 8, 7, 12, 0, tzinfo=UTC)
    runtime.update_health(
        "sample_module",
        HealthStatus(HealthState.HEALTHY, checked_at, "ready"),
    )

    run_manifest = runtime.create_run_manifest("run-001", checked_at)

    assert run_manifest.run_id == "run-001"
    assert run_manifest.module_versions[0].module_id == "sample_module"
    assert runtime.health.get("sample_module").state is HealthState.HEALTHY
