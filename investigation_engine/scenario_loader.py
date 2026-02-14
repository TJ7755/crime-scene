"""Scenario loader for loading and saving CrimeTypeConfig from JSON files."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .config import CrimeTypeConfig


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
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def list_scenarios(scenarios_dir: Path | str = "scenarios") -> list[str]:
    """List all scenario files in the scenarios directory.
    
    Returns a list of scenario IDs (filenames without .json extension).
    """
    scenarios_path = Path(scenarios_dir)
    if not scenarios_path.exists():
        return []
    
    return [
        f.stem
        for f in scenarios_path.glob("*.json")
        if f.is_file()
    ]


def get_scenario_path(scenario_id: str, scenarios_dir: Path | str = "scenarios") -> Path:
    """Get the file path for a scenario ID."""
    return Path(scenarios_dir) / f"{scenario_id}.json"
