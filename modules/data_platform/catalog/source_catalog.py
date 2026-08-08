"""SQLite catalog for source manifests and durable artifact status."""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from modules.source_intake.contracts.artifacts import ArtifactState
from modules.source_intake.contracts.intake import SourceManifest
from modules.source_intake.contracts.source import SourceKind, SourceRecord, SourceState

from ..contracts.storage import StoredArtifact


@dataclass(frozen=True, slots=True)
class SourceSummary:
    source_id: str
    title: str | None
    kind: str
    readiness: str
    artifact_count: int
    available_artifact_count: int
    inspected_at: datetime


@dataclass(frozen=True, slots=True)
class ArtifactSummary:
    artifact_id: str
    kind: str
    relative_path: str
    state: str
    size_bytes: int | None
    stored_size_bytes: int | None
    sha256: str | None


class SourceCatalog:
    """Small structured catalog; binary content remains in artifact storage."""

    def __init__(self, database_path: Path) -> None:
        self.database_path = Path(database_path)
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS sources (
                    source_id TEXT PRIMARY KEY,
                    locator TEXT NOT NULL,
                    kind TEXT NOT NULL,
                    title TEXT,
                    state TEXT NOT NULL,
                    registered_at TEXT NOT NULL,
                    tags_json TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS manifests (
                    source_id TEXT PRIMARY KEY REFERENCES sources(source_id),
                    inspected_at TEXT NOT NULL,
                    readiness TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS artifacts (
                    artifact_id TEXT PRIMARY KEY,
                    source_id TEXT NOT NULL REFERENCES sources(source_id),
                    kind TEXT NOT NULL,
                    relative_path TEXT NOT NULL,
                    state TEXT NOT NULL,
                    size_bytes INTEGER,
                    stored_size_bytes INTEGER,
                    sha256 TEXT,
                    stored_at TEXT,
                    UNIQUE(source_id, relative_path)
                );
                """
            )

    def upsert_manifest(
        self,
        manifest: SourceManifest,
        stored_artifacts: tuple[StoredArtifact, ...] = (),
    ) -> None:
        stored_by_id = {item.artifact_id: item for item in stored_artifacts}
        source = manifest.source
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO sources
                    (source_id, locator, kind, title, state, registered_at, tags_json)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(source_id) DO UPDATE SET
                    locator=excluded.locator,
                    kind=excluded.kind,
                    title=excluded.title,
                    state=excluded.state,
                    registered_at=excluded.registered_at,
                    tags_json=excluded.tags_json
                """ ,
                (
                    source.source_id,
                    source.locator,
                    source.kind.value,
                    source.title,
                    source.state.value,
                    source.registered_at.isoformat(),
                    json.dumps(source.tags),
                ),
            )
            connection.execute(
                """
                INSERT INTO manifests (source_id, inspected_at, readiness)
                VALUES (?, ?, ?)
                ON CONFLICT(source_id) DO UPDATE SET
                    inspected_at=excluded.inspected_at,
                    readiness=excluded.readiness
                """,
                (
                    source.source_id,
                    manifest.inspected_at.isoformat(),
                    manifest.readiness.value,
                ),
            )
            connection.execute(
                "DELETE FROM artifacts WHERE source_id = ?",
                (source.source_id,),
            )
            for artifact in manifest.artifacts:
                stored = stored_by_id.get(artifact.artifact_id)
                connection.execute(
                    """
                    INSERT INTO artifacts
                        (artifact_id, source_id, kind, relative_path, state,
                         size_bytes, stored_size_bytes, sha256, stored_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        artifact.artifact_id,
                        artifact.source_id,
                        artifact.kind.value,
                        artifact.relative_path,
                        artifact.state.value,
                        artifact.size_bytes,
                        stored.size_bytes if stored else None,
                        stored.sha256 if stored else None,
                        stored.stored_at.isoformat() if stored else None,
                    ),
                )

    def list_sources(self) -> tuple[SourceSummary, ...]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT sources.source_id, sources.title, sources.kind,
                       manifests.readiness, manifests.inspected_at,
                       COUNT(artifacts.artifact_id) AS artifact_count,
                       SUM(CASE WHEN artifacts.state = 'available' THEN 1 ELSE 0 END)
                           AS available_artifact_count
                FROM sources
                LEFT JOIN manifests ON manifests.source_id = sources.source_id
                LEFT JOIN artifacts ON artifacts.source_id = sources.source_id
                GROUP BY sources.source_id
                ORDER BY sources.source_id
                """
            ).fetchall()
        return tuple(
            SourceSummary(
                source_id=row["source_id"],
                title=row["title"],
                kind=row["kind"],
                readiness=row["readiness"] or "not_ready",
                artifact_count=int(row["artifact_count"] or 0),
                available_artifact_count=int(row["available_artifact_count"] or 0),
                inspected_at=datetime.fromisoformat(
                    row["inspected_at"]
                    or "1970-01-01T00:00:00+00:00"
                ),
            )
            for row in rows
        )

    def list_source_records(self) -> tuple[SourceRecord, ...]:
        """Return registered sources for operational workflows."""

        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT source_id, locator, kind, title, state, registered_at, tags_json
                FROM sources
                ORDER BY source_id
                """
            ).fetchall()
        return tuple(
            SourceRecord(
                source_id=row["source_id"],
                locator=row["locator"],
                kind=SourceKind(row["kind"]),
                title=row["title"],
                state=SourceState(row["state"]),
                registered_at=datetime.fromisoformat(row["registered_at"]),
                tags=tuple(json.loads(row["tags_json"])),
            )
            for row in rows
        )

    def list_artifacts(self, source_id: str) -> tuple[ArtifactSummary, ...]:
        """Return persisted artifact states for one source."""

        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT artifact_id, kind, relative_path, state, size_bytes,
                       stored_size_bytes, sha256
                FROM artifacts
                WHERE source_id = ?
                ORDER BY relative_path
                """,
                (source_id,),
            ).fetchall()
        return tuple(
            ArtifactSummary(
                artifact_id=row["artifact_id"],
                kind=row["kind"],
                relative_path=row["relative_path"],
                state=row["state"],
                size_bytes=row["size_bytes"],
                stored_size_bytes=row["stored_size_bytes"],
                sha256=row["sha256"],
            )
            for row in rows
        )
