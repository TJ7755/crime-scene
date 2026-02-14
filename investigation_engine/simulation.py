"""High-level game loop and engine orchestration."""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import random
from dataclasses import dataclass
from typing import Callable

from .actions import (
    InvestigatorTurnResult,
    PlayerActionResult,
    apply_player_action,
    perform_investigator_turn,
)
from .beliefs import clamp, log_odds_to_probability
from .config import (
    LOSS_CONFIDENCE_THRESHOLD,
    MAX_NOISE_LEVEL,
    MAX_PUBLIC_PRESSURE,
    get_crime_type_config,
)
from .models import CaseData, Evidence, GameState, InvestigatorState, PlayerState

SAVE_FORMAT_VERSION = 1


@dataclass(frozen=True)
class Outcome:
    """Terminal/non-terminal outcome state for one point in the simulation."""

    ended: bool
    player_lost: bool
    reason: str


@dataclass(frozen=True)
class TurnReport:
    """Summary of one completed turn."""

    turn: int
    day: int
    investigator_action: str
    discovered_evidence_ids: tuple[str, ...]
    player_action_requested: str
    player_action_resolved: str
    player_action_success: bool
    player_action_details: str
    public_pressure: float
    noise_level: float
    visible_evidence_count: int
    outcome: Outcome


class GameEngine:
    """Owns simulation state and executes deterministic turn progression."""

    def __init__(
        self,
        crime_type: str,
        seed: int,
        max_turns: int = 20,
        loss_confidence_threshold: float = LOSS_CONFIDENCE_THRESHOLD,
    ) -> None:
        self.max_turns = max_turns
        self.loss_confidence_threshold = loss_confidence_threshold
        self.state = self._build_initial_state(crime_type=crime_type, seed=seed, max_turns=max_turns)

    def step(self, player_action: str) -> TurnReport:
        """Advance one turn through investigator phase, discovery, player phase, and checks."""

        self.state.turn += 1
        self.state.day += 1
        self._apply_turn_pressure()

        investigator_result = perform_investigator_turn(self.state)
        player_result = apply_player_action(self.state, player_action)
        self._apply_passive_dynamics()
        outcome = self.evaluate_outcome()

        return TurnReport(
            turn=self.state.turn,
            day=self.state.day,
            investigator_action=investigator_result.action,
            discovered_evidence_ids=investigator_result.discovered_evidence_ids,
            player_action_requested=player_result.requested_action,
            player_action_resolved=player_result.resolved_action,
            player_action_success=player_result.success,
            player_action_details=player_result.details,
            public_pressure=round(self.state.public_pressure, 4),
            noise_level=round(self.state.noise_level, 4),
            visible_evidence_count=len(self.state.visible_evidence),
            outcome=outcome,
        )

    def run(
        self,
        player_policy: Callable[[GameState], str],
        turns: int | None = None,
    ) -> tuple[list[TurnReport], Outcome]:
        """Run repeated turns using the supplied player policy callable."""

        limit = turns if turns is not None else self.max_turns
        reports: list[TurnReport] = []
        outcome = self.evaluate_outcome()
        while len(reports) < limit and not outcome.ended:
            action = player_policy(self.state)
            report = self.step(action)
            reports.append(report)
            outcome = report.outcome
        return reports, outcome

    def save(self, path: str | Path) -> None:
        """Persist the current game state as versioned JSON."""

        save_path = Path(path)
        save_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "format_version": SAVE_FORMAT_VERSION,
            "saved_at": datetime.now(timezone.utc).isoformat(),
            "state": self.state.to_dict(),
        }
        with save_path.open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2)

    @classmethod
    def load(cls, path: str | Path) -> "GameEngine":
        """Restore a saved engine state from disk."""

        load_path = Path(path)
        with load_path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)

        if not isinstance(payload, dict):
            raise ValueError("Invalid save file: expected a top-level JSON object.")
        format_version = payload.get("format_version")
        if format_version != SAVE_FORMAT_VERSION:
            raise ValueError(
                f"Incompatible save format_version {format_version!r}; expected {SAVE_FORMAT_VERSION}."
            )
        state_data = payload.get("state")
        if not isinstance(state_data, dict):
            raise ValueError("Invalid save file: missing 'state' object.")

        state = GameState.from_dict(state_data)
        engine = cls(
            crime_type=state.case_data.crime_type,
            seed=state.seed,
            max_turns=len(state.case_data.timeline),
        )
        engine.state = state
        return engine

    def evaluate_outcome(self) -> Outcome:
        """Evaluate abstract loss/exit conditions."""

        suspicion_probability = log_odds_to_probability(
            self.state.investigator_state.hypotheses_log_odds.get("player_committed_crime", 0.0)
        )
        if suspicion_probability >= self.loss_confidence_threshold:
            return Outcome(
                ended=True,
                player_lost=True,
                reason="confidence_threshold_exceeded",
            )
        if self.state.public_pressure >= MAX_PUBLIC_PRESSURE:
            return Outcome(
                ended=True,
                player_lost=True,
                reason="public_pressure_overload",
            )
        if self.state.turn >= self.max_turns:
            return Outcome(
                ended=True,
                player_lost=False,
                reason="max_turns_reached",
            )
        return Outcome(
            ended=False,
            player_lost=False,
            reason="ongoing",
        )

    def _apply_turn_pressure(self) -> None:
        """Increase public pressure using crime-specific curve values."""

        curve = self.state.case_data.turn_pressure_curve
        curve_index = min(max(self.state.turn - 1, 0), len(curve) - 1)
        self.state.public_pressure = clamp(
            self.state.public_pressure + curve[curve_index], 0.0, MAX_PUBLIC_PRESSURE
        )

    def _apply_passive_dynamics(self) -> None:
        """Apply deterministic passive effects once per turn."""

        investigator = self.state.investigator_state
        investigator.compromised = clamp(investigator.compromised - 0.03, 0.0, 1.0)
        investigator.fatigue = clamp(investigator.fatigue - 0.02, 0.0, 2.0)
        self.state.noise_level = clamp(self.state.noise_level * 0.98, 0.0, MAX_NOISE_LEVEL)

    @staticmethod
    def _build_initial_state(crime_type: str, seed: int, max_turns: int) -> GameState:
        crime_config = get_crime_type_config(crime_type)
        rng = random.Random(seed)
        timeline = [f"turn_{index + 1}" for index in range(max_turns)]
        case_data = CaseData(
            crime_type=crime_config.name,
            timeline=timeline,
            allowed_evidence_types=list(crime_config.allowed_evidence_types),
            turn_pressure_curve=list(crime_config.turn_pressure_curve),
        )
        evidence_registry = {
            template_id: _evidence_from_template(crime_type, template_data)
            for template_id, template_data in _iter_evidence_templates(crime_type, crime_config.evidence_templates)
        }
        player_state = PlayerState(
            resources={
                "money": 12.0,
                "influence": 8.0,
                "focus": 10.0,
            }
        )
        investigator_state = _build_investigator_state(crime_config.baseline_hypotheses, rng)
        return GameState(
            turn=0,
            day=0,
            case_data=case_data,
            evidence_registry=evidence_registry,
            player_state=player_state,
            investigator_state=investigator_state,
            public_pressure=crime_config.default_public_pressure,
            noise_level=0.0,
            seed=seed,
            rng=rng,
        )


