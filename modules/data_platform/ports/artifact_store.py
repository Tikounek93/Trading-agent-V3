"""Storage port used by workflows and future storage implementations."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Protocol

from ..contracts.storage import StoredArtifact


class ArtifactStore(Protocol):
    def put_file(
        self,
        artifact_id: str,
        source_id: str,
        relative_path: str,
        source_path: Path,
        stored_at: datetime | None = None,
    ) -> StoredArtifact:
        """Copy one local artifact and return its durable receipt."""

    def promote_file(
        self,
        artifact_id: str,
        source_id: str,
        relative_path: str,
        source_path: Path,
        stored_at: datetime | None = None,
    ) -> StoredArtifact:
        """Move one verified staging artifact into durable storage."""

    def read_bytes(self, source_id: str, relative_path: str) -> bytes:
        """Read one stored artifact by its source-relative path."""

    def exists(self, source_id: str, relative_path: str) -> bool:
        """Return whether one artifact is present in durable storage."""
