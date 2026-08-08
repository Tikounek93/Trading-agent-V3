"""Advisory topic, stage and rule-candidate enrichment."""

from __future__ import annotations

import re
from typing import Any


TOPIC_KEYWORDS = {
    "market_structure_shift": ("market structure shift", "mss"),
    "order_block": ("order block",),
    "fair_value_gap": ("fair value gap", "fvg"),
    "ote": ("optimal trade entry", "ote"),
    "liquidity": ("liquidity", "buy side", "sell side", "stop hunt"),
    "breaker": ("breaker",),
    "premium_discount": ("premium", "discount"),
}

SETUP_STAGES = {
    "context": ("daily bias", "higher timeframe", "premium", "discount", "session"),
    "liquidity": ("liquidity", "stop hunt", "equal highs", "equal lows"),
    "confirmation": ("market structure shift", "breaker", "displacement"),
    "entry": ("order block", "fair value gap", "ote", "limit order"),
    "management": ("take profit", "stop loss", "partials", "runner"),
    "review": ("study journal", "review", "examples"),
}


def _matches(text: str, keywords: tuple[str, ...]) -> bool:
    return any(keyword in text for keyword in keywords)


def clean_ocr_text(raw_text: str) -> tuple[str, float]:
    """Remove low-value OCR lines and return cleaned text plus quality score."""

    cleaned_lines: list[str] = []
    seen: set[str] = set()
    for line in str(raw_text or "").splitlines():
        normalized = " ".join(line.split()).strip()
        if len(normalized) < 6:
            continue
        alpha_ratio = sum(character.isalpha() for character in normalized) / max(
            len(normalized), 1
        )
        if alpha_ratio < 0.45 or re.fullmatch(r"[\W_]+", normalized):
            continue
        key = normalized.casefold()
        if key in seen:
            continue
        seen.add(key)
        cleaned_lines.append(normalized)
    cleaned = "\n".join(cleaned_lines)
    useful_lines = sum(len(line.split()) >= 3 for line in cleaned_lines)
    score = round(useful_lines / max(len(cleaned_lines), 1), 3)
    return cleaned, score


def enrich_chunk(chunk: dict[str, Any]) -> dict[str, Any]:
    cleaned_ocr, ocr_quality_score = clean_ocr_text(chunk.get("combined_ocr", ""))
    text = "\n".join(
        (
            str(chunk.get("combined_transcript") or ""),
            cleaned_ocr,
        )
    ).strip()
    normalized = text.lower()
    topics = [
        topic
        for topic, keywords in TOPIC_KEYWORDS.items()
        if _matches(normalized, keywords)
    ]
    stages = [
        stage
        for stage, keywords in SETUP_STAGES.items()
        if _matches(normalized, keywords)
    ]
    rules = []
    if "market structure shift" in normalized:
        rules.append("Wait for market structure shift confirmation before entry.")
    if "order block" in normalized:
        rules.append("Use order block as a potential entry area.")
    if "fair value gap" in normalized:
        rules.append("Monitor fair value gap for retracement entries.")
    if "liquidity" in normalized:
        rules.append("Evaluate liquidity behavior before reversal assumptions.")
    enriched = dict(chunk)
    enriched["cleaned_ocr"] = cleaned_ocr
    enriched["ocr_quality_score"] = ocr_quality_score
    enriched["semantic"] = {
        "topic": topics[0] if topics else "general",
        "topics": topics,
        "summary": " ".join(text.split())[:400].rstrip(),
        "setup_stages": stages,
        "rule_candidates": rules,
        "search_text": text,
    }
    return enriched
