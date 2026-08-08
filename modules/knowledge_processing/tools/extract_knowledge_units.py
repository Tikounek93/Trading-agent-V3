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


def build_knowledge_candidates(chunks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Project enriched chunks into explicit, traceable knowledge candidates."""

    candidates: list[dict[str, Any]] = []
    for chunk in chunks:
        semantic = chunk.get("semantic", {})
        if not isinstance(semantic, dict):
            semantic = {}
        if not semantic.get("topics") and not chunk.get("events"):
            continue
        candidates.append(
            {
                "candidate_id": f"{chunk.get('chunk_id', 'chunk')}_candidate",
                "source_chunk_id": chunk.get("chunk_id"),
                "start": chunk.get("start"),
                "end": chunk.get("end"),
                "text": semantic.get("search_text") or chunk.get("combined_transcript", ""),
                "concepts": list(semantic.get("topics", [])),
                "setup_stages": list(semantic.get("setup_stages", [])),
                "rule_candidates": list(semantic.get("rule_candidates", [])),
                "events": list(chunk.get("events", [])),
            }
        )
    return candidates


def _canonical_unit_text(value: str) -> str:
    return re.sub(r"[^a-z0-9 ]+", "", value.casefold()).strip()


def _unit_is_redundant(candidate: dict[str, Any], existing: dict[str, Any]) -> bool:
    if candidate.get("source_chunk_id") != existing.get("source_chunk_id"):
        return False
    candidate_words = _canonical_unit_text(str(candidate.get("text") or "")).split()
    existing_words = _canonical_unit_text(str(existing.get("text") or "")).split()
    if not candidate_words or not existing_words:
        return True
    if candidate_words == existing_words:
        return True
    shorter, longer = sorted((candidate_words, existing_words), key=len)
    if len(shorter) >= 8:
        for start in range(len(longer) - len(shorter) + 1):
            if longer[start : start + len(shorter)] == shorter:
                return True
    overlap = len(set(candidate_words) & set(existing_words)) / max(
        len(set(shorter)), 1
    )
    return overlap >= 0.92


def refine_knowledge_units(
    units: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, int | str]]:
    """Remove repeated/contained units without merging separate chunks."""

    refined: list[dict[str, Any]] = []
    exact_duplicates = 0
    contained_duplicates = 0
    seen: set[tuple[str, str]] = set()
    for unit in units:
        key = (
            str(unit.get("source_chunk_id") or ""),
            _canonical_unit_text(str(unit.get("text") or "")),
        )
        if key in seen:
            exact_duplicates += 1
            continue
        redundant_index = next(
            (
                index
                for index, existing in enumerate(refined)
                if _unit_is_redundant(unit, existing)
            ),
            None,
        )
        if redundant_index is not None:
            existing = refined[redundant_index]
            if len(str(unit.get("text") or "")) > len(str(existing.get("text") or "")):
                refined[redundant_index] = unit
            contained_duplicates += 1
            continue
        seen.add(key)
        refined.append(unit)
    return refined, {
        "version": "1.0.0",
        "input_units": len(units),
        "retained_units": len(refined),
        "removed_exact_duplicates": exact_duplicates,
        "removed_contained_or_overlapping_units": contained_duplicates,
    }


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
