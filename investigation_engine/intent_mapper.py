"""Safe rule-based intent mapping sandbox.

This module is a placeholder for future LLM-to-intent mapping. It intentionally
uses fixed rules only and must not execute arbitrary code or trigger side effects.
"""

from __future__ import annotations

from typing import Any

ALLOWED_INTENTS = (
    "remove_evidence",
    "plant_evidence",
    "bribe_actor",
    "forge_record",
    "leak_to_media",
    "do_nothing",
)


def map_text_to_intent(text: str) -> tuple[str, dict[str, Any], float]:
    """Map free text to a supported game intent using simple keyword rules."""

    normalized = " ".join(text.strip().lower().replace("-", "_").split())
    if not normalized:
        return "do_nothing", {}, 1.0
    if normalized in ALLOWED_INTENTS:
        return normalized, {}, 1.0
    if "remove" in normalized and "evidence" in normalized:
        return "remove_evidence", {}, 0.9
    if "plant" in normalized and "evidence" in normalized:
        return "plant_evidence", {}, 0.9
    if "bribe" in normalized:
        return "bribe_actor", {}, 0.9
    if "forge" in normalized and ("record" in normalized or "records" in normalized):
        return "forge_record", {}, 0.9
    if "leak" in normalized and "media" in normalized:
        return "leak_to_media", {}, 0.9
    return "do_nothing", {}, 1.0
