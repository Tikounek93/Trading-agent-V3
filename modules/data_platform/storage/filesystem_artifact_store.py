"""Filesystem implementation of the artifact storage port."""

from __future__ import annotations

import hashlib
import shutil
from datetime import UTC, datetime
from pathlib import Path

from ..contracts.storage import StoredArtifact, StorageKey


class FileSystemArtifactStore:
    """Store artifacts below ``root/<source_id>/<relative_path>``."""

    def __init__(self, root: Path) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def _target(self, source_id: str, relative_path: str) -> Path:
        key = StorageKey(source_id, relative_path)
        target = self.root / key.source_id / key.relative_path
        resolved_root = self.root.resolve()
        resolved_target = target.resolve()
        if resolved_target != resolved_root and resolved_root not in resolved_target.parents:
            raise ValueError("artifact path escapes storage root")
        return target

    @staticmethod
    def _digest(path: Path) -> tuple[int, str]:
        digest = hashlib.sha256()
        size = 0
        with path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                size += len(chunk)
                digest.update(chunk)
        return size, digest.hexdigest()

    def put_file(
        self,
        artifact_id: str,
        source_id: str,
        relative_path: str,
        source_path: Path,
        stored_at: datetime | None = None,
    ) -> StoredArtifact:
        source = Path(source_path)
        if not source.is_file():
            raise FileNotFoundError(source)
        target = self._target(source_id, relative_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        if source.resolve() != target.resolve():
            shutil.copyfile(source, target)
        size, sha256 = self._digest(target)
        return StoredArtifact(
            artifact_id=artifact_id,
            source_id=source_id,
            relative_path=relative_path,
            size_bytes=size,
            sha256=sha256,
            stored_at=stored_at or datetime.now(UTC),
        )

    def promote_file(
        self,
        artifact_id: str,
        source_id: str,
        relative_path: str,
        source_path: Path,
        stored_at: datetime | None = None,
    ) -> StoredArtifact:
        """Move a complete staging artifact into durable storage.

        An existing target is accepted only when its digest matches. In that
        case the staging duplicate is removed and the operation is idempotent.
        """

        source = Path(source_path)
        target = self._target(source_id, relative_path)
        if not source.is_file() and not target.is_file():
            raise FileNotFoundError(source)
        if source.is_file() and source.resolve() != target.resolve():
            target.parent.mkdir(parents=True, exist_ok=True)
            if target.is_file():
                source_size, source_sha256 = self._digest(source)
                target_size, target_sha256 = self._digest(target)
                if (source_size, source_sha256) != (target_size, target_sha256):
                    raise ValueError(f"durable artifact differs from staging artifact: {target}")
                source.unlink()
            else:
                shutil.move(str(source), str(target))
        size, sha256 = self._digest(target)
        return StoredArtifact(
            artifact_id=artifact_id,
            source_id=source_id,
            relative_path=relative_path,
            size_bytes=size,
            sha256=sha256,
            stored_at=stored_at or datetime.now(UTC),
        )

    def remove_file(self, source_id: str, relative_path: str) -> bool:
        """Remove one durable artifact copy and prune empty source folders."""

        target = self._target(source_id, relative_path)
        if not target.is_file():
            return False
        target.unlink()
        current = target.parent
        source_root = (self.root / StorageKey(source_id, relative_path).source_id).resolve()
        while current.resolve() != source_root and current.is_dir():
            try:
                current.rmdir()
            except OSError:
                break
            current = current.parent
        return True

    def read_bytes(self, source_id: str, relative_path: str) -> bytes:
        target = self._target(source_id, relative_path)
        if not target.is_file():
            raise FileNotFoundError(target)
        return target.read_bytes()

    def exists(self, source_id: str, relative_path: str) -> bool:
        return self._target(source_id, relative_path).is_file()
