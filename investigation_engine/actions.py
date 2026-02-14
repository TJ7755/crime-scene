"""Turn action selection and action resolution systems."""

from __future__ import annotations

from dataclasses import dataclass

from .beliefs import clamp, log_odds_to_probability, update_hypotheses_with_evidence
from .config import (
    INVESTIGATOR_ACTION_CONFIGS,
    MAX_NOISE_LEVEL,
    MAX_PUBLIC_PRESSURE,
    PLAYER_ACTION_CONFIGS,
)
from .models import Evidence, GameState


@dataclass(frozen=True)
class InvestigatorTurnResult:
    """Result payload for one investigator action step."""

    action: str
    discovered_evidence_ids: tuple[str, ...]


@dataclass(frozen=True)
class PlayerActionResult:
    """Result payload for one player action step."""

    requested_action: str
    resolved_action: str
    success: bool
    details: str


def available_player_actions() -> tuple[str, ...]:
    """Return the fixed set of supported player actions."""

    return tuple(PLAYER_ACTION_CONFIGS.keys())


def choose_investigator_action(state: GameState) -> str:
    """Select one investigator action based only on observable system signals."""

    investigator = state.investigator_state
    player_conf = log_odds_to_probability(
        investigator.hypotheses_log_odds.get("player_committed_crime", 0.0)
    )
    uncertainty = 1.0 - abs(player_conf - 0.5) * 2.0
    active_evidence_count = sum(1 for item in state.evidence_registry.values() if item.active)
    visible_evidence_count = len(state.visible_evidence)
    investigation_need = 1.0 - (visible_evidence_count / max(active_evidence_count, 1))
    best_action = None
    best_score = float("-inf")

    for name, config in INVESTIGATOR_ACTION_CONFIGS.items():
        skill_value = investigator.skills.get(config.skill_focus, 0.5)
        score = (
            config.base_discovery * 0.70
            + skill_value * 0.55
            + state.public_pressure * config.pressure_weight
            + uncertainty * 0.22
            - investigator.fatigue * config.fatigue_cost * 0.70
        )
        if config.target_categories:
            score += investigation_need * 0.24
        if name == "press_briefing":
            score += max(state.public_pressure - 1.0, 0.0) * 0.70
            score -= 0.32 + investigation_need * 0.18
        if investigator.action_history:
            if investigator.action_history[-1] == name:
                score -= 0.14
            if len(investigator.action_history) >= 2 and investigator.action_history[-2] == name:
                score -= 0.10
        score += state.rng.random() * 0.03
        if best_action is None or score > best_score:
            best_action = name
            best_score = score

    assert best_action is not None
    return best_action


def perform_investigator_turn(state: GameState) -> InvestigatorTurnResult:
    """Execute one investigator action and discover evidence probabilistically."""

    action_name = choose_investigator_action(state)
    config = INVESTIGATOR_ACTION_CONFIGS[action_name]
    investigator = state.investigator_state
    investigator.action_history.append(action_name)
    investigator.fatigue = clamp(
        investigator.fatigue + config.fatigue_cost - investigator.patience * 0.03, 0.0, 2.0
    )
    state.public_pressure = clamp(
        state.public_pressure + config.pressure_delta, 0.0, MAX_PUBLIC_PRESSURE
    )

    discovered_ids: list[str] = []
    if config.target_categories:
        for evidence in state.evidence_registry.values():
            if evidence.discovered or not evidence.active:
                continue
            if evidence.category not in config.target_categories:
                continue

            skill_value = clamp(investigator.skills.get(config.skill_focus, 0.5), 0.1, 1.5)
            discovery_chance = evidence.detectability * config.base_discovery
            discovery_chance *= 0.70 + skill_value * 0.60
            discovery_chance *= 1.0 / (1.0 + state.noise_level * 0.35)
            discovery_chance *= 1.0 - clamp(
                investigator.compromised * investigator.corruption_susceptibility * 0.40,
                0.0,
                0.8,
            )
            discovery_chance *= 1.0 - clamp(investigator.fatigue * 0.25, 0.0, 0.5)
            discovery_chance *= 1.0 + clamp(state.public_pressure, 0.0, 2.0) * 0.05
            discovery_chance = clamp(discovery_chance, 0.0, 0.95)

            if state.rng.random() < discovery_chance:
                evidence.discovered = True
                discovered_ids.append(evidence.id)
                investigator.hypotheses_log_odds = update_hypotheses_with_evidence(
                    hypotheses_log_odds=investigator.hypotheses_log_odds,
                    evidence=evidence,
                    investigator=investigator,
                    public_pressure=state.public_pressure,
                    action_skill_focus=config.skill_focus,
                )

    return InvestigatorTurnResult(action=action_name, discovered_evidence_ids=tuple(discovered_ids))


