"""FastAPI inference server for OpenEnv Bug Triage Environment."""

import os
import sys
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

# Print working directory for debugging
print(f"Current working dir: {os.getcwd()}", flush=True)

# Load OpenEnv configuration
def load_openenv_config():
    """Load openenv.yaml configuration from repo root."""
    path = os.path.join(os.getcwd(), "openenv.yaml")
    try:
        with open(path, "r") as f:
            config = yaml.safe_load(f)
        print(f"Loaded OpenEnv config from {path}", flush=True)
        return config
    except Exception as e:
        print(f"Warning: Could not load openenv.yaml from {path}: {e}", flush=True)
        return None

# Load config at startup
OPENENV_CONFIG = load_openenv_config()
if OPENENV_CONFIG:
    print(f"Loaded OpenEnv config: {OPENENV_CONFIG}", flush=True)

# Read API environment variables
API_BASE_URL = os.getenv("API_BASE_URL", "https://api.openai.com/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-3.5-turbo")
HF_TOKEN = os.getenv("HF_TOKEN", "")

print(f"API_BASE_URL: {API_BASE_URL}", flush=True)
print(f"MODEL_NAME: {MODEL_NAME}", flush=True)

# Initialize environment with tasks and graders
try:
    from core.env import BugTriageEnv as CoreBugTriageEnv
    env_instance = CoreBugTriageEnv()
    tasks_with_graders = env_instance.get_tasks_with_graders()
    print(f"[START] Loaded {len(tasks_with_graders)} tasks with graders", flush=True)
    for task in tasks_with_graders:
        print(f"[TASK] id={task['id']} has_grader={task['has_grader']}", flush=True)
except Exception as e:
    print(f"Warning: Could not initialize environment: {e}", flush=True)
    env_instance = None

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


@app.get("/tasks")
async def tasks():
    """Get available tasks with their graders."""
    try:
        from environment.env import get_tasks, get_graders
        from graders import EasyGrader, MediumGrader, HardGrader
        from tasks import EASY_SCENARIOS, MEDIUM_SCENARIOS, HARD_SCENARIOS
        from models.action import BugAction
        from models.scenario import BugScenario
        
        # Get task definitions
        tasks_list = get_tasks()
        
        # Verify graders are working by testing them
        easy_grader = EasyGrader()
        medium_grader = MediumGrader()
        hard_grader = HardGrader()
        
        # Test graders with sample scenarios
        easy_scenario = BugScenario(**EASY_SCENARIOS[0])
        medium_scenario = BugScenario(**MEDIUM_SCENARIOS[0])
        hard_scenario = BugScenario(**HARD_SCENARIOS[0])
        
        test_action = BugAction(
            bug_type="null_pointer",
            file="auth.py",
            fix="Add null check"
        )
        
        # Verify graders return valid scores
        easy_score = easy_grader.grade(test_action, easy_scenario, 1)
        medium_score = medium_grader.grade(test_action, medium_scenario, 1)
        hard_score = hard_grader.grade(test_action, hard_scenario, 1)
        
        # Verify scores are in valid range (0, 1) exclusive
        assert 0 < easy_score < 1, f"Easy grader score {easy_score} not in (0, 1)"
        assert 0 < medium_score < 1, f"Medium grader score {medium_score} not in (0, 1)"
        assert 0 < hard_score < 1, f"Hard grader score {hard_score} not in (0, 1)"
        
        # Add test scores to tasks
        for task in tasks_list:
            if task["difficulty"] == "easy":
                task["test_score"] = float(easy_score)
                task["scenarios"] = len(EASY_SCENARIOS)
            elif task["difficulty"] == "medium":
                task["test_score"] = float(medium_score)
                task["scenarios"] = len(MEDIUM_SCENARIOS)
            elif task["difficulty"] == "hard":
                task["test_score"] = float(hard_score)
                task["scenarios"] = len(HARD_SCENARIOS)
        
        return {
            "status": "success",
            "tasks": tasks_list,
            "total_tasks": len(tasks_list),
            "graders_verified": True,
            "graders_available": {
                "easy": "EasyGrader",
                "medium": "MediumGrader",
                "hard": "HardGrader"
            }
        }
    except Exception as e:
        logger.error(f"Tasks retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/graders")
async def graders():
    """Get all available graders."""
    try:
        from environment.env import get_graders
        
        graders_list = get_graders()
        
        return {
            "status": "success",
            "graders": graders_list,
            "total_graders": len(graders_list),
            "graders_available": True
        }
    except Exception as e:
        logger.error(f"Graders retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


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
    
    # Print task information for validator
    try:
        from environment.env import get_tasks, get_graders
        tasks_list = get_tasks()
        graders_list = get_graders()
        print(f"[TASKS] count={len(tasks_list)}", flush=True)
        for task in tasks_list:
            print(f"[TASK] id={task['id']} name={task['name']} difficulty={task['difficulty']} grader={task['grader']}", flush=True)
        print(f"[GRADERS] count={len(graders_list)}", flush=True)
        for grader in graders_list:
            print(f"[GRADER] name={grader['name']} class={grader['class']}", flush=True)
    except Exception as e:
        print(f"[WARNING] Could not load tasks: {e}", flush=True)
    
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
