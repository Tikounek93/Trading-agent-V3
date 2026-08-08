"""External provider adapters for source_intake."""

from .youtube_adapter import create_youtube_downloader

__all__ = ["create_youtube_downloader"]
