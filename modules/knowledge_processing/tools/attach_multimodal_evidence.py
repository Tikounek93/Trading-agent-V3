"""Attach optional frame-index and OCR sidecar evidence to timeline segments."""

from __future__ import annotations

from typing import Any, Iterable, Mapping


def _timestamp(item: Mapping[str, Any]) -> float | None:
    for key in ("timestamp", "time", "start"):
        if item.get(key) is not None:
            return float(item[key])
    return None


def attach_multimodal_evidence(
    timeline: dict[str, Any],
    *,
    frame_index: Iterable[Mapping[str, Any]] = (),
    ocr_records: Iterable[Mapping[str, Any]] = (),
    max_distance_sec: float = 2.5,
) -> dict[str, Any]:
    frames = [dict(item) for item in frame_index if _timestamp(item) is not None]
    ocr = [dict(item) for item in ocr_records if _timestamp(item) is not None]
    result = {**timeline, "segments": []}
    for segment in timeline.get("segments", []):
        start = float(segment.get("start", 0))
        end = float(segment.get("end", start))
        midpoint = (start + end) / 2
        matched_frames = list(segment.get("frame_paths", []))
        matched_ocr = list(segment.get("ocr_texts", []))
        for frame in frames:
            timestamp = _timestamp(frame)
            if timestamp is not None and (
                start <= timestamp <= end or abs(timestamp - midpoint) <= max_distance_sec
            ):
                path = frame.get("path") or frame.get("frame_path")
                if path and path not in matched_frames:
                    matched_frames.append(str(path))
        for record in ocr:
            timestamp = _timestamp(record)
            if timestamp is not None and (
                start <= timestamp <= end or abs(timestamp - midpoint) <= max_distance_sec
            ):
                if record not in matched_ocr:
                    matched_ocr.append(record)
        result["segments"].append(
            {
                **segment,
                "frame_paths": matched_frames,
                "ocr_texts": matched_ocr,
            }
        )
    return result
