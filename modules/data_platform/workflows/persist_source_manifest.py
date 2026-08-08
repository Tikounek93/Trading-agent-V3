"""Persist available source artifacts without interpreting their content."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from modules.source_intake.contracts.artifacts import ArtifactState
from modules.source_intake.contracts.intake import SourceManifest, SourceReadiness

from ..contracts.storage import StoredArtifact
from ..catalog.source_catalog import SourceCatalog
from ..ports.artifact_store import ArtifactStore


@dataclass(frozen=True, slots=True)
class ManifestPersistenceResult:
    manifest: SourceManifest
    stored_artifacts: tuple[StoredArtifact, ...]
    skipped_artifact_ids: tuple[str, ...]


def _prune_empty_staging(root: Path) -> None:
    if not root.exists():
        return
    for path in sorted(root.rglob("*"), key=lambda item: len(item.parts), reverse=True):
        if path.is_dir():
            try:
                path.rmdir()
            except OSError:
                pass
    try:
        root.rmdir()
    except OSError:
        pass


def persist_source_manifest(
    manifest: SourceManifest,
    artifact_root: Path,
    store: ArtifactStore,
    stored_at: datetime | None = None,
    catalog: SourceCatalog | None = None,
) -> ManifestPersistenceResult:
    """Move available artifacts from staging when the manifest is complete."""

    stored: list[StoredArtifact] = []
    skipped: list[str] = []
    if manifest.readiness is not SourceReadiness.READY:
        for artifact in manifest.artifacts:
            if artifact.state is not ArtifactState.AVAILABLE:
                skipped.append(artifact.artifact_id)
        result = ManifestPersistenceResult(
            manifest=manifest,
            stored_artifacts=(),
            skipped_artifact_ids=tuple(skipped),
        )
        if catalog is not None:
            catalog.upsert_manifest(manifest)
        return result
    for artifact in manifest.artifacts:
        if artifact.state is not ArtifactState.AVAILABLE:
            skipped.append(artifact.artifact_id)
            continue
        source_path = Path(artifact_root) / artifact.relative_path
        stored.append(
            store.promote_file(
                artifact_id=artifact.artifact_id,
                source_id=artifact.source_id,
                relative_path=artifact.relative_path,
                source_path=source_path,
                stored_at=stored_at,
            )
        )
    _prune_empty_staging(Path(artifact_root))
    result = ManifestPersistenceResult(
        manifest=manifest,
        stored_artifacts=tuple(stored),
        skipped_artifact_ids=tuple(skipped),
    )
    if catalog is not None:
        catalog.upsert_manifest(manifest, result.stored_artifacts)
    return result
