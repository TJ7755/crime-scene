"""Static, data-driven configuration for the simulation engine."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


EVIDENCE_CATEGORIES = (
    "physical",
    "digital",
    "testimonial",
    "circumstantial",
)


@dataclass(frozen=True)
class CrimeTypeConfig:
    """Defines crime-type specific systemic parameters."""

    name: str
    allowed_evidence_types: tuple[str, ...]
    baseline_hypotheses: Mapping[str, float]
    default_public_pressure: float
    turn_pressure_curve: tuple[float, ...]
    evidence_templates: tuple[Mapping[str, object], ...]


@dataclass(frozen=True)
class PlayerActionConfig:
    """Defines cost/risk/noise settings for one player action."""

    name: str
    costs: Mapping[str, float]
    risk: float
    noise_delta: float


@dataclass(frozen=True)
class InvestigatorActionConfig:
    """Defines one investigator action profile."""

    name: str
    skill_focus: str
    target_categories: tuple[str, ...]
    base_discovery: float
    pressure_weight: float
    fatigue_cost: float
    pressure_delta: float


CRIME_TYPE_CONFIGS: dict[str, CrimeTypeConfig] = {
    "murder": CrimeTypeConfig(
        name="murder",
        allowed_evidence_types=("physical", "digital", "testimonial", "circumstantial"),
        baseline_hypotheses={
            "player_committed_crime": 0.10,
            "alternative_actor": -0.20,
            "non_criminal_explanation": -0.75,
        },
        default_public_pressure=0.90,
        turn_pressure_curve=(0.12, 0.10, 0.09, 0.10, 0.11, 0.12, 0.12, 0.14, 0.15, 0.15),
        evidence_templates=(
            {
                "id": "ev_phys_1",
                "category": "physical",
                "base_reliability": 0.86,
                "detectability": 0.58,
                "manipulability": 0.30,
                "current_credibility": 0.86,
                "hypothesis_impacts": {
                    "player_committed_crime": 0.92,
                    "alternative_actor": -0.35,
                },
            },
            {
                "id": "ev_dig_1",
                "category": "digital",
                "base_reliability": 0.72,
                "detectability": 0.66,
                "manipulability": 0.56,
                "current_credibility": 0.72,
                "hypothesis_impacts": {
                    "player_committed_crime": 0.55,
                    "non_criminal_explanation": -0.25,
                },
            },
            {
                "id": "ev_test_1",
                "category": "testimonial",
                "base_reliability": 0.61,
                "detectability": 0.74,
                "manipulability": 0.72,
                "current_credibility": 0.61,
                "hypothesis_impacts": {
                    "player_committed_crime": 0.40,
                    "alternative_actor": 0.16,
                },
            },
            {
                "id": "ev_circ_1",
                "category": "circumstantial",
                "base_reliability": 0.49,
                "detectability": 0.81,
                "manipulability": 0.79,
                "current_credibility": 0.49,
                "hypothesis_impacts": {
                    "player_committed_crime": 0.28,
                    "non_criminal_explanation": 0.10,
                },
            },
        ),
    ),
    "fraud": CrimeTypeConfig(
        name="fraud",
        allowed_evidence_types=("digital", "testimonial", "circumstantial"),
        baseline_hypotheses={
            "player_committed_crime": 0.22,
            "alternative_actor": -0.30,
            "non_criminal_explanation": -0.35,
        },
        default_public_pressure=0.68,
        turn_pressure_curve=(0.06, 0.06, 0.07, 0.08, 0.08, 0.09, 0.10, 0.10, 0.11, 0.12),
        evidence_templates=(
            {
                "id": "ev_dig_1",
                "category": "digital",
                "base_reliability": 0.89,
                "detectability": 0.62,
                "manipulability": 0.46,
                "current_credibility": 0.89,
                "hypothesis_impacts": {
                    "player_committed_crime": 0.88,
                    "alternative_actor": -0.30,
                },
            },
            {
                "id": "ev_dig_2",
                "category": "digital",
                "base_reliability": 0.74,
                "detectability": 0.70,
                "manipulability": 0.58,
                "current_credibility": 0.74,
                "hypothesis_impacts": {
                    "player_committed_crime": 0.57,
                    "non_criminal_explanation": -0.19,
                },
            },
            {
                "id": "ev_test_1",
                "category": "testimonial",
                "base_reliability": 0.52,
                "detectability": 0.76,
                "manipulability": 0.80,
                "current_credibility": 0.52,
                "hypothesis_impacts": {
                    "player_committed_crime": 0.26,
                    "alternative_actor": 0.14,
                },
            },
            {
                "id": "ev_circ_1",
                "category": "circumstantial",
                "base_reliability": 0.60,
                "detectability": 0.73,
                "manipulability": 0.66,
                "current_credibility": 0.60,
                "hypothesis_impacts": {
                    "player_committed_crime": 0.33,
                    "non_criminal_explanation": 0.08,
                },
            },
        ),
    ),
    "arson": CrimeTypeConfig(
        name="arson",
        allowed_evidence_types=("physical", "digital", "circumstantial"),
        baseline_hypotheses={
            "player_committed_crime": 0.05,
            "alternative_actor": -0.10,
            "non_criminal_explanation": -0.20,
        },
        default_public_pressure=0.82,
        turn_pressure_curve=(0.09, 0.09, 0.08, 0.09, 0.10, 0.11, 0.12, 0.12, 0.13, 0.14),
        evidence_templates=(
            {
                "id": "ev_phys_1",
                "category": "physical",
                "base_reliability": 0.81,
                "detectability": 0.57,
                "manipulability": 0.34,
                "current_credibility": 0.81,
                "hypothesis_impacts": {
                    "player_committed_crime": 0.83,
                    "non_criminal_explanation": -0.26,
                },
            },
            {
                "id": "ev_phys_2",
                "category": "physical",
                "base_reliability": 0.69,
                "detectability": 0.63,
                "manipulability": 0.49,
                "current_credibility": 0.69,
                "hypothesis_impacts": {
                    "player_committed_crime": 0.48,
                    "alternative_actor": 0.12,
                },
            },
            {
                "id": "ev_dig_1",
                "category": "digital",
                "base_reliability": 0.63,
                "detectability": 0.69,
                "manipulability": 0.61,
                "current_credibility": 0.63,
                "hypothesis_impacts": {
                    "player_committed_crime": 0.42,
                    "alternative_actor": 0.10,
                },
            },
            {
                "id": "ev_circ_1",
                "category": "circumstantial",
                "base_reliability": 0.58,
                "detectability": 0.79,
                "manipulability": 0.75,
                "current_credibility": 0.58,
                "hypothesis_impacts": {
                    "player_committed_crime": 0.25,
                    "non_criminal_explanation": 0.14,
                },
            },
        ),
    ),
    "hit_and_run": CrimeTypeConfig(
        name="hit_and_run",
        allowed_evidence_types=("physical", "digital", "testimonial", "circumstantial"),
        baseline_hypotheses={
            "player_committed_crime": 0.08,
            "alternative_actor": -0.22,
            "non_criminal_explanation": -0.50,
        },
        default_public_pressure=0.76,
        turn_pressure_curve=(0.08, 0.08, 0.09, 0.10, 0.10, 0.11, 0.11, 0.12, 0.12, 0.13),
        evidence_templates=(
            {
                "id": "ev_phys_1",
                "category": "physical",
                "base_reliability": 0.78,
                "detectability": 0.61,
                "manipulability": 0.42,
                "current_credibility": 0.78,
                "hypothesis_impacts": {
                    "player_committed_crime": 0.76,
                    "alternative_actor": -0.24,
                },
            },
            {
                "id": "ev_dig_1",
                "category": "digital",
                "base_reliability": 0.71,
                "detectability": 0.64,
                "manipulability": 0.53,
                "current_credibility": 0.71,
                "hypothesis_impacts": {
                    "player_committed_crime": 0.52,
                    "non_criminal_explanation": -0.16,
                },
            },
            {
                "id": "ev_test_1",
                "category": "testimonial",
                "base_reliability": 0.56,
                "detectability": 0.80,
                "manipulability": 0.78,
                "current_credibility": 0.56,
                "hypothesis_impacts": {
                    "player_committed_crime": 0.30,
                    "alternative_actor": 0.18,
                },
            },
            {
                "id": "ev_circ_1",
                "category": "circumstantial",
                "base_reliability": 0.45,
                "detectability": 0.84,
                "manipulability": 0.82,
                "current_credibility": 0.45,
                "hypothesis_impacts": {
                    "player_committed_crime": 0.21,
                    "non_criminal_explanation": 0.16,
                },
            },
        ),
    ),
}


PLAYER_ACTION_CONFIGS: dict[str, PlayerActionConfig] = {
    "remove_evidence": PlayerActionConfig(
        name="remove_evidence",
        costs={"focus": 1.0},
        risk=0.36,
        noise_delta=0.12,
    ),
    "plant_evidence": PlayerActionConfig(
        name="plant_evidence",
        costs={"money": 2.0, "focus": 1.0},
        risk=0.42,
        noise_delta=0.26,
    ),
    "bribe_actor": PlayerActionConfig(
        name="bribe_actor",
        costs={"money": 3.0, "influence": 2.0},
        risk=0.54,
        noise_delta=0.34,
    ),
    "forge_record": PlayerActionConfig(
        name="forge_record",
        costs={"money": 1.0, "focus": 1.5},
        risk=0.46,
        noise_delta=0.22,
    ),
    "leak_to_media": PlayerActionConfig(
        name="leak_to_media",
        costs={"influence": 2.0},
        risk=0.51,
        noise_delta=0.50,
    ),
    "do_nothing": PlayerActionConfig(
        name="do_nothing",
        costs={},
        risk=0.0,
        noise_delta=-0.10,
    ),
}


INVESTIGATOR_ACTION_CONFIGS: dict[str, InvestigatorActionConfig] = {
    "survey_scene": InvestigatorActionConfig(
        name="survey_scene",
        skill_focus="forensic",
        target_categories=("physical", "circumstantial"),
        base_discovery=0.28,
        pressure_weight=0.13,
        fatigue_cost=0.12,
        pressure_delta=0.03,
    ),
    "audit_records": InvestigatorActionConfig(
        name="audit_records",
        skill_focus="analytical",
        target_categories=("digital", "circumstantial"),
        base_discovery=0.26,
        pressure_weight=0.10,
        fatigue_cost=0.10,
        pressure_delta=0.02,
    ),
    "interview_witnesses": InvestigatorActionConfig(
        name="interview_witnesses",
        skill_focus="social",
        target_categories=("testimonial", "circumstantial"),
        base_discovery=0.24,
        pressure_weight=0.17,
        fatigue_cost=0.14,
        pressure_delta=0.04,
    ),
    "press_briefing": InvestigatorActionConfig(
        name="press_briefing",
        skill_focus="social",
        target_categories=(),
        base_discovery=0.0,
        pressure_weight=0.52,
        fatigue_cost=0.06,
        pressure_delta=-0.18,
    ),
}


MIN_LOG_ODDS = -4.0
MAX_LOG_ODDS = 4.0
MAX_PUBLIC_PRESSURE = 3.0
MAX_NOISE_LEVEL = 3.0
LOSS_CONFIDENCE_THRESHOLD = 0.85


def get_crime_type_config(crime_type: str) -> CrimeTypeConfig:
    """Return one supported crime type config."""

    try:
        return CRIME_TYPE_CONFIGS[crime_type]
    except KeyError as exc:
        supported = ", ".join(sorted(CRIME_TYPE_CONFIGS))
        raise ValueError(f"Unsupported crime_type='{crime_type}'. Supported: {supported}") from exc
