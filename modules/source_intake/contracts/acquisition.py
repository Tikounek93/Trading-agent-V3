"""Contracts for explicit source acquisition operations."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from .artifacts import ArtifactRecord
from .intake import IntakeResult


class AcquisitionStatus(str, Enum):
    PREPARED = "prepared"
    BLOCKED = "blocked"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class AcquisitionPlan:
    """Explicit operations requested for one source."""

    download_video: bool = False
    fetch_metadata: bool = False
    fetch_subtitles: bool = False
    subtitle_languages: tuple[str, ...] = ("en", "en-orig")

    def __post_init__(self) -> None:
        for name in ("download_video", "fetch_metadata", "fetch_subtitles"):
            if not isinstance(getattr(self, name), bool):
                raise TypeError(f"{name} must be boolean")
        if not any((self.download_video, self.fetch_metadata, self.fetch_subtitles)):
            raise ValueError("acquisition plan must request at least one operation")
        normalized = tuple(language.strip() for language in self.subtitle_languages)
        if not normalized or any(not language for language in normalized):
            raise ValueError("subtitle_languages must contain non-empty values")
        if len(normalized) != len(set(normalized)):
            raise ValueError("subtitle_languages must not contain duplicates")
        object.__setattr__(self, "subtitle_languages", normalized)


@dataclass(frozen=True, slots=True)
class AcquisitionResult:
    source_id: str
    operation: str
    status: AcquisitionStatus
    artifacts: tuple[ArtifactRecord, ...] = field(default_factory=tuple)
    message: str = ""

    def __post_init__(self) -> None:
        for name in ("source_id", "operation"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be a non-empty string")
        if not isinstance(self.status, AcquisitionStatus):
            raise TypeError("status must be AcquisitionStatus")
        if not all(isinstance(item, ArtifactRecord) for item in self.artifacts):
            raise TypeError("artifacts must contain ArtifactRecord values")


@dataclass(frozen=True, slots=True)
class AcquisitionWorkflowResult:
    intake_result: IntakeResult
    acquisitions: tuple[AcquisitionResult, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.intake_result, IntakeResult):
            raise TypeError("intake_result must be IntakeResult")
        if not all(isinstance(item, AcquisitionResult) for item in self.acquisitions):
            raise TypeError("acquisitions must contain AcquisitionResult values")