def apply_player_action(state: GameState, requested_action: str) -> PlayerActionResult:
    """Apply one player action, including costs, risk, and world-state effects."""

    resolved_action = requested_action if requested_action in PLAYER_ACTION_CONFIGS else "do_nothing"
    config = PLAYER_ACTION_CONFIGS[resolved_action]
    details = "ok"

    if not _can_pay_costs(state.player_state.resources, config.costs):
        resolved_action = "do_nothing"
        config = PLAYER_ACTION_CONFIGS["do_nothing"]
        details = "insufficient_resources"

    _pay_costs(state.player_state.resources, config.costs)
    state.player_state.actions_taken.append(resolved_action)
    state.noise_level = clamp(state.noise_level + config.noise_delta, 0.0, MAX_NOISE_LEVEL)

    if resolved_action == "do_nothing":
        success = True
    else:
        adjusted_risk = clamp(
            config.risk + state.noise_level * 0.05 + state.public_pressure * 0.04,
            0.0,
            0.95,
        )
        success = state.rng.random() >= adjusted_risk
        state.player_state.risk_exposure = clamp(
            state.player_state.risk_exposure + adjusted_risk * 0.10, 0.0, 3.0
        )

    effect_details = _resolve_player_effect(state, resolved_action, success)
    if details != "ok":
        effect_details = f"{details}; {effect_details}"
    return PlayerActionResult(
        requested_action=requested_action,
        resolved_action=resolved_action,
        success=success,
        details=effect_details,
    )


def _resolve_player_effect(state: GameState, action: str, success: bool) -> str:
    if action == "remove_evidence":
        return _effect_remove_evidence(state, success)
    if action == "plant_evidence":
        return _effect_plant_evidence(state, success)
    if action == "bribe_actor":
        return _effect_bribe_actor(state, success)
    if action == "forge_record":
        return _effect_forge_record(state, success)
    if action == "leak_to_media":
        return _effect_leak_to_media(state, success)
    state.noise_level = clamp(state.noise_level - 0.08, 0.0, MAX_NOISE_LEVEL)
    return "standby"


def _effect_remove_evidence(state: GameState, success: bool) -> str:
    if success:
        hidden_targets = [item for item in state.evidence_registry.values() if item.active and not item.discovered]
        if hidden_targets:
            target = max(hidden_targets, key=lambda item: item.detectability * item.manipulability)
            concealment_strength = clamp(0.18 + target.manipulability * 0.45, 0.05, 0.65)
            target.detectability = clamp(target.detectability * (1.0 - concealment_strength), 0.04, 1.0)
            target.current_credibility = clamp(
                target.current_credibility * (1.0 - concealment_strength * 0.35),
                0.05,
                1.0,
            )
            if state.rng.random() < target.manipulability * 0.30:
                target.active = False
                return f"concealed:{target.id}:removed"
            return f"concealed:{target.id}:reduced"
        visible_targets = [item for item in state.visible_evidence if item.active]
        if visible_targets:
            target = max(visible_targets, key=lambda item: item.current_credibility)
            target.current_credibility = clamp(target.current_credibility * 0.65, 0.05, 1.0)
            return f"degraded:{target.id}"
        return "no_target"

    _add_generated_evidence(
        state=state,
        prefix="tamper_trace",
        category="physical",
        base_reliability=0.74,
        detectability=0.77,
        manipulability=0.20,
        credibility=0.74,
        impacts={"player_committed_crime": 0.62, "alternative_actor": -0.20},
    )
    state.public_pressure = clamp(state.public_pressure + 0.12, 0.0, MAX_PUBLIC_PRESSURE)
    return "backfire:tamper_trace_added"


def _effect_plant_evidence(state: GameState, success: bool) -> str:
    if success:
        category = "circumstantial"
        if "digital" in state.case_data.allowed_evidence_types and state.rng.random() < 0.4:
            category = "digital"
        new_evidence = _add_generated_evidence(
            state=state,
            prefix="planted",
            category=category,
            base_reliability=0.35 + state.rng.random() * 0.18,
            detectability=0.68,
            manipulability=0.74,
            credibility=0.45 + state.rng.random() * 0.20,
            impacts={
                "player_committed_crime": -0.34,
                "alternative_actor": 0.40,
                "non_criminal_explanation": 0.16,
            },
        )
        return f"planted:{new_evidence.id}"

    _add_generated_evidence(
        state=state,
        prefix="plant_trace",
        category="circumstantial",
        base_reliability=0.71,
        detectability=0.79,
        manipulability=0.25,
        credibility=0.71,
        impacts={"player_committed_crime": 0.58, "alternative_actor": -0.14},
    )
    state.public_pressure = clamp(state.public_pressure + 0.10, 0.0, MAX_PUBLIC_PRESSURE)
    return "backfire:plant_trace_added"


