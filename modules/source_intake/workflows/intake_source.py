"""Minimal source intake workflow for v0.1.0."""

from datetime import datetime
from pathlib import Path
from typing import Mapping

from ..contracts.artifacts import ArtifactKind
from ..contracts.intake import IntakeResult
from ..contracts.source import SourceRecord
from ..registry.source_registry import SourceRegistry
from ..tools.build_source_manifest import build_source_manifest
from ..tools.inspect_artifacts import inspect_artifacts


def intake_source(
    registry: SourceRegistry,
    source: SourceRecord,
    artifact_root: Path,
    declared_paths: Mapping[ArtifactKind, str],
    inspected_at: datetime,
) -> IntakeResult:
    registered_new_source = registry.register(source)
    registered_source = registry.get(source.source_id)
    artifacts = inspect_artifacts(registered_source, artifact_root, declared_paths)
    manifest = build_source_manifest(registered_source, artifacts, inspected_at)
    return IntakeResult(
        manifest=manifest,
        registered_new_source=registered_new_source,
    )
