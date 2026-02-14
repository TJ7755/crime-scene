"""Mapper to convert GameState to frontend VisibleState JSON format."""

from __future__ import annotations

from typing import Any

from .actions import available_player_actions
from .beliefs import log_odds_to_probability
from .config import PLAYER_ACTION_CONFIGS
from .models import Evidence, GameState


def _map_pressure_to_label(pressure: float) -> str:
    """Convert numeric pressure to qualitative label."""
    if pressure < 0.5:
        return "low"
    elif pressure < 1.0:
        return "moderate"
    elif pressure < 1.5:
        return "elevated"
    elif pressure < 2.0:
        return "high"
    else:
        return "critical"


def _map_evidence_state(evidence: Evidence, state: GameState) -> str:
    """Map evidence to a state descriptor."""
    if not evidence.active:
        return "archived"
    if not evidence.discovered:
        return "logged"
    # Evidence is discovered and active
    if evidence.current_credibility < 0.3:
        return "suppressed"
    elif evidence.current_credibility < 0.6:
        return "review"
    else:
        return "surfaced"


def _generate_evidence_summary(evidence: Evidence) -> str:
    """Generate a summary description for evidence."""
    reliability_desc = "probable" if evidence.current_credibility > 0.6 else "uncertain"
    
    # Add qualitative descriptors based on attributes
    if evidence.manipulability > 0.7:
        integrity_desc = "contradictory"
    elif evidence.manipulability > 0.4:
        integrity_desc = "partially contradictory"
    else:
        integrity_desc = "stable"
    
    return f"{reliability_desc.capitalize()} evidence with {integrity_desc} integrity profile."


def _map_investigator_priority(state: GameState) -> str:
    """Determine investigator priority from action history."""
    if not state.investigator_state.action_history:
        return "uncertain"
    
    recent_action = state.investigator_state.action_history[-1]
    
    if recent_action == "survey_scene":
        return "forensics"
    elif recent_action == "audit_records":
        return "financial"
    elif recent_action == "interview_witnesses":
        return "interviews"
    elif recent_action == "press_briefing":
        return "public_relations"
    else:
        return "uncertain"


def _map_investigator_demeanour(state: GameState) -> str:
    """Determine investigator demeanour from internal state."""
    inv = state.investigator_state
    
    if inv.fatigue > 1.2:
        return "exhausted"
    elif inv.fatigue > 0.8:
        return "impatient"
    elif inv.compromised > 0.5:
        return "guarded"
    else:
        return "methodical"


def _map_recent_shift(state: GameState) -> str:
    """Determine recent shift in investigator behavior."""
    inv = state.investigator_state
    
    if len(inv.action_history) < 2:
        return "uncertain"
    
    recent = inv.action_history[-1]
    previous = inv.action_history[-2]
    
    if recent == previous:
        return "attention_narrowing"
    elif recent == "press_briefing":
        return "risk_avoidance"
    else:
        return "scope_balancing"


def map_game_state_to_visible_state(state: GameState) -> dict[str, Any]:
    """Convert GameState to VisibleState JSON format expected by frontend."""
    
    # Map evidence
    evidence_items = []
    for evidence in state.visible_evidence:
        evidence_items.append({
            "id": evidence.id,
            "label": evidence.id.replace("_", " ").title(),
            "category": evidence.category,
            "state": _map_evidence_state(evidence, state),
            "summary": _generate_evidence_summary(evidence),
        })
    
    # Map timeline
    timeline_items = []
    for turn_idx, event in enumerate(state.case_data.timeline[:state.turn + 1]):
        timeline_items.append({
            "time": f"2026-02-01T{20 + turn_idx}:00:00.000Z",
            "label": f"turn_{turn_idx}",
            "details": event,
        })
    
    # Add investigator action events
    for idx, action in enumerate(state.investigator_state.action_history[-5:]):
        timeline_items.append({
            "time": f"2026-02-01T{20 + len(timeline_items)}:00:00.000Z",
            "label": action.replace("_", " ").title(),
            "details": f"Investigator action: {action}",
        })
    
    # Calculate pressure values
    public_pressure = _map_pressure_to_label(state.public_pressure)
    
    # Institutional pressure is loosely based on turn and player exposure
    institutional_pressure_val = state.turn / len(state.case_data.timeline) + state.player_state.risk_exposure / 3.0
    institutional_pressure = _map_pressure_to_label(institutional_pressure_val)
    
    # Personal pressure based on player risk and noise
    personal_pressure_val = state.player_state.risk_exposure / 2.0 + state.noise_level / 3.0
    personal_pressure = _map_pressure_to_label(personal_pressure_val)
    
    # Determine case status
    if state.turn >= len(state.case_data.timeline):
        status = "closed"
    elif state.public_pressure > 2.0:
        status = "cold"
    elif state.noise_level > 2.0:
        status = "paused"
    elif len(state.visible_evidence) > 0:
        status = "active"
    else:
        status = "contained"
    
    return {
        "case_id": f"case_{state.seed % 1000:03d}",
        "crime_type": state.case_data.crime_type,
        "turn": state.turn,
        "status": status,
        "evidence": evidence_items,
        "timeline": timeline_items[-12:],  # Keep last 12 timeline items
        "investigator_signals": {
            "priority": _map_investigator_priority(state),
            "demeanour": _map_investigator_demeanour(state),
            "recent_shift": _map_recent_shift(state),
        },
        "pressure": {
            "public": public_pressure,
            "institutional": institutional_pressure,
            "personal": personal_pressure,
        },
    }


def map_actions_to_action_options(state: GameState) -> list[dict[str, Any]]:
    """Convert available player actions to ActionOption format."""
    
    actions = []
    player_actions = available_player_actions()
    
    for action_id in player_actions:
        config = PLAYER_ACTION_CONFIGS[action_id]
        
        # Check if action can be afforded
        can_afford = all(
            state.player_state.resources.get(resource, 0.0) >= cost
            for resource, cost in config.costs.items()
        )
        
        # Format costs for display
        cost_parts = [f"{cost:.0f} {resource}" for resource, cost in config.costs.items()]
        cost_str = ", ".join(cost_parts) if cost_parts else None
        
        # Generate description
        desc = f"Risk: {config.risk:.0%}, Noise: {config.noise_delta:+.2f}"
        
        # Determine if enabled
        enabled = can_afford
        disabled_reason = None
        if not can_afford:
            disabled_reason = f"Insufficient resources: need {cost_str}"
        
        actions.append({
            "id": action_id,
            "label": action_id.replace("_", " ").title(),
            "enabled": enabled,
            "cost": cost_str,
            "desc": desc,
            "disabled_reason": disabled_reason,
        })
    
    return actions
