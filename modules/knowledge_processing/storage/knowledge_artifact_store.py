"""Atomic append-only JSON storage for knowledge artifacts."""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path


@dataclass(frozen=True, slots=True)
class KnowledgeStorageReceipt:
    source_id: str
    relative_path: str
    size_bytes: int
    sha256: str
    stored_at: datetime
    status: str
    history_relative_path: str | None = None


class KnowledgeArtifactStore:
    """Persist a current projection and an append-only history per source."""

    def __init__(self, root: Path) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _validate_source_id(source_id: str) -> None:
        if not source_id or source_id in {".", ".."} or any(
            character not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_.-"
            for character in source_id
        ):
            raise ValueError("unsafe source_id")

    def _target(self, source_id: str) -> Path:
        self._validate_source_id(source_id)
        return self.root / source_id / "knowledge.json"

    @staticmethod
    def _digest(payload: bytes) -> str:
        return hashlib.sha256(payload).hexdigest()

    def save(self, source_id: str, payload: dict) -> KnowledgeStorageReceipt:
        target = self._target(source_id)
        encoded = (
            json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True)
            + "\n"
        ).encode("utf-8")
        digest = self._digest(encoded)
        status = "stored"
        history_relative_path: str | None = None
        if target.is_file() and target.read_bytes() == encoded:
            status = "already_current"
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            history_dir = target.parent / "history"
            history_dir.mkdir(parents=True, exist_ok=True)
            history_target = history_dir / (
                f"{datetime.now(UTC).strftime('%Y%m%dT%H%M%S%fZ')}_{digest[:12]}.json"
            )
            history_temporary = history_target.with_suffix(".json.tmp")
            history_temporary.write_bytes(encoded)
            os.replace(history_temporary, history_target)
            temporary = target.with_suffix(".json.tmp")
            temporary.write_bytes(encoded)
            os.replace(temporary, target)
            history_relative_path = f"{source_id}/history/{history_target.name}"
        return KnowledgeStorageReceipt(
            source_id=source_id,
            relative_path=f"{source_id}/knowledge.json",
            size_bytes=len(encoded),
            sha256=digest,
            stored_at=datetime.now(UTC),
            status=status,
            history_relative_path=history_relative_path,
        )

    def load(self, source_id: str) -> dict:
        target = self._target(source_id)
        if not target.is_file():
            raise FileNotFoundError(target)
        return json.loads(target.read_text(encoding="utf-8"))

    def exists(self, source_id: str) -> bool:
        return self._target(source_id).is_file()

    def list_source_ids(self) -> tuple[str, ...]:
        if not self.root.is_dir():
            return ()
        return tuple(
            sorted(
                path.name
                for path in self.root.iterdir()
                if path.is_dir() and (path / "knowledge.json").is_file()
            )
        )
