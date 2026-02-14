"""Belief update and confidence utility functions."""

from __future__ import annotations

import math

from .config import MAX_LOG_ODDS, MIN_LOG_ODDS
from .models import Evidence, InvestigatorState


CATEGORY_TO_SKILL = {
    "physical": "forensic",
    "digital": "analytical",
    "testimonial": "social",
    "circumstantial": "analytical",
}


def clamp(value: float, lower: float, upper: float) -> float:
    """Clamp one float into the inclusive [lower, upper] range."""

    if value < lower:
        return lower
    if value > upper:
        return upper
    return value


def log_odds_to_probability(log_odds: float) -> float:
    """Convert log-odds to probability."""

    return 1.0 / (1.0 + math.exp(-log_odds))


def probability_to_log_odds(probability: float) -> float:
    """Convert probability to log-odds."""

    p = clamp(probability, 1e-6, 1.0 - 1e-6)
    return math.log(p / (1.0 - p))


def hypothesis_probabilities(log_odds_map: dict[str, float]) -> dict[str, float]:
    """Convert each hypothesis log-odds value into probability."""

    return {name: log_odds_to_probability(value) for name, value in log_odds_map.items()}


def update_hypotheses_with_evidence(
    hypotheses_log_odds: dict[str, float],
    evidence: Evidence,
    investigator: InvestigatorState,
    public_pressure: float,
    action_skill_focus: str | None = None,
    clip_bounds: tuple[float, float] = (MIN_LOG_ODDS, MAX_LOG_ODDS),
) -> dict[str, float]:
    """
    Apply one evidence item to hypothesis log-odds.

    Influence is weighted by evidence reliability/credibility, relevant skill,
    investigator learning rate, configured hypothesis impacts, and bounded clipping.
    """

    lower, upper = clip_bounds
    updated = dict(hypotheses_log_odds)
    primary_skill_name = CATEGORY_TO_SKILL.get(evidence.category, "analytical")
    primary_skill = clamp(investigator.skills.get(primary_skill_name, 0.5), 0.1, 1.5)
    focus_bonus = 1.10 if action_skill_focus == primary_skill_name else 1.0
    pressure_factor = 1.0 + clamp(public_pressure, 0.0, 2.0) * 0.08
    corruption_penalty = 1.0 - clamp(
        investigator.compromised * investigator.corruption_susceptibility * 0.25,
        0.0,
        0.8,
    )
    interpretation_strength = (
        evidence.base_reliability
        * evidence.current_credibility
        * primary_skill
        * focus_bonus
        * pressure_factor
        * corruption_penalty
    )

    for hypothesis, impact in evidence.hypothesis_impacts.items():
        if hypothesis not in updated:
            updated[hypothesis] = 0.0
        bias_adjustment = investigator.biases.get(hypothesis, 0.0) * 0.05
        delta = investigator.learning_rate * interpretation_strength * impact + bias_adjustment
        updated[hypothesis] = clamp(updated[hypothesis] + delta, lower, upper)

    return updated
