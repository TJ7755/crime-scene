"""Reproducibility checks for versioned save/load."""

from __future__ import annotations

from investigation_engine.models import GameState
from investigation_engine.simulation import GameEngine, TurnReport


def _do_nothing_policy(_: GameState) -> str:
    return "do_nothing"


def _trace_signature(reports: list[TurnReport]) -> list[tuple[object, ...]]:
    return [
        (
            report.turn,
            report.day,
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


def test_save_load_preserves_deterministic_continuation(tmp_path) -> None:
    seed = 42
    max_turns = 10
    split_turns = 5
    remaining_turns = max_turns - split_turns
    save_path = tmp_path / "repro-save.json"

    engine = GameEngine(crime_type="murder", seed=seed, max_turns=max_turns)
    engine.run(player_policy=_do_nothing_policy, turns=split_turns)
    engine.save(save_path)

    baseline_reports, _ = engine.run(player_policy=_do_nothing_policy, turns=remaining_turns)
    baseline_state = engine.state.to_dict()

    loaded_engine = GameEngine.load(save_path)
    loaded_reports, _ = loaded_engine.run(player_policy=_do_nothing_policy, turns=remaining_turns)
    loaded_state = loaded_engine.state.to_dict()

    assert _trace_signature(baseline_reports) == _trace_signature(loaded_reports)
    assert baseline_state == loaded_state
