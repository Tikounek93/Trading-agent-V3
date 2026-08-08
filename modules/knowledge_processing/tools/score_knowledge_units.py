"""Deterministic advisory scoring, never a strategy or execution decision."""

from __future__ import annotations

import re
from typing import Any


HIGH_VALUE_CONCEPTS = {
    "market_structure_shift",
    "liquidity",
    "fair_value_gap",
    "order_block",
    "ote",
}
HIGH_VALUE_TYPES = {"condition", "confirmation", "workflow_step", "invalidation"}
NOISE_PATTERNS = (
    r"\bwelcome back\b",
    r"\byoutube channel\b",
    r"\bhomework\b",
    r"\bstudy journal\b",
)


def score_knowledge_unit(unit: dict[str, Any]) -> dict[str, Any]:
    text = str(unit.get("text") or "")
    concepts = set(unit.get("concepts", []))
    unit_types = set(unit.get("unit_types", []))
    stages = set(unit.get("setup_stages", []))
    score = 0
    reasons: list[str] = []
    if concepts & HIGH_VALUE_CONCEPTS:
        score += 3
        reasons.append("contains_high_value_concept")
    if unit_types & HIGH_VALUE_TYPES:
        score += 2
        reasons.append("contains_actionable_unit_type")
    if len(concepts) >= 2:
        score += 2
        reasons.append("multiple_concepts")
    if len(stages) >= 2:
        score += 1
        reasons.append("multiple_setup_stages")
    if "condition" in unit_types:
        score += 2
        reasons.append("conditional_logic")
    if "confirmation" in unit_types:
        score += 2
        reasons.append("confirmation_logic")
    if "invalidation" in unit_types:
        score += 2
        reasons.append("risk_or_invalidation")
    if any(re.search(pattern, text.lower()) for pattern in NOISE_PATTERNS):
        score -= 4
        reasons.append("noise_pattern_detected")
    if len(text) < 60:
        score -= 1
        reasons.append("short_text")
    if len(text) > 450:
        score -= 1
        reasons.append("long_text_maybe_mixed")
    scored = dict(unit)
    scored["knowledge_score"] = score
    scored["relevance"] = (
        "high_value" if score >= 7 else "medium_value" if score >= 3 else "low_value"
    )
    scored["score_reasons"] = reasons
    return scored