def _iter_evidence_templates(
    crime_type: str,
    templates: tuple[dict[str, object] | object, ...],
) -> list[tuple[str, dict[str, object]]]:
    items: list[tuple[str, dict[str, object]]] = []
    for template in templates:
        template_dict = dict(template)
        evidence_id = f"{crime_type}_{template_dict['id']}"
        items.append((evidence_id, template_dict))
    return items


def _evidence_from_template(crime_type: str, template: dict[str, object]) -> Evidence:
    return Evidence(
        id=f"{crime_type}_{template['id']}",
        category=str(template["category"]),
        base_reliability=float(template["base_reliability"]),
        detectability=float(template["detectability"]),
        manipulability=float(template["manipulability"]),
        current_credibility=float(template["current_credibility"]),
        discovered=False,
        active=True,
        hypothesis_impacts={str(key): float(value) for key, value in dict(template["hypothesis_impacts"]).items()},
    )


def _build_investigator_state(
    baseline_hypotheses: dict[str, float] | object,
    rng: random.Random,
) -> InvestigatorState:
    hypotheses = {str(key): float(value) for key, value in dict(baseline_hypotheses).items()}
    skills = {
        "forensic": round(0.55 + rng.random() * 0.35, 4),
        "social": round(0.50 + rng.random() * 0.35, 4),
        "analytical": round(0.58 + rng.random() * 0.30, 4),
    }
    biases = {key: round(rng.uniform(-0.08, 0.08), 4) for key in hypotheses}
    return InvestigatorState(
        hypotheses_log_odds=hypotheses,
        skills=skills,
        biases=biases,
        patience=round(0.45 + rng.random() * 0.45, 4),
        fatigue=0.0,
        learning_rate=round(0.58 + rng.random() * 0.20, 4),
        corruption_susceptibility=round(0.20 + rng.random() * 0.35, 4),
    )
