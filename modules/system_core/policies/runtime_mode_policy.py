"""Policy for selecting a mode supported by a module."""

from ..contracts.module_manifest import ModuleManifest
from ..contracts.runtime_mode import RuntimeMode


class UnsupportedRuntimeMode(ValueError):
    """Raised when a module cannot operate in the requested mode."""


class RuntimeModePolicy:
    def validate_module(self, manifest: ModuleManifest, mode: RuntimeMode) -> None:
        if mode not in manifest.supported_modes:
            raise UnsupportedRuntimeMode(
                f"{manifest.module_id} does not support {mode.value}"
            )
