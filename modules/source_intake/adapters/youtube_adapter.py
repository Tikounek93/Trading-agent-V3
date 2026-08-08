"""Lazy YouTube provider adapter.

The optional provider dependency is imported only when a real acquisition is
requested. Tests and callers may inject their own downloader factory.
"""

from typing import Any


def create_youtube_downloader(options: dict[str, Any]) -> Any:
    try:
        from yt_dlp import YoutubeDL
    except ModuleNotFoundError as exc:
        raise RuntimeError("yt-dlp is required for YouTube acquisition") from exc
    return YoutubeDL(options)
