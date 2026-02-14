"""Scenario loader for loading and saving CrimeTypeConfig from JSON files."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from .config import CrimeTypeConfig

# JSON formatting constant
JSON_INDENT = 2

# Pattern for valid scenario IDs (alphanumeric, underscore, hyphen only)
VALID_SCENARIO_ID_PATTERN = re.compile(r"^[a-zA-Z0-9_-]+$")


def _serialize_crime_type_config(config: CrimeTypeConfig) -> dict[str, Any]:
    """Serialize a CrimeTypeConfig to a JSON-compatible dictionary."""
    return {
        "name": config.name,
        "allowed_evidence_types": list(config.allowed_evidence_types),
        "baseline_hypotheses": dict(config.baseline_hypotheses),
        "default_public_pressure": config.default_public_pressure,
        "turn_pressure_curve": list(config.turn_pressure_curve),
        "evidence_templates": [dict(template) for template in config.evidence_templates],
    }


def _deserialize_crime_type_config(data: dict[str, Any]) -> CrimeTypeConfig:
    """Deserialize a JSON-compatible dictionary to a CrimeTypeConfig."""
    return CrimeTypeConfig(
        name=data["name"],
        allowed_evidence_types=tuple(data["allowed_evidence_types"]),
        baseline_hypotheses=data["baseline_hypotheses"],
        default_public_pressure=data["default_public_pressure"],
        turn_pressure_curve=tuple(data["turn_pressure_curve"]),
        evidence_templates=tuple(data["evidence_templates"]),
    )


def load_scenario(path: Path | str) -> CrimeTypeConfig:
    """Load a scenario from a JSON file."""
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return _deserialize_crime_type_config(data)


def save_scenario(config: CrimeTypeConfig, path: Path | str) -> None:
    """Save a scenario to a JSON file."""
    data = _serialize_crime_type_config(config)
    path_obj = Path(path)
    path_obj.parent.mkdir(parents=True, exist_ok=True)
    with open(path_obj, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=JSON_INDENT, ensure_ascii=False)


def list_scenarios(scenarios_dir: Path | str = "scenarios") -> list[str]:
    """List all scenario files in the scenarios directory.
    
    Returns a sorted list of scenario IDs (filenames without .json extension).
    """
    scenarios_path = Path(scenarios_dir)
    if not scenarios_path.exists():
        return []
    
    return sorted(
        [
            f.stem
            for f in scenarios_path.glob("*.json")
            if f.is_file()
        ]
    )


def get_scenario_path(scenario_id: str, scenarios_dir: Path | str = "scenarios") -> Path:
    """Get the file path for a scenario ID.
    
    Args:
        scenario_id: The scenario identifier (must match ^[a-zA-Z0-9_-]+$)
        scenarios_dir: The scenarios directory path
        
    Returns:
        Path to the scenario file
        
    Raises:
        ValueError: If scenario_id contains invalid characters or path traversal attempts
    """
    # Validate scenario_id to prevent path traversal
    if not VALID_SCENARIO_ID_PATTERN.match(scenario_id):
        raise ValueError(
            f"Invalid scenario_id '{scenario_id}'. "
            f"Only alphanumeric characters, underscores, and hyphens are allowed."
        )
    
    # Construct and validate the path
    scenarios_path = Path(scenarios_dir).resolve()
    candidate_path = (scenarios_path / f"{scenario_id}.json").resolve()
    
    # Ensure the resolved path is within the scenarios directory
    try:
        candidate_path.relative_to(scenarios_path)
    except ValueError:
        raise ValueError(
            f"Invalid scenario_id '{scenario_id}'. Path traversal detected."
        )
    
    return candidate_path
