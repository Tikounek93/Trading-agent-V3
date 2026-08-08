"""Append-only operator corrections for knowledge artifacts."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4


ALLOWED_TARGET_TYPES = frozenset({"timeline_segment", "chunk", "knowledge_unit"})
ALLOWED_FIELDS = frozenset(
    {
        "transcript",
        "ocr_text",
        "start",
        "end",
        "concepts",
        "setup_stages",
        "text",
        "classification",
        "note",
    }
)


class KnowledgeCorrectionStore:
    """Keep human corrections separate from generated knowledge output."""

    def __init__(self, root: Path) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _validate_source_id(source_id: str) -> None:
        allowed = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_.-"
        if not source_id or any(character not in allowed for character in source_id):
            raise ValueError("unsafe source_id")

    def _target(self, source_id: str) -> Path:
        self._validate_source_id(source_id)
        return self.root / source_id / "corrections.jsonl"

    def list(self, source_id: str) -> list[dict[str, Any]]:
        target = self._target(source_id)
        if not target.is_file():
            return []
        records: list[dict[str, Any]] = []
        for line in target.read_text(encoding="utf-8").splitlines():
            if line.strip():
                records.append(json.loads(line))
        return records

    def count(self, source_id: str) -> int:
        return len(self.list(source_id))

    def create(
        self,
        source_id: str,
        *,
        target_type: str,
        target_id: str,
        field: str,
        corrected_value: Any,
        reason: str,
        author: str = "operator",
    ) -> dict[str, Any]:
        target = self._target(source_id)
        if target_type not in ALLOWED_TARGET_TYPES:
            raise ValueError("unsupported correction target type")
        if field not in ALLOWED_FIELDS:
            raise ValueError("unsupported correction field")
        if not isinstance(target_id, str) or not target_id.strip():
            raise ValueError("target_id must not be empty")
        if not isinstance(reason, str) or not reason.strip():
            raise ValueError("reason must not be empty")
        if not isinstance(author, str) or not author.strip():
            raise ValueError("author must not be empty")
        record = {
            "correction_id": uuid4().hex,
            "source_id": source_id,
            "target_type": target_type,
            "target_id": target_id.strip(),
            "field": field,
            "corrected_value": corrected_value,
            "reason": reason.strip(),
            "author": author.strip(),
            "created_at": datetime.now(UTC).isoformat(),
            "append_only": True,
        }
        encoded = json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n"
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("a", encoding="utf-8") as handle:
            handle.write(encoded)
        return record
