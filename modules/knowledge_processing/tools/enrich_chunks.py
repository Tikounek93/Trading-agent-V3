"""Advisory topic, stage and rule-candidate enrichment."""

from __future__ import annotations

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


def enrich_chunk(chunk: dict[str, Any]) -> dict[str, Any]:
    text = "\n".join(
        (
            str(chunk.get("combined_transcript") or ""),
            str(chunk.get("combined_ocr") or ""),
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
    enriched["semantic"] = {
        "topic": topics[0] if topics else "general",
        "topics": topics,
        "summary": " ".join(text.split())[:400].rstrip(),
        "setup_stages": stages,
        "rule_candidates": rules,
        "search_text": text,
    }
    return enriched
