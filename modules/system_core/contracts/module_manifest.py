"""Description of a module and the contracts it provides or requires."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable

from .runtime_mode import RuntimeMode
from .versioning import SemanticVersion


def _text(value: str, field_name: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field_name} must not be empty")
    return normalized


def _unique_text(values: Iterable[str], field_name: str) -> tuple[str, ...]:
    normalized = tuple(_text(value, field_name) for value in values)
    if len(normalized) != len(set(normalized)):
        raise ValueError(f"{field_name} must not contain duplicates")
    return normalized


@dataclass(frozen=True, slots=True)
class ContractDeclaration:
    name: str
    version: SemanticVersion

    def __post_init__(self) -> None:
        object.__setattr__(self, "name", _text(self.name, "contract name"))
        if not isinstance(self.version, SemanticVersion):
            raise TypeError("contract version must be SemanticVersion")


@dataclass(frozen=True, slots=True)
class ModuleManifest:
    module_id: str
    version: SemanticVersion
    description: str
    supported_modes: frozenset[RuntimeMode]
    dependencies: tuple[str, ...] = ()
    required_contracts: tuple[ContractDeclaration, ...] = ()
    provided_contracts: tuple[ContractDeclaration, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "module_id", _text(self.module_id, "module_id"))
        object.__setattr__(self, "description", _text(self.description, "description"))
        if not isinstance(self.version, SemanticVersion):
            raise TypeError("module version must be SemanticVersion")
        if not self.supported_modes:
            raise ValueError("supported_modes must not be empty")
        if not all(isinstance(mode, RuntimeMode) for mode in self.supported_modes):
            raise TypeError("supported_modes must contain RuntimeMode values")
        object.__setattr__(self, "dependencies", _unique_text(self.dependencies, "dependencies"))
        self._validate_contracts(self.required_contracts, "required_contracts")
        self._validate_contracts(self.provided_contracts, "provided_contracts")

    @staticmethod
    def _validate_contracts(
        contracts: tuple[ContractDeclaration, ...],
        field_name: str,
    ) -> None:
        if not all(isinstance(item, ContractDeclaration) for item in contracts):
            raise TypeError(f"{field_name} must contain ContractDeclaration values")
        names = [item.name for item in contracts]
        if len(names) != len(set(names)):
            raise ValueError(f"{field_name} must not contain duplicate contract names")

    def provides(self, contract_name: str) -> ContractDeclaration | None:
        return next((item for item in self.provided_contracts if item.name == contract_name), None)
