"""FastAPI inference server for OpenEnv Bug Triage Environment."""

import os
import json
import sys
from typing import Optional, Dict, Any
from datetime import datetime

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse, RedirectResponse
from pydantic import BaseModel

from models.config import Config
from models.action import BugAction
from environment.env import BugTriageEnv
from core.logging_config import get_logger

# Initialize FastAPI app
app = FastAPI(
    title="OpenEnv Bug Triage Environment",
    description="Bug triage simulation environment for agent evaluation",
    version="1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Initialize logger
logger = get_logger()

# Global environment instance
env_instance: Optional[BugTriageEnv] = None


class InferenceRequest(BaseModel):
    """Request model for inference endpoint."""
    task: str = "easy"
    bug_type: Optional[str] = None
    file: Optional[str] = None
    fix: Optional[str] = None


class InferenceResponse(BaseModel):
    """Response model for inference endpoint."""
    status: str
    message: str
    data: Optional[Dict[str, Any]] = None


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
            "infer": "/infer",
            "state": "/state",
            "docs": "/docs"
        }
    }


@app.get("/health")
def health():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.get("/docs_redirect")
def docs_redirect():
    """Redirect to API documentation."""
    return RedirectResponse(url="/docs")


@app.post("/reset")
async def reset():
    """Reset the environment and start a new episode."""
    global env_instance
    
    try:
        config = Config(task="easy", max_steps=3)
        env_instance = BugTriageEnv(config)
        observation = env_instance.reset()
        
        # Ensure JSON serializable
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
        
        # Ensure JSON serializable
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


@app.post("/infer")
async def infer(request: InferenceRequest):
    """Inference endpoint - run a complete episode."""
    global env_instance
    
    try:
        # Reset environment
        config = Config(task=request.task, max_steps=3)
        env_instance = BugTriageEnv(config)
        observation = env_instance.reset()
        
        logger.info(f"Inference started: task={request.task}")
        
        # Run 3 steps
        steps_data = []
        total_reward = 0.0
        
        for step_num in range(1, 4):
            action = BugAction(
                bug_type=request.bug_type or "logic",
                file=request.file or observation.repo_modules[0] if observation.repo_modules else "main.py",
                fix=request.fix or "Fix the issue"
            )
            
            observation, reward, done, info = env_instance.step(action)
            total_reward += reward
            
            steps_data.append({
                "step": step_num,
                "action": action.model_dump(),
                "reward": reward,
                "done": done
            })
            
            if done:
                break
        
        logger.info(f"Inference completed: total_reward={total_reward:.2f}")
        
        return {
            "status": "success",
            "task": request.task,
            "total_reward": total_reward,
            "steps": steps_data,
            "success": total_reward > 0.0
        }
    except Exception as e:
        logger.error(f"Inference failed: {e}")
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


if __name__ == "__main__":
    import uvicorn
    import argparse
    
    parser = argparse.ArgumentParser(description="Run OpenEnv Bug Triage inference server")
    parser.add_argument("--host", default="0.0.0.0", help="Server host")
    parser.add_argument("--port", type=int, default=7860, help="Server port")
    
    args = parser.parse_args()
    
    logger.info(f"Starting FastAPI server on {args.host}:{args.port}")
    uvicorn.run(app, host=args.host, port=args.port)
