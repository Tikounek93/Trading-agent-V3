"""Explicit module dependency registry."""

from __future__ import annotations


class DependencyRegistry:
    def __init__(self) -> None:
        self._dependencies: dict[str, tuple[str, ...]] = {}

    def register(self, module_id: str, dependencies: tuple[str, ...]) -> None:
        if not module_id.strip():
            raise ValueError("module_id must not be empty")
        if module_id in dependencies:
            raise ValueError("a module cannot depend on itself")
        if len(dependencies) != len(set(dependencies)):
            raise ValueError("dependencies must not contain duplicates")
        self._dependencies[module_id] = tuple(sorted(dependencies))

    def for_module(self, module_id: str) -> tuple[str, ...]:
        return self._dependencies.get(module_id, ())

    def unresolved(self, registered_modules: set[str]) -> dict[str, tuple[str, ...]]:
        return {
            module_id: tuple(dep for dep in dependencies if dep not in registered_modules)
            for module_id, dependencies in self._dependencies.items()
            if any(dep not in registered_modules for dep in dependencies)
        }
