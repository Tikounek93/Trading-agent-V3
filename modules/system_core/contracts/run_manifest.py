"""Immutable identity of one system run."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from .runtime_mode import RuntimeMode
from .versioning import SemanticVersion


@dataclass(frozen=True, slots=True)
class ModuleVersionRecord:
    module_id: str
    version: SemanticVersion

    def __post_init__(self) -> None:
        if not isinstance(self.module_id, str) or not self.module_id.strip():
            raise ValueError("module_id must be a non-empty string")
        if not isinstance(self.version, SemanticVersion):
            raise TypeError("version must be SemanticVersion")


@dataclass(frozen=True, slots=True)
class RunManifest:
    run_id: str
    mode: RuntimeMode
    started_at: datetime
    module_versions: tuple[ModuleVersionRecord, ...]
    strategy_version: SemanticVersion | None = None
    configuration_version: SemanticVersion | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.run_id, str) or not self.run_id.strip():
            raise ValueError("run_id must be a non-empty string")
        if not isinstance(self.mode, RuntimeMode):
            raise TypeError("mode must be RuntimeMode")
        if self.started_at.tzinfo is None or self.started_at.utcoffset() is None:
            raise ValueError("started_at must be timezone-aware")
        if not all(isinstance(item, ModuleVersionRecord) for item in self.module_versions):
            raise TypeError("module_versions must contain ModuleVersionRecord values")
        module_ids = [item.module_id for item in self.module_versions]
        if len(module_ids) != len(set(module_ids)):
            raise ValueError("module_versions must not contain duplicate modules")
        for name, value in (
            ("strategy_version", self.strategy_version),
            ("configuration_version", self.configuration_version),
        ):
            if value is not None and not isinstance(value, SemanticVersion):
                raise TypeError(f"{name} must be SemanticVersion when provided")
