"""Tool for deriving source readiness from artifact states."""

from datetime import datetime

from ..contracts.artifacts import ArtifactRecord, ArtifactState
from ..contracts.intake import SourceManifest, SourceReadiness
from ..contracts.source import SourceRecord


def build_source_manifest(
    source: SourceRecord,
    artifacts: tuple[ArtifactRecord, ...],
    inspected_at: datetime,
) -> SourceManifest:
    states = {artifact.state for artifact in artifacts}
    if not artifacts:
        readiness = SourceReadiness.NOT_READY
    elif ArtifactState.INVALID in states:
        readiness = SourceReadiness.BLOCKED
    elif states == {ArtifactState.AVAILABLE}:
        readiness = SourceReadiness.READY
    else:
        readiness = SourceReadiness.PARTIAL

    return SourceManifest(
        source=source,
        artifacts=artifacts,
        inspected_at=inspected_at,
        readiness=readiness,
    )
