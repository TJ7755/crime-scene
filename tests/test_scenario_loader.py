"""Tests for scenario loader functionality."""

from __future__ import annotations

from pathlib import Path
import pytest

from investigation_engine.config import CrimeTypeConfig
from investigation_engine.scenario_loader import (
    load_scenario,
    save_scenario,
    list_scenarios,
    get_scenario_path,
)


def test_save_and_load_scenario(tmp_path: Path) -> None:
    """Test saving and loading a scenario."""
    # Create a test scenario
    test_config = CrimeTypeConfig(
        name="test_crime",
        allowed_evidence_types=("physical", "digital"),
        baseline_hypotheses={
            "player_committed_crime": 0.20,
            "alternative_actor": -0.15,
        },
        default_public_pressure=0.75,
        turn_pressure_curve=(0.08, 0.09, 0.10, 0.11, 0.12),
        evidence_templates=(
            {
                "id": "ev_1",
                "category": "physical",
                "base_reliability": 0.85,
                "detectability": 0.65,
                "manipulability": 0.35,
                "current_credibility": 0.85,
                "hypothesis_impacts": {
                    "player_committed_crime": 0.80,
                },
            },
        ),
    )

    # Save scenario
    scenario_path = tmp_path / "test_crime.json"
    save_scenario(test_config, scenario_path)

    # Load scenario
    loaded_config = load_scenario(scenario_path)

    # Verify all fields match
    assert loaded_config.name == test_config.name
    assert loaded_config.allowed_evidence_types == test_config.allowed_evidence_types
    assert loaded_config.baseline_hypotheses == test_config.baseline_hypotheses
    assert loaded_config.default_public_pressure == test_config.default_public_pressure
    assert loaded_config.turn_pressure_curve == test_config.turn_pressure_curve
    assert len(loaded_config.evidence_templates) == len(test_config.evidence_templates)


def test_list_scenarios(tmp_path: Path) -> None:
    """Test listing scenarios."""
    scenarios_dir = tmp_path / "scenarios"
    scenarios_dir.mkdir()

    # Create some test scenario files
    test_configs = [
        CrimeTypeConfig(
            name=f"crime_{i}",
            allowed_evidence_types=("physical",),
            baseline_hypotheses={"player_committed_crime": 0.1},
            default_public_pressure=0.8,
            turn_pressure_curve=(0.1, 0.1),
            evidence_templates=(),
        )
        for i in range(3)
    ]

    for config in test_configs:
        save_scenario(config, scenarios_dir / f"{config.name}.json")

    # List scenarios
    scenarios = list_scenarios(scenarios_dir)

    # Verify count
    assert len(scenarios) == 3
    assert set(scenarios) == {"crime_0", "crime_1", "crime_2"}


def test_get_scenario_path() -> None:
    """Test getting scenario path."""
    path = get_scenario_path("test_scenario", "my_scenarios")
    # Path should end with the correct filename in the scenarios directory
    assert path.name == "test_scenario.json"
    assert "my_scenarios" in str(path)


def test_list_scenarios_empty_directory(tmp_path: Path) -> None:
    """Test listing scenarios when directory doesn't exist."""
    scenarios = list_scenarios(tmp_path / "nonexistent")
    assert scenarios == []


def test_save_scenario_creates_directory(tmp_path: Path) -> None:
    """Test that save_scenario creates parent directories if they don't exist."""
    test_config = CrimeTypeConfig(
        name="test_crime",
        allowed_evidence_types=("physical",),
        baseline_hypotheses={"player_committed_crime": 0.1},
        default_public_pressure=0.8,
        turn_pressure_curve=(0.1, 0.1),
        evidence_templates=(),
    )
    
    # Save to a path where parent directory doesn't exist
    nested_path = tmp_path / "new_dir" / "scenarios" / "test_crime.json"
    save_scenario(test_config, nested_path)
    
    # Verify file was created
    assert nested_path.exists()
    
    # Verify content is correct
    loaded_config = load_scenario(nested_path)
    assert loaded_config.name == test_config.name


def test_list_scenarios_sorted(tmp_path: Path) -> None:
    """Test that list_scenarios returns sorted results."""
    scenarios_dir = tmp_path / "scenarios"
    scenarios_dir.mkdir()
    
    # Create scenarios with names that would not be in alphabetical order naturally
    names = ["zebra", "alpha", "charlie", "bravo"]
    for name in names:
        config = CrimeTypeConfig(
            name=name,
            allowed_evidence_types=("physical",),
            baseline_hypotheses={"player_committed_crime": 0.1},
            default_public_pressure=0.8,
            turn_pressure_curve=(0.1, 0.1),
            evidence_templates=(),
        )
        save_scenario(config, scenarios_dir / f"{name}.json")
    
    # List scenarios
    scenarios = list_scenarios(scenarios_dir)
    
    # Verify they are sorted
    assert scenarios == ["alpha", "bravo", "charlie", "zebra"]


def test_get_scenario_path_path_traversal_prevention() -> None:
    """Test that get_scenario_path prevents path traversal attacks."""
    # Test various path traversal attempts
    with pytest.raises(ValueError, match="Invalid scenario_id"):
        get_scenario_path("../secrets")
    
    with pytest.raises(ValueError, match="Invalid scenario_id"):
        get_scenario_path("../../etc/passwd")
    
    with pytest.raises(ValueError, match="Invalid scenario_id"):
        get_scenario_path("test/../../../secrets")
    
    with pytest.raises(ValueError, match="Invalid scenario_id"):
        get_scenario_path("test/../../secrets")


def test_get_scenario_path_invalid_characters() -> None:
    """Test that get_scenario_path rejects invalid characters."""
    # Test invalid characters
    with pytest.raises(ValueError, match="Invalid scenario_id"):
        get_scenario_path("test scenario")  # space
    
    with pytest.raises(ValueError, match="Invalid scenario_id"):
        get_scenario_path("test;scenario")  # semicolon
    
    with pytest.raises(ValueError, match="Invalid scenario_id"):
        get_scenario_path("test/scenario")  # slash
    
    with pytest.raises(ValueError, match="Invalid scenario_id"):
        get_scenario_path("test\\scenario")  # backslash


def test_get_scenario_path_valid_characters() -> None:
    """Test that get_scenario_path accepts valid scenario IDs."""
    # These should all be valid
    valid_ids = ["test", "test_scenario", "test-scenario", "Test123", "test_123-abc"]
    
    for scenario_id in valid_ids:
        path = get_scenario_path(scenario_id, "scenarios")
        assert path.name == f"{scenario_id}.json"
        assert "scenarios" in str(path)
