"""Acquire one video through an injected or real YouTube provider."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from ..adapters.youtube_adapter import create_youtube_downloader
from ..contracts.acquisition import AcquisitionResult, AcquisitionStatus
from ..contracts.artifacts import ArtifactKind, ArtifactRecord, ArtifactState
from ..contracts.source import SourceRecord, SourceKind


DownloaderFactory = Callable[[dict[str, Any]], Any]


def build_video_download_options(raw_dir: Path) -> dict[str, Any]:
    return {
        "outtmpl": str(raw_dir / "video.%(ext)s"),
        "format": "mp4/best",
        "merge_output_format": "mp4",
        "quiet": True,
        "noplaylist": True,
        "skip_download": False,
    }


def acquire_video(
    source: SourceRecord,
    artifact_root: Path,
    downloader_factory: DownloaderFactory | None = None,
) -> AcquisitionResult:
    if source.kind is not SourceKind.VIDEO:
        return AcquisitionResult(
            source_id=source.source_id,
            operation="download_video",
            status=AcquisitionStatus.BLOCKED,
            message="video acquisition requires a video source",
        )

    raw_dir = artifact_root / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    options = build_video_download_options(raw_dir)
    factory = downloader_factory or create_youtube_downloader

    try:
        with factory(options) as downloader:
            downloader.extract_info(source.locator, download=True)
    except Exception as exc:
        return AcquisitionResult(
            source_id=source.source_id,
            operation="download_video",
            status=AcquisitionStatus.FAILED,
            message=str(exc),
        )

    video_path = raw_dir / "video.mp4"
    if not video_path.is_file():
        candidates = sorted(
            path
            for path in raw_dir.glob("video.*")
            if path.is_file() and path.suffix.lower() not in {".part", ".ytdl"}
        )
        if len(candidates) == 1:
            candidates[0].replace(video_path)

    if not video_path.is_file():
        return AcquisitionResult(
            source_id=source.source_id,
            operation="download_video",
            status=AcquisitionStatus.FAILED,
            message="provider completed without a local video artifact",
        )

    artifact = ArtifactRecord(
        artifact_id=f"{source.source_id}:video",
        source_id=source.source_id,
        kind=ArtifactKind.VIDEO,
        relative_path="raw/video.mp4",
        state=ArtifactState.AVAILABLE,
        size_bytes=video_path.stat().st_size,
    )
    return AcquisitionResult(
        source_id=source.source_id,
        operation="download_video",
        status=AcquisitionStatus.PREPARED,
        artifacts=(artifact,),
        message="video artifact acquired",
    )
