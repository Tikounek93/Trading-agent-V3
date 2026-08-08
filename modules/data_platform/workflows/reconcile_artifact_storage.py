"""Reconcile existing catalog storage after switching to promotion semantics."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from modules.source_intake.contracts.artifacts import ArtifactKind, ArtifactRecord, ArtifactState
from modules.source_intake.contracts.intake import SourceManifest, SourceReadiness

from ..catalog import SourceCatalog
from ..storage import FileSystemArtifactStore
from .persist_source_manifest import persist_source_manifest


@dataclass(frozen=True, slots=True)
class StorageReconciliationResult:
    promoted_source_ids: tuple[str, ...]
    staging_source_ids: tuple[str, ...]
    removed_duplicate_count: int


def reconcile_artifact_storage(
    catalog: SourceCatalog,
    staging_root: Path,
    store: FileSystemArtifactStore,
) -> StorageReconciliationResult:
    """Move complete sources and remove durable copies for incomplete sources."""

    summaries = {item.source_id: item for item in catalog.list_sources()}
    promoted: list[str] = []
    staging: list[str] = []
    removed = 0
    for source in catalog.list_source_records():
        summary = summaries[source.source_id]
        artifacts = tuple(
            ArtifactRecord(
                artifact_id=item.artifact_id,
                source_id=source.source_id,
                kind=ArtifactKind(item.kind),
                relative_path=item.relative_path,
                state=ArtifactState(item.state),
                size_bytes=item.size_bytes,
            )
            for item in catalog.list_artifacts(source.source_id)
        )
        manifest = SourceManifest(
            source=source,
            artifacts=artifacts,
            inspected_at=summary.inspected_at,
            readiness=SourceReadiness(summary.readiness),
        )
        if manifest.readiness is SourceReadiness.READY:
            persist_source_manifest(
                manifest,
                Path(staging_root) / source.source_id,
                store,
            )
            promoted.append(source.source_id)
            continue
        staging.append(source.source_id)
        for artifact in artifacts:
            if artifact.state is ArtifactState.AVAILABLE and store.remove_file(
                source.source_id,
                artifact.relative_path,
            ):
                removed += 1
        # Keep the catalog aligned with the staging-only state after removing
        # any stale durable-storage receipt.
        catalog.upsert_manifest(manifest)
    return StorageReconciliationResult(
        promoted_source_ids=tuple(promoted),
        staging_source_ids=tuple(staging),
        removed_duplicate_count=removed,
    )
