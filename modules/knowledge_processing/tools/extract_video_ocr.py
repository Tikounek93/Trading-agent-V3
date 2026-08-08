"""Create sampled video frames and OCR sidecars for knowledge processing."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class OCRRuntimeUnavailable(RuntimeError):
    """Raised when the optional video/OCR runtime is not installed."""


def _normalize_text(value: str) -> str:
    return "\n".join(
        line.strip()
        for line in str(value or "").splitlines()
        if line.strip()
    )


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def extract_video_ocr(
    video_path: str | Path,
    source_root: str | Path,
    source_id: str,
    *,
    sample_every_sec: float = 15.0,
) -> dict[str, Any]:
    """Sample a video, persist frames with readable text, and return sidecars.

    Frames with no detected text are intentionally not persisted. The OCR record
    keeps the raw text while the normal knowledge pipeline creates cleaned OCR.
    """

    try:
        import cv2
        import pytesseract
    except ModuleNotFoundError as exc:
        raise OCRRuntimeUnavailable(
            "OCR runtime requires opencv-python, pillow and pytesseract"
        ) from exc

    if sample_every_sec <= 0:
        raise ValueError("sample_every_sec must be positive")

    video_path = Path(video_path)
    source_root = Path(source_root)
    frames_dir = source_root / "raw" / "frames"
    frame_index_path = source_root / "raw" / "frame_index.json"
    ocr_index_path = source_root / "raw" / "ocr_index.json"

    capture = cv2.VideoCapture(str(video_path))
    if not capture.isOpened():
        raise RuntimeError(f"Cannot open video for OCR: {video_path}")

    fps = float(capture.get(cv2.CAP_PROP_FPS) or 25.0)
    frame_count = int(capture.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    duration = frame_count / fps if fps else 0.0
    frame_records: list[dict[str, Any]] = []
    ocr_records: list[dict[str, Any]] = []

    try:
        timestamp = 0.0
        while timestamp <= duration:
            capture.set(cv2.CAP_PROP_POS_MSEC, timestamp * 1000.0)
            ok, frame = capture.read()
            if not ok:
                timestamp += sample_every_sec
                continue

            text = _normalize_text(
                pytesseract.image_to_string(frame, config="--psm 6")
            )
            if text:
                frame_name = f"{int(timestamp * 1000):010d}_sample.jpg"
                frame_path = frames_dir / frame_name
                frame_path.parent.mkdir(parents=True, exist_ok=True)
                cv2.imwrite(str(frame_path), frame)
                relative_frame_path = str(frame_path.relative_to(source_root))
                record = {
                    "source_id": source_id,
                    "timestamp": round(timestamp, 3),
                    "frame_no": int(timestamp * fps),
                    "path": relative_frame_path,
                    "frame_path": relative_frame_path,
                    "type": "sample",
                    "text": text,
                }
                frame_records.append(
                    {
                        "timestamp": record["timestamp"],
                        "frame_no": record["frame_no"],
                        "path": relative_frame_path,
                        "type": "sample",
                    }
                )
                ocr_records.append(record)
            timestamp += sample_every_sec
    finally:
        capture.release()

    _write_json(
        frame_index_path,
        {
            "source_id": source_id,
            "video_path": str(video_path),
            "sample_every_sec": sample_every_sec,
            "duration": round(duration, 3),
            "frames_count": len(frame_records),
            "frames": frame_records,
        },
    )
    _write_json(
        ocr_index_path,
        {
            "source_id": source_id,
            "frame_count": len(ocr_records),
            "frames": ocr_records,
            "records": ocr_records,
        },
    )
    return {
        "frame_index_path": frame_index_path,
        "ocr_index_path": ocr_index_path,
        "frames": frame_records,
        "ocr_records": ocr_records,
        "duration": duration,
    }
