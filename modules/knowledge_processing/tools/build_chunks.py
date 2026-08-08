"""Deterministic semantic chunking adapted from the v2 extraction core."""

from __future__ import annotations

from collections import Counter
from typing import Any


def _event_key(event: dict[str, Any]) -> str:
    return str(event.get("type") or event.get("event_type") or "unknown")


def _dedupe_text(parts: list[str]) -> str:
    words: list[str] = []
    for part in parts:
        part_words = " ".join(part.split()).split()
        overlap = 0
        for size in range(min(len(words), len(part_words), 20), 0, -1):
            if [word.lower() for word in words[-size:]] == [
                word.lower() for word in part_words[:size]
            ]:
                overlap = size
                break
        words.extend(part_words[overlap:])
    return " ".join(words)


def _dedupe_events(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    unique: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str]] = set()
    for event in events:
        key = (
            str(event.get("type") or event.get("event_type") or "unknown"),
            str(event.get("keyword") or ""),
            str(event.get("source") or ""),
        )
        if key in seen:
            continue
        seen.add(key)
        unique.append(event)
    return unique


def build_semantic_chunks(
    timeline: dict[str, Any],
    *,
    max_gap_sec: float = 8.0,
    max_chunk_duration_sec: float = 180.0,
    min_chunk_duration_sec: float = 20.0,
) -> list[dict[str, Any]]:
    chunks: list[dict[str, Any]] = []
    current: list[dict[str, Any]] = []

    def flush() -> None:
        if not current:
            return
        transcript = _dedupe_text(
            [str(item.get("transcript") or "") for item in current]
        )
        ocr = []
        for item in current:
            for value in item.get("ocr_texts", []):
                if isinstance(value, dict):
                    text = str(value.get("text") or value.get("content") or "").strip()
                else:
                    text = str(value).strip()
                if text:
                    ocr.append(text)
        frames = [path for item in current for path in item.get("frame_paths", [])]
        events = _dedupe_events(
            [event for item in current for event in item.get("events", [])]
        )
        start = float(current[0].get("start", 0))
        end = float(current[-1].get("end", start))
        counts = Counter(_event_key(event) for event in events)
        chunks.append(
            {
                "chunk_id": f"chunk_{len(chunks):05d}",
                "start": start,
                "end": end,
                "duration": round(end - start, 3),
                "combined_transcript": transcript,
                "combined_ocr": "\n".join(dict.fromkeys(ocr)),
                "events": events,
                "event_counts": dict(counts),
                "dominant_concepts": [name for name, _ in counts.most_common(8)],
                "frame_paths": list(dict.fromkeys(frames)),
                "segment_refs": [
                    {"start": item.get("start"), "end": item.get("end")}
                    for item in current
                ],
                "quality": {
                    "has_transcript": bool(transcript),
                    "has_ocr": bool(ocr),
                    "has_events": bool(events),
                    "frame_count": len(set(frames)),
                    "event_count": len(events),
                    "segment_count": len(current),
                },
            }
        )
        current.clear()

    for segment in timeline.get("segments", []):
        if not current:
            current.append(segment)
            continue
        previous = current[-1]
        gap = float(segment.get("start", 0)) - float(previous.get("end", 0))
        duration = float(segment.get("end", 0)) - float(
            current[0].get("start", 0)
        )
        should_split = gap > max_gap_sec or duration > max_chunk_duration_sec
        if (
            duration >= min_chunk_duration_sec
            and segment.get("events")
            and previous.get("events")
        ):
            should_split = should_split or bool(
                {
                    _event_key(event) for event in segment["events"]
                }.isdisjoint(
                    {_event_key(event) for event in previous["events"]}
                )
            )
        if should_split:
            flush()
        current.append(segment)
    flush()
    return chunks
