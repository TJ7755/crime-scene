"""FastAPI server to expose investigation_engine to frontend."""

from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
import logging
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from investigation_engine.api_mapper import (
    map_actions_to_action_options,
    map_game_state_to_visible_state,
)
from investigation_engine.simulation import GameEngine
from investigation_engine.scenario_loader import (
    list_scenarios,
    load_scenario,
    save_scenario,
    get_scenario_path,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown."""
    # Startup
    global game_engine
    logger.info("Initializing game engine...")
    game_engine = GameEngine(crime_type="murder", seed=1, max_turns=20)
    logger.info("Game engine initialized successfully")
    yield
    # Shutdown (if needed)
    logger.info("Shutting down...")


# Create FastAPI app
app = FastAPI(
    title="Crime Scene Investigation Engine API",
    version="1.0.0",
    lifespan=lifespan,
)

# Configure CORS for frontend (typically port 5173 for Vite)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global game engine instance and lock for concurrent access
game_engine: GameEngine | None = None
engine_lock = asyncio.Lock()


class ApplyActionRequest(BaseModel):
    """Request body for apply_action endpoint."""
    action_id: str
    params: dict[str, Any] | None = Field(
        default=None,
        description="Optional parameters for the action (currently ignored by the backend)",
    )


class ResetRequest(BaseModel):
    """Request body for reset endpoint."""
    seed: int = Field(default=1, ge=1, le=1_000_000)
    crime_type: str = "murder"
    max_turns: int = Field(default=20, ge=1, le=100)


class PlayScenarioRequest(BaseModel):
    """Request body for playing a scenario."""
    scenario_id: str
    seed: int = Field(default=1, ge=1, le=1_000_000)
    max_turns: int = Field(default=20, ge=1, le=100)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Crime Scene Investigation Engine API",
        "version": "1.0.0",
        "endpoints": {
            "GET /api/visible_state": "Get current game state",
            "GET /api/actions": "Get available actions",
            "POST /api/apply_action": "Apply an action",
            "POST /api/reset": "Reset the game",
            "GET /api/scenarios": "List available scenarios",
            "GET /api/scenarios/{id}": "Get a specific scenario",
            "POST /api/scenarios/{id}": "Save/Update a scenario",
            "POST /api/scenarios/play": "Initialize game with a scenario",
        },
    }


@app.get("/api/visible_state")
async def get_visible_state() -> dict[str, Any]:
    """Get current game state formatted as VisibleState."""
    if game_engine is None:
        raise HTTPException(status_code=500, detail="Game engine not initialized")
    
    async with engine_lock:
        try:
            visible_state = map_game_state_to_visible_state(game_engine.state)
            logger.info(f"Returning visible state for turn {game_engine.state.turn}")
            return visible_state
        except Exception as e:
            logger.error(f"Error getting visible state: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail="Error getting visible state")


@app.get("/api/actions")
async def get_actions() -> dict[str, Any]:
    """Get available player actions."""
    if game_engine is None:
        raise HTTPException(status_code=500, detail="Game engine not initialized")
    
    async with engine_lock:
        try:
            actions = map_actions_to_action_options(game_engine.state)
            logger.info(f"Returning {len(actions)} available actions")
            return {"actions": actions}
        except Exception as e:
            logger.error(f"Error getting actions: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail="Error getting actions")


@app.post("/api/apply_action")
async def apply_action(request: ApplyActionRequest) -> dict[str, Any]:
    """Apply a player action and return updated state."""
    if game_engine is None:
        raise HTTPException(status_code=500, detail="Game engine not initialized")
    
    async with engine_lock:
        try:
            action_id = request.action_id
            logger.info(f"Applying action: {action_id}")
            
            # Step the game engine with the player action
            turn_report = game_engine.step(action_id)
            
            # Get updated visible state
            visible_state = map_game_state_to_visible_state(game_engine.state)
            
            # Format action result
            action_result = {
                "success": turn_report.player_action_success,
                "summary": (
                    f"{turn_report.player_action_resolved}: {turn_report.player_action_details}. "
                    f"Investigator took action: {turn_report.investigator_action}."
                ),
            }
            
            logger.info(
                f"Action applied successfully. Turn: {game_engine.state.turn}, "
                f"Success: {turn_report.player_action_success}"
            )
            
            return {
                "visible_state": visible_state,
                "action_result": action_result,
            }
        except Exception as e:
            logger.error(f"Error applying action: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail="Error applying action")


@app.post("/api/reset")
async def reset_game(request: ResetRequest) -> dict[str, Any]:
    """Reset the game with a new seed and crime type."""
    global game_engine
    
    async with engine_lock:
        try:
            logger.info(
                f"Resetting game with seed={request.seed}, "
                f"crime_type={request.crime_type}, max_turns={request.max_turns}"
            )
            
            game_engine = GameEngine(
                crime_type=request.crime_type,
                seed=request.seed,
                max_turns=request.max_turns,
            )
            
            visible_state = map_game_state_to_visible_state(game_engine.state)
            
            logger.info("Game reset successfully")
            
            return {
                "message": "Game reset successfully",
                "visible_state": visible_state,
            }
        except Exception as e:
            logger.error(f"Error resetting game: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail="Error resetting game")


@app.get("/api/scenarios")
async def get_scenarios() -> dict[str, Any]:
    """List all available scenario files."""
    try:
        scenarios = list_scenarios()
        logger.info(f"Returning {len(scenarios)} scenarios")
        return {"scenarios": scenarios}
    except Exception as e:
        logger.error(f"Error listing scenarios: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error listing scenarios")


@app.post("/api/scenarios/play")
async def play_scenario(request: PlayScenarioRequest) -> dict[str, Any]:
    """Initialize the game engine with a specific scenario configuration."""
    global game_engine
    
    async with engine_lock:
        try:
            # Load the scenario
            path = get_scenario_path(request.scenario_id)
            if not path.exists():
                raise HTTPException(status_code=404, detail=f"Scenario '{request.scenario_id}' not found")
            
            config = load_scenario(path)
            
            logger.info(
                f"Initializing game with scenario '{request.scenario_id}', "
                f"seed={request.seed}, max_turns={request.max_turns}"
            )
            
            # Initialize game engine with the loaded config
            # We need to create a modified GameEngine that accepts a config
            # For now, we'll use the crime type name from the config
            game_engine = GameEngine(
                crime_type=config.name,
                seed=request.seed,
                max_turns=request.max_turns,
            )
            
            visible_state = map_game_state_to_visible_state(game_engine.state)
            
            logger.info(f"Game initialized with scenario '{request.scenario_id}'")
            
            return {
                "message": f"Game initialized with scenario '{request.scenario_id}'",
                "visible_state": visible_state,
            }
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error playing scenario {request.scenario_id}: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail="Error initializing game with scenario")


@app.get("/api/scenarios/{scenario_id}")
async def get_scenario(scenario_id: str) -> dict[str, Any]:
    """Get the content of a specific scenario."""
    try:
        path = get_scenario_path(scenario_id)
        if not path.exists():
            raise HTTPException(status_code=404, detail=f"Scenario '{scenario_id}' not found")
        
        config = load_scenario(path)
        logger.info(f"Loaded scenario: {scenario_id}")
        
        # Convert to JSON-compatible format
        from investigation_engine.scenario_loader import _serialize_crime_type_config
        return _serialize_crime_type_config(config)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error loading scenario {scenario_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error loading scenario")


@app.post("/api/scenarios/{scenario_id}")
async def save_scenario_endpoint(scenario_id: str, scenario_data: dict[str, Any]) -> dict[str, Any]:
    """Save or update a scenario."""
    try:
        # Validate and deserialize
        from investigation_engine.scenario_loader import _deserialize_crime_type_config
        config = _deserialize_crime_type_config(scenario_data)
        
        # Save to file
        path = get_scenario_path(scenario_id)
        save_scenario(config, path)
        
        logger.info(f"Saved scenario: {scenario_id}")
        return {"message": f"Scenario '{scenario_id}' saved successfully"}
    except Exception as e:
        logger.error(f"Error saving scenario {scenario_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error saving scenario")


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")
