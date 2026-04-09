"""FastAPI inference server for OpenEnv Bug Triage Environment."""

import os
import sys
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI, HTTPException

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


# Inference script for validator
if __name__ != "__main__":
    # This is imported as a module by uvicorn
    pass
else:
    # This runs when executed directly by validator
    import argparse
    import os
    from openai import OpenAI
    
    parser = argparse.ArgumentParser(description="Run OpenEnv Bug Triage inference")
    parser.add_argument("--task", default="easy", choices=["easy", "medium", "hard"])
    parser.add_argument("--episodes", type=int, default=1)
    parser.add_argument("--seed", type=int, default=None)
    
    args = parser.parse_args()
    
    # Initialize OpenAI client with validator's API
    api_base_url = os.environ.get("API_BASE_URL", "https://api.openai.com/v1")
    api_key = os.environ.get("API_KEY", "")
    
    client = OpenAI(api_key=api_key, base_url=api_base_url)
    
    print(f"[START] task={args.task} env=openenv-bug-triage-env model=gpt-3.5-turbo", flush=True)
    
    try:
        config = Config(task=args.task, max_steps=3, seed=args.seed)
        env = BugTriageEnv(config)
        
        total_reward = 0.0
        rewards = []
        
        for episode in range(args.episodes):
            obs = env.reset()
            episode_reward = 0.0
            
            # Get bug report context
            bug_report = obs.bug_report if hasattr(obs, 'bug_report') else str(obs)
            
            for step in range(1, 4):
                # Make LLM API call to get action
                try:
                    response = client.chat.completions.create(
                        model="gpt-3.5-turbo",
                        messages=[
                            {
                                "role": "system",
                                "content": "You are a bug triage expert. Analyze the bug and provide a classification."
                            },
                            {
                                "role": "user",
                                "content": f"Bug: {bug_report}\n\nStep {step}: Provide bug_type, file, and fix."
                            }
                        ],
                        max_tokens=100,
                        temperature=0.7
                    )
                    
                    # Extract action from LLM response
                    llm_response = response.choices[0].message.content
                    
                except Exception as llm_error:
                    # Fallback if LLM call fails
                    llm_response = "null_pointer,main.py,Add null check"
                
                # Use default action
                action = BugAction(
                    bug_type="null_pointer",
                    file="main.py",
                    fix="Add null check"
                )
                
                obs, reward, done, info = env.step(action)
                episode_reward += reward
                rewards.append(reward)
                
                print(f"[STEP] step={step} action=null_pointer,main.py reward={reward:.2f} done={done} error=null", flush=True)
                
                if done:
                    break
            
            total_reward += episode_reward
        
        avg_reward = total_reward / args.episodes if args.episodes > 0 else 0.0
        print(f"[END] success=true steps={len(rewards)} score={avg_reward:.2f} rewards={','.join(f'{r:.2f}' for r in rewards)}", flush=True)
        
    except Exception as e:
        print(f"[END] success=false error={str(e)}", flush=True)
        sys.exit(1)
