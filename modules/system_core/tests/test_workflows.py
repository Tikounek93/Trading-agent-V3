from modules.system_core.contracts import ModuleManifest, RuntimeMode, SemanticVersion
from modules.system_core.runtime import SystemRuntime
from modules.system_core.workflows import begin_startup, shutdown_modules


def _manifest(module_id: str, dependencies: tuple[str, ...] = ()) -> ModuleManifest:
    return ModuleManifest(
        module_id=module_id,
        version=SemanticVersion.parse("0.1.0"),
        description=f"{module_id} test module",
        supported_modes=frozenset({RuntimeMode.BACKTEST}),
        dependencies=dependencies,
    )


def test_startup_returns_dependency_safe_order_without_claiming_ready() -> None:
    runtime = SystemRuntime()
    runtime.register_module(_manifest("consumer", ("provider",)))
    runtime.register_module(_manifest("provider"))

    order = begin_startup(runtime, RuntimeMode.BACKTEST)

    assert order == ("provider", "consumer")
    assert all(entry.status.value == "registered" for entry in runtime.registry.all())


def test_shutdown_stops_started_modules() -> None:
    runtime = SystemRuntime()
    runtime.register_module(_manifest("sample_module"))
    runtime.set_mode(RuntimeMode.BACKTEST)
    runtime.start_module("sample_module")
    runtime.mark_module_ready("sample_module")

    assert shutdown_modules(runtime) == ("sample_module",)
    assert runtime.registry.get("sample_module").status.value == "stopped"