def _effect_bribe_actor(state: GameState, success: bool) -> str:
    if success:
        gain = 0.18 + 0.20 * state.investigator_state.corruption_susceptibility
        state.investigator_state.compromised = clamp(
            state.investigator_state.compromised + gain, 0.0, 1.0
        )
        state.public_pressure = clamp(state.public_pressure - 0.05, 0.0, MAX_PUBLIC_PRESSURE)
        return f"investigator_compromised:+{gain:.2f}"

    _add_generated_evidence(
        state=state,
        prefix="bribe_trace",
        category="testimonial",
        base_reliability=0.80,
        detectability=0.83,
        manipulability=0.22,
        credibility=0.80,
        impacts={"player_committed_crime": 0.72, "alternative_actor": -0.24},
    )
    state.public_pressure = clamp(state.public_pressure + 0.22, 0.0, MAX_PUBLIC_PRESSURE)
    return "backfire:bribe_trace_added"


def _effect_forge_record(state: GameState, success: bool) -> str:
    digital_targets = [
        item
        for item in state.evidence_registry.values()
        if item.active and item.category == "digital" and not item.discovered
    ]
    if success:
        if digital_targets:
            target = max(digital_targets, key=lambda item: item.manipulability)
            target.current_credibility = clamp(
                target.current_credibility - 0.30 * target.manipulability, 0.05, 1.0
            )
            target.hypothesis_impacts["player_committed_crime"] = (
                target.hypothesis_impacts.get("player_committed_crime", 0.0) * 0.65
            )
            target.hypothesis_impacts["alternative_actor"] = (
                target.hypothesis_impacts.get("alternative_actor", 0.0) + 0.18
            )
            return f"forged:{target.id}"
        generated = _add_generated_evidence(
            state=state,
            prefix="forged_record",
            category="digital",
            base_reliability=0.40,
            detectability=0.70,
            manipulability=0.82,
            credibility=0.42,
            impacts={
                "player_committed_crime": -0.28,
                "alternative_actor": 0.24,
                "non_criminal_explanation": 0.12,
            },
        )
        return f"forged:{generated.id}"

    _add_generated_evidence(
        state=state,
        prefix="audit_anomaly",
        category="digital",
        base_reliability=0.76,
        detectability=0.82,
        manipulability=0.20,
        credibility=0.76,
        impacts={"player_committed_crime": 0.66, "alternative_actor": -0.20},
    )
    state.public_pressure = clamp(state.public_pressure + 0.16, 0.0, MAX_PUBLIC_PRESSURE)
    return "backfire:audit_anomaly_added"


def _effect_leak_to_media(state: GameState, success: bool) -> str:
    if success:
        state.public_pressure = clamp(state.public_pressure - 0.24, 0.0, MAX_PUBLIC_PRESSURE)
        state.noise_level = clamp(state.noise_level + 0.15, 0.0, MAX_NOISE_LEVEL)
        return "pressure_reduced"

    _add_generated_evidence(
        state=state,
        prefix="media_trace",
        category="testimonial",
        base_reliability=0.68,
        detectability=0.73,
        manipulability=0.26,
        credibility=0.68,
        impacts={"player_committed_crime": 0.46, "alternative_actor": -0.12},
    )
    state.public_pressure = clamp(state.public_pressure + 0.36, 0.0, MAX_PUBLIC_PRESSURE)
    return "backfire:media_trace_added"


def _can_pay_costs(resources: dict[str, float], costs: dict[str, float] | object) -> bool:
    costs_dict = dict(costs)
    return all(resources.get(name, 0.0) >= required for name, required in costs_dict.items())


def _pay_costs(resources: dict[str, float], costs: dict[str, float] | object) -> None:
    for name, required in dict(costs).items():
        resources[name] = round(resources.get(name, 0.0) - required, 4)


def _add_generated_evidence(
    state: GameState,
    prefix: str,
    category: str,
    base_reliability: float,
    detectability: float,
    manipulability: float,
    credibility: float,
    impacts: dict[str, float],
) -> Evidence:
    allowed_types = set(state.case_data.allowed_evidence_types)
    final_category = category if category in allowed_types else "circumstantial"
    if final_category not in allowed_types:
        final_category = state.case_data.allowed_evidence_types[0]

    evidence_id = _next_dynamic_evidence_id(state, prefix)
    evidence = Evidence(
        id=evidence_id,
        category=final_category,
        base_reliability=clamp(base_reliability, 0.05, 1.0),
        detectability=clamp(detectability, 0.05, 1.0),
        manipulability=clamp(manipulability, 0.0, 1.0),
        current_credibility=clamp(credibility, 0.05, 1.0),
        discovered=False,
        active=True,
        hypothesis_impacts=dict(impacts),
    )
    state.evidence_registry[evidence.id] = evidence
    return evidence


def _next_dynamic_evidence_id(state: GameState, prefix: str) -> str:
    index = 1
    while True:
        candidate = f"{prefix}_{state.turn}_{index}"
        if candidate not in state.evidence_registry:
            return candidate
        index += 1
