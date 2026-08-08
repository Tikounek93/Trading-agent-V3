"""Deterministic domain-event extraction from transcript and OCR text."""

from __future__ import annotations

from typing import Any


EVENT_PATTERNS = {
    "fair_value_gap": ("fair value gap", "fvg"),
    "market_structure_shift": ("market structure shift", "mss"),
    "liquidity_sweep": ("liquidity sweep", "sweep liquidity", "liquidity run"),
    "buy_side_liquidity": ("buy side liquidity", "buyside liquidity", "bsl"),
    "sell_side_liquidity": ("sell side liquidity", "sellside liquidity", "ssl"),
    "order_block": ("order block",),
    "breaker": ("breaker",),
    "displacement": ("displacement",),
    "premium_discount": ("premium", "discount"),
    "dealing_range": ("dealing range",),
    "ote": ("optimal trade entry", "ote"),
}


def extract_events(text: str, *, source: str = "transcript") -> list[dict[str, Any]]:
    normalized = text.lower().strip()
    events = []
    for event_type, keywords in EVENT_PATTERNS.items():
        for keyword in keywords:
            if keyword in normalized:
                events.append(
                    {
                        "type": event_type,
                        "keyword": keyword,
                        "confidence": 0.9,
                        "source": source,
                    }
                )
    return events
