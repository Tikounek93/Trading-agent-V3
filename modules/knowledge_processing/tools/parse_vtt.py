"""Small dependency-free WebVTT parser for local subtitle artifacts."""

from __future__ import annotations

from pathlib import Path


def timestamp_to_seconds(value: str) -> float:
    parts = value.strip().replace(",", ".").split(":")
    if len(parts) == 3:
        hours, minutes, seconds = map(float, parts)
        return hours * 3600 + minutes * 60 + seconds
    if len(parts) == 2:
        minutes, seconds = map(float, parts)
        return minutes * 60 + seconds
    raise ValueError(f"Unsupported subtitle timestamp: {value}")


def _parse_timestamp_line(line: str) -> tuple[float, float] | None:
    if "-->" not in line:
        return None
    start, end = (part.strip().split(" ", 1)[0] for part in line.split("-->", 1))
    return timestamp_to_seconds(start), timestamp_to_seconds(end)


def parse_vtt_subtitles(path: str | Path) -> list[dict[str, object]]:
    """Return non-empty subtitle cues with normalized text and timestamps."""

    subtitle_path = Path(path)
    if not subtitle_path.is_file():
        raise FileNotFoundError(subtitle_path)

    lines = subtitle_path.read_text(encoding="utf-8-sig").splitlines()
    segments: list[dict[str, object]] = []
    index = 0
    while index < len(lines):
        timing = _parse_timestamp_line(lines[index])
        if timing is None and index + 1 < len(lines):
            timing = _parse_timestamp_line(lines[index + 1])
            if timing is not None:
                index += 1
        if timing is None:
            index += 1
            continue

        start, end = timing
        index += 1
        text_lines: list[str] = []
        while index < len(lines) and lines[index].strip():
            text_lines.append(lines[index].strip())
            index += 1
        text = " ".join(text_lines).strip()
        if text:
            segments.append({"start": start, "end": end, "text": text})
        index += 1
    return segments
