"""In-memory registries used by the first system_core release."""

from .dependency_registry import DependencyRegistry
from .module_registry import ModuleRegistry, RegisteredModule

__all__ = ["DependencyRegistry", "ModuleRegistry", "RegisteredModule"]
