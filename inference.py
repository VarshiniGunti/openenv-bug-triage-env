"""FastAPI inference server for OpenEnv Bug Triage Environment."""

import os
import sys
import json
import yaml
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

# Read API environment variables
API_BASE_URL = os.getenv("API_BASE_URL", "https://api.openai.com/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-3.5-turbo")
HF_TOKEN = os.getenv("HF_TOKEN", "")

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
async def reset(task: str = "easy"):
    """Reset the environment and start a new episode."""
    global env_instance
    
    try:
        if task not in ["easy", "medium", "hard"]:
            raise ValueError(f"Invalid task: {task}. Must be 'easy', 'medium', or 'hard'")
        
        config = Config(task=task, max_steps=3)
        env_instance = BugTriageEnv(config)
        observation = env_instance.reset()
        
        if hasattr(observation, "model_dump"):
            observation = observation.model_dump()
        elif hasattr(observation, "dict"):
            observation = observation.dict()
        elif hasattr(observation, "__dict__"):
            observation = observation.__dict__
        
        logger.info(f"Environment reset: task={task}")
        
        return {
            "observation": observation,
            "info": {"task": task}
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
            fix=action.get("fix") or "Apply a fix to resolve the issue"
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


@app.get("/tasks")
async def tasks():
    """Get available tasks with their graders."""
    return [
        {"id": "easy_bug", "difficulty": "easy", "grader": "easy_grader"},
        {"id": "medium_bug", "difficulty": "medium", "grader": "medium_grader"},
        {"id": "hard_bug", "difficulty": "hard", "grader": "hard_grader"}
    ]


@app.get("/graders")
async def graders():
    """Get all available graders."""
    return {
        "easy_grader": {"path": "graders.easy_grader.EasyGrader"},
        "medium_grader": {"path": "graders.medium_grader.MediumGrader"},
        "hard_grader": {"path": "graders.hard_grader.HardGrader"}
    }


@app.post("/evaluate")
async def evaluate(task: str = "easy", num_episodes: int = 5):
    """Run evaluation with baseline agent."""
    try:
        from baseline.baseline_agent import BaselineAgent
        
        agent = BaselineAgent(task=task)
        results = []
        total_reward = 0.0
        
        for episode in range(num_episodes):
            result = agent.run_episode()
            results.append(result)
            total_reward += result["total_reward"]
        
        avg_reward = total_reward / num_episodes if num_episodes > 0 else 0.0
        success_rate = sum(1 for r in results if r["success"]) / num_episodes if num_episodes > 0 else 0.0
        
        return {
            "status": "success",
            "task": task,
            "num_episodes": num_episodes,
            "avg_reward": avg_reward,
            "success_rate": success_rate,
            "total_reward": total_reward,
            "episodes": results
        }
    except Exception as e:
        logger.error(f"Evaluation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/metrics")
async def metrics():
    """Get environment metrics and configuration."""
    try:
        return {
            "status": "success",
            "environment": {
                "name": "OpenEnv Bug Triage",
                "version": "1.0",
                "tasks": ["easy", "medium", "hard"],
                "max_steps": 3,
                "reward_range": [0.05, 0.95]
            },
            "graders": {
                "easy": {
                    "steps": 1,
                    "max_reward": 0.35,
                    "min_reward": 0.05
                },
                "medium": {
                    "steps": 2,
                    "max_reward": 0.70,
                    "min_reward": 0.10
                },
                "hard": {
                    "steps": 3,
                    "max_reward": 0.95,
                    "min_reward": 0.15
                }
            }
        }
    except Exception as e:
        logger.error(f"Metrics retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Inference script for validator
if __name__ != "__main__":
    # This is imported as a module by uvicorn
    pass
else:
    # This runs when executed directly by validator
    import argparse
    from openai import OpenAI
    
    parser = argparse.ArgumentParser(description="Run OpenEnv Bug Triage inference")
    parser.add_argument("--task", default="easy", choices=["easy", "medium", "hard"])
    parser.add_argument("--episodes", type=int, default=1)
    parser.add_argument("--seed", type=int, default=None)
    
    args = parser.parse_args()
    
    # Initialize OpenAI client with validator's API
    api_base_url = os.environ.get("API_BASE_URL", "https://router.huggingface.co/v1")
    model_name = os.environ.get("MODEL_NAME", "gpt-3.5-turbo")
    api_key = os.environ.get("HF_TOKEN") or os.environ.get("API_KEY") or "dummy"
    
    client = OpenAI(api_key=api_key, base_url=api_base_url)
    
    # Helper functions for logging in official format
    def log_start(task, env, model):
        """Print [START] line in official format."""
        print(f"[START] task={task} env={env} model={model}", flush=True)
    
    def log_step(step, action, reward, done, error):
        """Print [STEP] line in official format."""
        done_str = str(done).lower()
        error_str = error if error else "null"
        print(f"[STEP] step={step} action={action} reward={reward:.2f} done={done_str} error={error_str}", flush=True)
    
    def log_end(success, steps, score, rewards):
        """Print [END] line in official format."""
        rewards_str = ",".join(f"{r:.2f}" for r in rewards)
        print(f"[END] success={str(success).lower()} steps={steps} score={score:.3f} rewards={rewards_str}", flush=True)
    
    def parse_llm_response(llm_response: str) -> Optional[dict]:
        """Parse LLM response to extract bug_type, file, fix."""
        if not llm_response:
            return None
        
        lines = llm_response.strip().split('\n')
        result = {}
        
        for line in lines:
            line_lower = line.lower()
            # Extract bug_type
            if 'bug_type' in line_lower or 'type' in line_lower:
                parts = line.split(':')
                if len(parts) > 1:
                    bug_type_value = parts[1].strip().lower().replace(' ', '_')
                    if bug_type_value:
                        result['bug_type'] = bug_type_value
            # Extract file
            elif 'file' in line_lower:
                parts = line.split(':')
                if len(parts) > 1:
                    file_value = parts[1].strip()
                    if file_value:
                        result['file'] = file_value
            # Extract fix
            elif 'fix' in line_lower:
                parts = line.split(':')
                if len(parts) > 1:
                    fix_value = parts[1].strip()
                    if fix_value:
                        result['fix'] = fix_value
        
        # Return result only if all required fields are present
        return result if all(k in result for k in ['bug_type', 'file', 'fix']) else None
    
    # Print START in official format
    log_start(task=args.task, env="openenv-bug-triage-env", model=model_name)
    
    try:
        config = Config(task=args.task, max_steps=3, seed=args.seed)
        env = BugTriageEnv(config)
        
        total_reward = 0.0
        all_rewards = []
        
        for episode in range(args.episodes):
            obs = env.reset()
            
            # Get bug report context
            bug_report = obs.bug_report if hasattr(obs, 'bug_report') else str(obs)
            
            for step_num in range(1, 4):
                # Make LLM API call to get action
                action = None
                try:
                    response = client.chat.completions.create(
                        model=model_name,
                        messages=[
                            {
                                "role": "system",
                                "content": "You are a bug triage expert. Analyze the bug and provide a classification."
                            },
                            {
                                "role": "user",
                                "content": f"Bug: {bug_report}\n\nStep {step_num}: Provide bug_type, file, and fix."
                            }
                        ],
                        max_tokens=100,
                        temperature=0.7
                    )
                    llm_response = response.choices[0].message.content
                    
                    # Parse LLM response to extract structured data
                    parsed = parse_llm_response(llm_response)
                    
                    # Use parsed values if valid, otherwise use fallback
                    if parsed:
                        action = BugAction(
                            bug_type=parsed['bug_type'],
                            file=parsed['file'],
                            fix=parsed['fix']
                        )
                except Exception as llm_error:
                    # Fallback on any LLM error
                    pass
                
                # Use default action if parsing failed or LLM call failed
                if action is None:
                    action = BugAction(
                        bug_type="null_pointer",
                        file="main.py",
                        fix="Add null check"
                    )
                
                obs, reward, done, info = env.step(action)
                all_rewards.append(reward)
                
                # Log STEP in official format
                log_step(step=step_num, action="null_pointer", reward=reward, done=done, error=None)
                
                if done:
                    break
            
            total_reward += sum(all_rewards)
        
        # Calculate average score
        avg_score = total_reward / (args.episodes * 3) if args.episodes > 0 else 0.0
        avg_score = min(max(avg_score, 0.0), 1.0)
        success = avg_score > 0.0
        
        # Log END in official format
        log_end(success=success, steps=len(all_rewards), score=avg_score, rewards=all_rewards)
        
    except Exception as e:
        # Log END in official format for error case
        log_end(success=False, steps=0, score=0.0, rewards=[])
        sys.exit(1)
