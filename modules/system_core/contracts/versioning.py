"""Small semantic version value object used by v3 contracts."""

from __future__ import annotations

from dataclasses import dataclass
import re


_VERSION_RE = re.compile(r"^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$")


@dataclass(frozen=True, order=True, slots=True)
class SemanticVersion:
    """Immutable major/minor/patch version without pre-release support."""

    major: int
    minor: int
    patch: int

    def __post_init__(self) -> None:
        for name, value in (
            ("major", self.major),
            ("minor", self.minor),
            ("patch", self.patch),
        ):
            if isinstance(value, bool) or not isinstance(value, int):
                raise TypeError(f"{name} must be an integer")
            if value < 0:
                raise ValueError(f"{name} must not be negative")

    @classmethod
    def parse(cls, value: str) -> "SemanticVersion":
        if not isinstance(value, str) or _VERSION_RE.fullmatch(value) is None:
            raise ValueError("version must use MAJOR.MINOR.PATCH format")
        major, minor, patch = (int(part) for part in value.split("."))
        return cls(major, minor, patch)

    def __str__(self) -> str:
        return f"{self.major}.{self.minor}.{self.patch}"
