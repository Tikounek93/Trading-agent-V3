"""Coordinator agent for explicit source acquisition plans."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Callable

from ..contracts.acquisition import AcquisitionPlan, AcquisitionWorkflowResult
from ..contracts.source import SourceRecord
from ..registry.source_registry import SourceRegistry
from ..workflows.acquire_source import acquire_source


class SourceAcquisitionAgent:
    """Coordinate source acquisition without interpreting the acquired content."""

    def __init__(self, registry: SourceRegistry, downloader_factory: Callable | None = None) -> None:
        self.registry = registry
        self.downloader_factory = downloader_factory

    def run(
        self,
        source: SourceRecord,
        artifact_root: Path,
        plan: AcquisitionPlan,
        inspected_at: datetime | None = None,
    ) -> AcquisitionWorkflowResult:
        return acquire_source(
            registry=self.registry,
            source=source,
            artifact_root=artifact_root,
            plan=plan,
            inspected_at=inspected_at or datetime.now(UTC),
            downloader_factory=self.downloader_factory,
        )

