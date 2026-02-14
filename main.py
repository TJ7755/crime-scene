"""Console demo showing deterministic save/load continuation."""

from __future__ import annotations

from pathlib import Path

from investigation_engine.models import GameState
from investigation_engine.simulation import GameEngine, TurnReport


def sample_player_policy(state: GameState) -> str:
    """Simple deterministic policy used for sample runs."""

    resources = state.player_state.resources
    hidden_high_risk = [
        item
        for item in state.evidence_registry.values()
        if item.active and not item.discovered and item.detectability >= 0.65
    ]

    if state.public_pressure >= 1.7 and resources.get("influence", 0.0) >= 2.0:
        return "leak_to_media"
    if hidden_high_risk and resources.get("focus", 0.0) >= 1.0:
        return "remove_evidence"
    if (
        resources.get("money", 0.0) >= 3.0
        and resources.get("influence", 0.0) >= 2.0
        and state.investigator_state.compromised <= 0.25
    ):
        return "bribe_actor"
    if resources.get("money", 0.0) >= 2.0 and resources.get("focus", 0.0) >= 1.0:
        return "plant_evidence"
    return "do_nothing"


def _reports_signature(reports: list[TurnReport]) -> list[tuple[object, ...]]:
    """Return a compact deterministic signature for turn reports."""

    return [
        (
            report.turn,
            report.investigator_action,
            report.discovered_evidence_ids,
            report.player_action_requested,
            report.player_action_resolved,
            report.player_action_success,
            report.player_action_details,
            report.public_pressure,
            report.noise_level,
            report.visible_evidence_count,
            report.outcome.ended,
            report.outcome.player_lost,
            report.outcome.reason,
        )
        for report in reports
    ]


def main() -> None:
    seed = 17
    crime_type = "murder"
    max_turns = 10
    save_after_turns = 5
    engine = GameEngine(crime_type=crime_type, seed=seed, max_turns=max_turns)
    save_path = Path("saves/demo-save.json")

    engine.run(player_policy=sample_player_policy, turns=save_after_turns)
    engine.save(save_path)

    remaining_turns = max_turns - save_after_turns
    baseline_reports, _ = engine.run(player_policy=sample_player_policy, turns=remaining_turns)
    baseline_state = engine.state.to_dict()

    loaded_engine = GameEngine.load(save_path)
    loaded_reports, _ = loaded_engine.run(player_policy=sample_player_policy, turns=remaining_turns)

    continuation_matches = (
        _reports_signature(baseline_reports) == _reports_signature(loaded_reports)
        and baseline_state == loaded_engine.state.to_dict()
    )
    print(f"Deterministic save/load continuation: {'PASS' if continuation_matches else 'FAIL'}")


if __name__ == "__main__":
    main()
