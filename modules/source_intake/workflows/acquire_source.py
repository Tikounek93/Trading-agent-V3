"""Acquisition workflow that keeps provider and storage boundaries explicit."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from ..contracts.acquisition import AcquisitionPlan, AcquisitionWorkflowResult
from ..contracts.artifacts import ArtifactKind
from ..contracts.intake import IntakeResult
from ..contracts.source import SourceRecord
from ..registry.source_registry import SourceRegistry
from ..tools.acquire_metadata import acquire_metadata
from ..tools.acquire_subtitles import acquire_subtitles
from ..tools.acquire_video import acquire_video
from ..tools.build_source_manifest import build_source_manifest
from ..tools.inspect_artifacts import inspect_artifacts


def acquire_source(
    registry: SourceRegistry,
    source: SourceRecord,
    artifact_root: Path,
    plan: AcquisitionPlan,
    inspected_at: datetime,
    downloader_factory=None,
) -> AcquisitionWorkflowResult:
    registered = registry.register(source)
    registered_source = registry.get(source.source_id)
    results = []

    if plan.download_video:
        results.append(acquire_video(registered_source, artifact_root, downloader_factory))
    if plan.fetch_metadata:
        results.append(acquire_metadata(registered_source, artifact_root, downloader_factory))
    if plan.fetch_subtitles:
        results.append(
            acquire_subtitles(
                registered_source,
                artifact_root,
                languages=plan.subtitle_languages,
                downloader_factory=downloader_factory,
            )
        )

    declared_paths = {}
    if plan.download_video:
        declared_paths[ArtifactKind.VIDEO] = "raw/video.mp4"
    if plan.fetch_metadata:
        declared_paths[ArtifactKind.METADATA] = "raw/info.json"
    artifacts = list(inspect_artifacts(registered_source, artifact_root, declared_paths))
    if plan.fetch_subtitles:
        for language in plan.subtitle_languages:
            artifacts.extend(
                inspect_artifacts(
                    registered_source,
                    artifact_root,
                    {ArtifactKind.SUBTITLE: f"raw/subtitles.{language}.vtt"},
                )
            )
    manifest = build_source_manifest(registered_source, artifacts, inspected_at)

    return AcquisitionWorkflowResult(
        intake_result=IntakeResult(manifest=manifest, registered_new_source=registered),
        acquisitions=tuple(results),
    )
