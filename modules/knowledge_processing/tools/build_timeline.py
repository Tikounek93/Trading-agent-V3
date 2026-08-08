"""Build the canonical timeline shape consumed by later tools."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any


def build_timeline(
    source_id: str,
    subtitle_segments: Iterable[Mapping[str, Any]],
    *,
    title: str | None = None,
    duration: float | None = None,
    source_locator: str | None = None,
) -> dict[str, Any]:
    segments = []
    for item in subtitle_segments:
        start = float(item["start"])
        end = float(item["end"])
        if end < start:
            raise ValueError("timeline segment end cannot precede start")
        segments.append(
            {
                "start": start,
                "end": end,
                "transcript": str(item.get("text", "")).strip(),
                "frame_paths": list(item.get("frame_paths", [])),
                "ocr_texts": list(item.get("ocr_texts", [])),
                "events": list(item.get("events", [])),
            }
        )
    return {
        "source_id": source_id,
        "title": title,
        "duration": duration,
        "source_locator": source_locator,
        "segments": segments,
    }
