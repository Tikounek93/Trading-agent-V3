"""Extract traceable advisory knowledge units from enriched chunks."""

from __future__ import annotations

import re
from collections import Counter
from typing import Any


UNIT_PATTERNS = {
    "concept_definition": (r"\bthis is\b", r"\bwhen I say\b", r"\bthe term\b"),
    "workflow_step": (r"\blook for\b", r"\bwait for\b", r"\bthen\b", r"\bnext\b"),
    "condition": (r"\bif\b", r"\bwhen\b", r"\bonce\b", r"\bshould\b"),
    "confirmation": (r"\bconfirm\b", r"\bconfirmation\b", r"\bdisplacement\b"),
    "invalidation": (r"\binvalid\b", r"\binvalidation\b", r"\bstop loss\b"),
}

CONCEPT_KEYWORDS = {
    "market_structure_shift": ("market structure shift", "mss"),
    "liquidity": ("liquidity", "buy side", "sell side", "sweep"),
    "fair_value_gap": ("fair value gap", "fvg", "imbalance"),
    "order_block": ("order block", "bullish order block", "bearish order block"),
    "ote": ("ote", "optimal trade entry", "retracement", "premium", "discount"),
}


def _sentences(text: str) -> list[str]:
    normalized = re.sub(r"\s+", " ", text or "").strip()
    parts = re.split(
        r"(?<=[.!?])\s+|\s(?=all right|okay|so|now|then|if|when)\b",
        normalized,
    )
    return [part.strip() for part in parts if len(part.strip()) > 20]


def extract_knowledge_units(chunks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    units: list[dict[str, Any]] = []
    for chunk in chunks:
        semantic = chunk.get("semantic", {})
        text = str(
            semantic.get("search_text")
            or chunk.get("combined_transcript")
            or ""
        )
        for index, sentence in enumerate(_sentences(text)):
            lowered = sentence.lower()
            unit_types = [
                name
                for name, patterns in UNIT_PATTERNS.items()
                if any(re.search(pattern, lowered) for pattern in patterns)
            ]
            concepts = [
                name
                for name, keywords in CONCEPT_KEYWORDS.items()
                if any(keyword in lowered for keyword in keywords)
            ]
            if not unit_types and not concepts:
                continue
            stages = []
            if "liquidity" in concepts:
                stages.append("liquidity_context")
            if "market_structure_shift" in concepts:
                stages.append("market_structure_confirmation")
            if {"fair_value_gap", "order_block", "ote"} & set(concepts):
                stages.append("pd_array_selection")
            if "confirmation" in unit_types:
                stages.append("confirmation_logic")
            if "invalidation" in unit_types:
                stages.append("risk_or_invalidation")
            units.append(
                {
                    "unit_id": f"{chunk.get('chunk_id', 'chunk')}_u{index:03d}",
                    "source_chunk_id": chunk.get("chunk_id"),
                    "source_start": chunk.get("start"),
                    "source_end": chunk.get("end"),
                    "text": sentence,
                    "unit_types": unit_types,
                    "concepts": concepts,
                    "setup_stages": stages,
                    "source_events": list(chunk.get("events", [])),
                    "source_frame_paths": list(chunk.get("frame_paths", [])),
                    "confidence": "heuristic_v1",
                }
            )
    return units


def build_knowledge_units_summary(
    source_id: str,
    units: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "source_id": source_id,
        "units_count": len(units),
        "unit_type_counts": dict(
            Counter(kind for unit in units for kind in unit["unit_types"])
        ),
        "concept_counts": dict(
            Counter(concept for unit in units for concept in unit["concepts"])
        ),
        "stage_counts": dict(
            Counter(stage for unit in units for stage in unit["setup_stages"])
        ),
        "knowledge_units": units,
    }
