"""Fetch and normalize VTT subtitles without downloading media."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .acquire_video import DownloaderFactory
from ..adapters.youtube_adapter import create_youtube_downloader
from ..contracts.acquisition import AcquisitionResult, AcquisitionStatus
from ..contracts.artifacts import ArtifactKind, ArtifactRecord, ArtifactState
from ..contracts.source import SourceRecord, SourceKind


def build_subtitle_options(raw_dir: Path, languages: tuple[str, ...]) -> dict[str, Any]:
    return {
        "skip_download": True,
        "noplaylist": True,
        "writesubtitles": True,
        "writeautomaticsub": True,
        "subtitleslangs": list(languages),
        "subtitlesformat": "vtt",
        "outtmpl": str(raw_dir / "subtitles.%(ext)s"),
        "quiet": True,
        "no_warnings": True,
    }


def _normalize_subtitle(raw_dir: Path, language: str, source_id: str) -> Path | None:
    canonical = raw_dir / f"subtitles.{language}.vtt"
    if canonical.is_file():
        return canonical
    candidates = (
        raw_dir / f"{source_id}.{language}.vtt",
        raw_dir / f"subtitles.{language}.{language}.vtt",
        raw_dir / "subtitles.vtt" if language == "en" else raw_dir / "missing.vtt",
    )
    for candidate in candidates:
        if candidate.is_file():
            candidate.replace(canonical)
            return canonical
    return None


def acquire_subtitles(
    source: SourceRecord,
    artifact_root: Path,
    languages: tuple[str, ...] = ("en", "en-orig"),
    downloader_factory: DownloaderFactory | None = None,
) -> AcquisitionResult:
    if source.kind is not SourceKind.VIDEO:
        return AcquisitionResult(
            source_id=source.source_id,
            operation="fetch_subtitles",
            status=AcquisitionStatus.BLOCKED,
            message="subtitle acquisition requires a video source",
        )

    raw_dir = artifact_root / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    factory = downloader_factory or create_youtube_downloader
    try:
        with factory(build_subtitle_options(raw_dir, languages)) as downloader:
            downloader.extract_info(source.locator, download=True)
    except Exception as exc:
        return AcquisitionResult(
            source_id=source.source_id,
            operation="fetch_subtitles",
            status=AcquisitionStatus.FAILED,
            message=str(exc),
        )

    artifacts: list[ArtifactRecord] = []
    for language in languages:
        subtitle_path = _normalize_subtitle(raw_dir, language, source.source_id)
        if subtitle_path is None:
            continue
        artifacts.append(
            ArtifactRecord(
                artifact_id=f"{source.source_id}:subtitle:{language}",
                source_id=source.source_id,
                kind=ArtifactKind.SUBTITLE,
                relative_path=f"raw/subtitles.{language}.vtt",
                state=ArtifactState.AVAILABLE,
                size_bytes=subtitle_path.stat().st_size,
            )
        )

    if not artifacts:
        return AcquisitionResult(
            source_id=source.source_id,
            operation="fetch_subtitles",
            status=AcquisitionStatus.BLOCKED,
            message="provider completed without a local VTT subtitle",
        )
    return AcquisitionResult(
        source_id=source.source_id,
        operation="fetch_subtitles",
        status=AcquisitionStatus.PREPARED,
        artifacts=tuple(artifacts),
        message="subtitle artifacts acquired",
    )
