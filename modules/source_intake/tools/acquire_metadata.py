"""Fetch provider metadata without downloading media."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .acquire_video import DownloaderFactory
from ..adapters.youtube_adapter import create_youtube_downloader
from ..contracts.acquisition import AcquisitionResult, AcquisitionStatus
from ..contracts.artifacts import ArtifactKind, ArtifactRecord, ArtifactState
from ..contracts.source import SourceRecord, SourceKind


def build_metadata_options(raw_dir: Path) -> dict[str, Any]:
    return {
        "outtmpl": str(raw_dir / "metadata.%(ext)s"),
        "quiet": True,
        "noplaylist": True,
        "skip_download": True,
    }


def acquire_metadata(
    source: SourceRecord,
    artifact_root: Path,
    downloader_factory: DownloaderFactory | None = None,
) -> AcquisitionResult:
    if source.kind is not SourceKind.VIDEO:
        return AcquisitionResult(
            source_id=source.source_id,
            operation="fetch_metadata",
            status=AcquisitionStatus.BLOCKED,
            message="provider metadata acquisition requires a video source",
        )

    raw_dir = artifact_root / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    factory = downloader_factory or create_youtube_downloader
    try:
        with factory(build_metadata_options(raw_dir)) as downloader:
            info = downloader.extract_info(source.locator, download=False)
        if not isinstance(info, dict):
            raise ValueError("provider returned no metadata mapping")
        metadata_path = raw_dir / "info.json"
        metadata_path.write_text(
            json.dumps(info, ensure_ascii=False, indent=2, sort_keys=True, default=str),
            encoding="utf-8",
        )
    except Exception as exc:
        return AcquisitionResult(
            source_id=source.source_id,
            operation="fetch_metadata",
            status=AcquisitionStatus.FAILED,
            message=str(exc),
        )

    artifact = ArtifactRecord(
        artifact_id=f"{source.source_id}:metadata",
        source_id=source.source_id,
        kind=ArtifactKind.METADATA,
        relative_path="raw/info.json",
        state=ArtifactState.AVAILABLE,
        size_bytes=metadata_path.stat().st_size,
    )
    return AcquisitionResult(
        source_id=source.source_id,
        operation="fetch_metadata",
        status=AcquisitionStatus.PREPARED,
        artifacts=(artifact,),
        message="metadata artifact acquired",
    )
