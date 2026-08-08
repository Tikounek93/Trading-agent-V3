"""Read-only inspection of explicitly declared local artifacts."""

from __future__ import annotations

from pathlib import Path
from typing import Mapping

from ..contracts.artifacts import ArtifactKind, ArtifactRecord, ArtifactState
from ..contracts.source import SourceRecord


def inspect_artifacts(
    source: SourceRecord,
    artifact_root: Path,
    declared_paths: Mapping[ArtifactKind, str],
) -> tuple[ArtifactRecord, ...]:
    """Inspect file presence without downloading, parsing or modifying content."""

    records: list[ArtifactRecord] = []
    for kind, relative_path in declared_paths.items():
        path_parts = relative_path.replace("\\", "/").split("/")
        if relative_path.startswith(("/", "\\")) or ".." in path_parts:
            raise ValueError("declared artifact path must be relative")

        path = artifact_root / relative_path
        available = path.is_file()
        records.append(
            ArtifactRecord(
                artifact_id=(
                    f"{source.source_id}:{kind.value}:"
                    f"{relative_path.replace('\\', '_').replace('/', '_')}"
                ),
                source_id=source.source_id,
                kind=kind,
                relative_path=relative_path,
                state=ArtifactState.AVAILABLE if available else ArtifactState.MISSING,
                size_bytes=path.stat().st_size if available else None,
            )
        )
    return tuple(records)
