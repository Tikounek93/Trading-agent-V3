"""Tool for checking required and available contract versions."""

from collections.abc import Mapping

from ..contracts.versioning import SemanticVersion
from ..policies.compatibility_policy import assert_compatible


def check_compatibility(
    required: Mapping[str, SemanticVersion],
    available: Mapping[str, SemanticVersion],
) -> bool:
    assert_compatible(required, available)
    return True
