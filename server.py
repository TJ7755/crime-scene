"""FastAPI server to expose investigation_engine to frontend."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from investigation_engine.api_mapper import (
    map_actions_to_action_options,
    map_game_state_to_visible_state,
)
from investigation_engine.simulation import GameEngine

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(title="Crime Scene Investigation Engine API", version="1.0.0")

# Configure CORS for frontend (typically port 5173 for Vite)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global game engine instance
game_engine: GameEngine | None = None


class ApplyActionRequest(BaseModel):
    """Request body for apply_action endpoint."""
    action_id: str


class ResetRequest(BaseModel):
    """Request body for reset endpoint."""
    seed: int = 1
    crime_type: str = "murder"
    max_turns: int = 20


@app.on_event("startup")
async def startup_event():
    """Initialize game engine on startup."""
    global game_engine
    logger.info("Initializing game engine...")
    game_engine = GameEngine(crime_type="murder", seed=1, max_turns=20)
    logger.info("Game engine initialized successfully")


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
        },
    }


@app.get("/api/visible_state")
async def get_visible_state() -> dict[str, Any]:
    """Get current game state formatted as VisibleState."""
    if game_engine is None:
        raise HTTPException(status_code=500, detail="Game engine not initialized")
    
    try:
        visible_state = map_game_state_to_visible_state(game_engine.state)
        logger.info(f"Returning visible state for turn {game_engine.state.turn}")
        return visible_state
    except Exception as e:
        logger.error(f"Error getting visible state: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting visible state: {str(e)}")


@app.get("/api/actions")
async def get_actions() -> dict[str, Any]:
    """Get available player actions."""
    if game_engine is None:
        raise HTTPException(status_code=500, detail="Game engine not initialized")
    
    try:
        actions = map_actions_to_action_options(game_engine.state)
        logger.info(f"Returning {len(actions)} available actions")
        return {"actions": actions}
    except Exception as e:
        logger.error(f"Error getting actions: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting actions: {str(e)}")


@app.post("/api/apply_action")
async def apply_action(request: ApplyActionRequest) -> dict[str, Any]:
    """Apply a player action and return updated state."""
    if game_engine is None:
        raise HTTPException(status_code=500, detail="Game engine not initialized")
    
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
        logger.error(f"Error applying action: {e}")
        raise HTTPException(status_code=500, detail=f"Error applying action: {str(e)}")


@app.post("/api/reset")
async def reset_game(request: ResetRequest) -> dict[str, Any]:
    """Reset the game with a new seed and crime type."""
    global game_engine
    
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
        logger.error(f"Error resetting game: {e}")
        raise HTTPException(status_code=500, detail=f"Error resetting game: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")
