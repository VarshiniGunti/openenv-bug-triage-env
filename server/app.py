"""FastAPI server for OpenEnv Bug Triage Environment."""

import os
import sys
from typing import Optional, Dict, Any

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from models.config import Config
from models.action import BugAction
from environment.env import BugTriageEnv

try:
    from core.logging_config import get_logger
except ImportError:
    from logging_config import get_logger

app = FastAPI(
    title="OpenEnv Bug Triage Environment",
    description="Bug triage simulation environment for agent evaluation",
    version="1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

logger = get_logger()
env_instance: Optional[BugTriageEnv] = None


@app.on_event("startup")
def startup_event():
    """Log startup event."""
    print("OpenEnv Bug Triage Environment Started")
    logger.info("FastAPI server started successfully")


@app.get("/")
def root():
    """Root endpoint - returns service status."""
    return {
        "message": "OpenEnv Bug Triage Environment Running",
        "status": "ok",
        "version": "1.0",
        "endpoints": {
            "health": "/health",
            "reset": "/reset",
            "step": "/step",
            "state": "/state",
            "docs": "/docs"
        }
    }


@app.get("/health")
def health():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.post("/reset")
async def reset():
    """Reset the environment and start a new episode."""
    global env_instance
    
    try:
        config = Config(task="easy", max_steps=3)
        env_instance = BugTriageEnv(config)
        observation = env_instance.reset()
        
        if hasattr(observation, "model_dump"):
            observation = observation.model_dump()
        elif hasattr(observation, "dict"):
            observation = observation.dict()
        elif hasattr(observation, "__dict__"):
            observation = observation.__dict__
        
        logger.info("Environment reset: task=easy")
        
        return {
            "observation": observation,
            "info": {}
        }
    except Exception as e:
        logger.error(f"Reset failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/step")
async def step(action: dict = {}):
    """Execute one step in the environment."""
    global env_instance
    
    if env_instance is None:
        raise HTTPException(status_code=400, detail="Environment not initialized. Call /reset first.")
    
    try:
        bug_action = BugAction(
            bug_type=action.get("bug_type") or "logic",
            file=action.get("file") or "main.py",
            fix=action.get("fix") or "Fix the issue"
        )
        
        observation, reward, done, info = env_instance.step(bug_action)
        
        if hasattr(observation, "model_dump"):
            observation = observation.model_dump()
        elif hasattr(observation, "dict"):
            observation = observation.dict()
        elif hasattr(observation, "__dict__"):
            observation = observation.__dict__
        
        logger.info(f"Step executed: reward={reward:.2f}, done={done}")
        
        return {
            "observation": observation,
            "reward": float(reward),
            "done": bool(done),
            "info": info or {}
        }
    except Exception as e:
        logger.error(f"Step failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/state")
async def state():
    """Get current environment state."""
    global env_instance
    
    if env_instance is None:
        raise HTTPException(status_code=400, detail="Environment not initialized. Call /reset first.")
    
    try:
        state_data = env_instance.state()
        return {
            "status": "success",
            "state": state_data
        }
    except Exception as e:
        logger.error(f"State retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def main():
    """Main entry point for the server."""
    import uvicorn
    import argparse
    
    parser = argparse.ArgumentParser(description="Run OpenEnv Bug Triage inference server")
    parser.add_argument("--host", default="0.0.0.0", help="Server host")
    parser.add_argument("--port", type=int, default=7860, help="Server port")
    
    args = parser.parse_args()
    
    logger.info(f"Starting FastAPI server on {args.host}:{args.port}")
    uvicorn.run(app, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
