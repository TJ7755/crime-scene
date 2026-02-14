"""Core data models for deterministic simulation state."""

from __future__ import annotations

from collections.abc import Iterable
import logging
import random
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


def _serialize_rng_state(state: Any) -> Any:
    """Convert random state into a JSON-serializable structure."""

    if state is None or isinstance(state, (int, float, str, bool)):
        return state
    if isinstance(state, dict):
        return {str(key): _serialize_rng_state(value) for key, value in state.items()}
    if isinstance(state, Iterable) and not isinstance(state, (str, bytes, bytearray)):
        return [_serialize_rng_state(item) for item in state]
    return state


def _deserialize_rng_state(data: Any) -> Any:
    """Reconstruct random state tuples from a JSON-serialized structure."""

    if data is None or isinstance(data, (int, float, str, bool)):
        return data
    if isinstance(data, dict):
        return {str(key): _deserialize_rng_state(value) for key, value in data.items()}
    if isinstance(data, list):
        return tuple(_deserialize_rng_state(item) for item in data)
    return data


@dataclass
class Evidence:
    """Evidence unit tracked by the simulation."""

    id: str
    category: str
    base_reliability: float
    detectability: float
    manipulability: float
    current_credibility: float
    discovered: bool = False
    active: bool = True
    hypothesis_impacts: dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Return JSON-safe dictionary representation."""

        return {
            "id": self.id,
            "category": self.category,
            "base_reliability": self.base_reliability,
            "detectability": self.detectability,
            "manipulability": self.manipulability,
            "current_credibility": self.current_credibility,
            "discovered": self.discovered,
            "active": self.active,
            "hypothesis_impacts": dict(self.hypothesis_impacts),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Evidence":
        """Build an Evidence instance from serialized data."""

        return cls(
            id=str(data["id"]),
            category=str(data["category"]),
            base_reliability=float(data["base_reliability"]),
            detectability=float(data["detectability"]),
            manipulability=float(data["manipulability"]),
            current_credibility=float(data["current_credibility"]),
            discovered=bool(data["discovered"]),
            active=bool(data["active"]),
            hypothesis_impacts={
                str(key): float(value) for key, value in dict(data["hypothesis_impacts"]).items()
            },
        )


@dataclass
class PlayerState:
    """Player-facing resources and action history."""

    resources: dict[str, float]
    actions_taken: list[str] = field(default_factory=list)
    risk_exposure: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        """Return JSON-safe dictionary representation."""

        return {
            "resources": {str(k): float(v) for k, v in self.resources.items()},
            "actions_taken": list(self.actions_taken),
            "risk_exposure": self.risk_exposure,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PlayerState":
        """Build a PlayerState instance from serialized data."""

        return cls(
            resources={str(key): float(value) for key, value in dict(data["resources"]).items()},
            actions_taken=[str(item) for item in list(data["actions_taken"])],
            risk_exposure=float(data["risk_exposure"]),
        )


@dataclass
class InvestigatorState:
    """Hidden investigator model state."""

    hypotheses_log_odds: dict[str, float]
    skills: dict[str, float]
    biases: dict[str, float]
    patience: float
    fatigue: float
    learning_rate: float
    corruption_susceptibility: float
    compromised: float = 0.0
    action_history: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Return JSON-safe dictionary representation."""

        return {
            "hypotheses_log_odds": {
                str(key): float(value) for key, value in self.hypotheses_log_odds.items()
            },
            "skills": {str(key): float(value) for key, value in self.skills.items()},
            "biases": {str(key): float(value) for key, value in self.biases.items()},
            "patience": self.patience,
            "fatigue": self.fatigue,
            "learning_rate": self.learning_rate,
            "corruption_susceptibility": self.corruption_susceptibility,
            "compromised": self.compromised,
            "action_history": list(self.action_history),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "InvestigatorState":
        """Build an InvestigatorState instance from serialized data."""

        return cls(
            hypotheses_log_odds={
                str(key): float(value) for key, value in dict(data["hypotheses_log_odds"]).items()
            },
            skills={str(key): float(value) for key, value in dict(data["skills"]).items()},
            biases={str(key): float(value) for key, value in dict(data["biases"]).items()},
            patience=float(data["patience"]),
            fatigue=float(data["fatigue"]),
            learning_rate=float(data["learning_rate"]),
            corruption_susceptibility=float(data["corruption_susceptibility"]),
            compromised=float(data["compromised"]),
            action_history=[str(item) for item in list(data["action_history"])],
        )


@dataclass
class CaseData:
    """Case-level metadata, independent of transient turn state."""

    crime_type: str
    timeline: list[str]
    allowed_evidence_types: list[str]
    turn_pressure_curve: list[float]

    def to_dict(self) -> dict[str, Any]:
        """Return JSON-safe dictionary representation."""

        return {
            "crime_type": self.crime_type,
            "timeline": list(self.timeline),
            "allowed_evidence_types": list(self.allowed_evidence_types),
            "turn_pressure_curve": [float(value) for value in self.turn_pressure_curve],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CaseData":
        """Build CaseData from serialized data."""

        return cls(
            crime_type=str(data["crime_type"]),
            timeline=[str(item) for item in list(data["timeline"])],
            allowed_evidence_types=[str(item) for item in list(data["allowed_evidence_types"])],
            turn_pressure_curve=[float(value) for value in list(data["turn_pressure_curve"])],
        )


@dataclass
class GameState:
    """Central mutable state object for the simulation loop."""

    turn: int
    day: int
    case_data: CaseData
    evidence_registry: dict[str, Evidence]
    player_state: PlayerState
    investigator_state: InvestigatorState
    public_pressure: float
    noise_level: float
    seed: int
    rng: random.Random = field(repr=False, compare=False)

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-safe serialization of all state, including RNG state."""

        return {
            "turn": self.turn,
            "day": self.day,
            "case_data": self.case_data.to_dict(),
            "evidence_registry": {
                str(key): evidence.to_dict() for key, evidence in self.evidence_registry.items()
            },
            "player_state": self.player_state.to_dict(),
            "investigator_state": self.investigator_state.to_dict(),
            "public_pressure": self.public_pressure,
            "noise_level": self.noise_level,
            "seed": self.seed,
            "rng_state": _serialize_rng_state(self.rng.getstate()),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "GameState":
        """Restore GameState from serialized JSON-safe data."""

        seed_raw = data.get("seed")
        if seed_raw is None:
            raise ValueError("Serialized GameState is missing required 'seed'.")
        seed = int(seed_raw)
        rng = random.Random(seed)
        rng_state_data = data.get("rng_state")
        if rng_state_data is None:
            logger.warning(
                "Serialized GameState missing 'rng_state'; falling back to seed-based RNG initialization."
            )
        else:
            try:
                rng.setstate(_deserialize_rng_state(rng_state_data))
            except (TypeError, ValueError) as exc:
                raise ValueError("Serialized GameState contains invalid 'rng_state'.") from exc
        return cls(
            turn=int(data["turn"]),
            day=int(data["day"]),
            case_data=CaseData.from_dict(dict(data["case_data"])),
            evidence_registry={
                str(key): Evidence.from_dict(dict(value))
                for key, value in dict(data["evidence_registry"]).items()
            },
            player_state=PlayerState.from_dict(dict(data["player_state"])),
            investigator_state=InvestigatorState.from_dict(dict(data["investigator_state"])),
            public_pressure=float(data["public_pressure"]),
            noise_level=float(data["noise_level"]),
            seed=seed,
            rng=rng,
        )

    @property
    def visible_evidence(self) -> list[Evidence]:
        """Evidence currently known to the investigator."""

        return [item for item in self.evidence_registry.values() if item.discovered and item.active]
