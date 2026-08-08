"""Compatibility checks for public contract versions."""

from collections.abc import Mapping

from ..contracts.versioning import SemanticVersion


class CompatibilityError(ValueError):
    """Raised when a required contract is unavailable or incompatible."""


def _is_compatible(required: SemanticVersion, available: SemanticVersion) -> bool:
    if required.major == 0 or available.major == 0:
        return required == available
    return required.major == available.major and available >= required


def assert_compatible(
    required: Mapping[str, SemanticVersion],
    available: Mapping[str, SemanticVersion],
) -> None:
    for name, required_version in required.items():
        provided_version = available.get(name)
        if provided_version is None:
            raise CompatibilityError(f"Missing required contract: {name}")
        if not _is_compatible(required_version, provided_version):
            raise CompatibilityError(
                f"Incompatible contract {name}: required {required_version}, "
                f"available {provided_version}"
            )
