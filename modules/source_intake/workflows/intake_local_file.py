"""Register and store one locally supplied source file."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from ..contracts.artifacts import ArtifactKind, ArtifactRecord, ArtifactState
from ..contracts.intake import IntakeResult, SourceManifest, SourceReadiness
from ..contracts.source import SourceKind, SourceRecord
from ..registry.source_registry import SourceRegistry


_ARTIFACT_KIND_BY_SOURCE = {
    SourceKind.VIDEO: ArtifactKind.VIDEO,
    SourceKind.DOCUMENT: ArtifactKind.DOCUMENT,
    SourceKind.NOTE: ArtifactKind.NOTE,
    SourceKind.IMAGE: ArtifactKind.IMAGE,
}


@dataclass(frozen=True, slots=True)
class LocalFileIntakeResult:
    intake_result: IntakeResult
    artifact: ArtifactRecord


def intake_local_file(
    registry: SourceRegistry,
    source: SourceRecord,
    artifact_root: Path,
    filename: str,
    content: bytes,
    inspected_at: datetime,
) -> LocalFileIntakeResult:
    if source.kind not in _ARTIFACT_KIND_BY_SOURCE:
        raise ValueError(f"local files are not supported for source kind: {source.kind.value}")
    if not isinstance(content, bytes) or not content:
        raise ValueError("local file content must be non-empty bytes")
    safe_name = Path(filename).name
    if not safe_name or safe_name in {".", ".."}:
        raise ValueError("filename must contain a file name")

    registered = registry.register(source)
    raw_dir = Path(artifact_root) / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    target = raw_dir / safe_name
    target.write_bytes(content)
    relative_path = f"raw/{safe_name}"
    artifact = ArtifactRecord(
        artifact_id=f"{source.source_id}:{_ARTIFACT_KIND_BY_SOURCE[source.kind].value}",
        source_id=source.source_id,
        kind=_ARTIFACT_KIND_BY_SOURCE[source.kind],
        relative_path=relative_path,
        state=ArtifactState.AVAILABLE,
        size_bytes=len(content),
    )
    manifest = SourceManifest(
        source=source,
        artifacts=(artifact,),
        inspected_at=inspected_at,
        readiness=SourceReadiness.READY,
    )
    return LocalFileIntakeResult(
        intake_result=IntakeResult(
            manifest=manifest,
            registered_new_source=registered,
        ),
        artifact=artifact,
    )

