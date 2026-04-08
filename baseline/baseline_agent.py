"""Baseline agent for OpenEnv Bug Triage Environment."""

import random
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from environment.env import BugTriageEnv
from models.config import Config
from models.action import BugAction


class BaselineAgent:
    """Simple baseline agent that makes random predictions."""
    
    BUG_TYPES = [
        "memory", "logic", "authentication", "database",
        "performance", "null_pointer", "session", "race_condition"
    ]
    
    def __init__(self, task: str = "easy"):
        """Initialize the baseline agent."""
        self.task = task
        self.env = BugTriageEnv(Config(task=task))
    
    def run_episode(self) -> dict:
        """Run a single episode and return results."""
        obs = self.env.reset()
        total_reward = 0.0
        steps_data = []
        
        for step in range(3):
            # Make random predictions
            action = BugAction(
                bug_type=random.choice(self.BUG_TYPES),
                file=random.choice(obs.repo_modules),
                fix="Fix the issue by addressing the root cause"
            )
            
            obs, reward, done, info = self.env.step(action)
            total_reward += reward
            
            steps_data.append({
                "step": step + 1,
                "action": action.model_dump(),
                "reward": reward,
                "done": done
            })
            
            if done:
                break
        
        return {
            "task": self.task,
            "total_reward": total_reward,
            "steps": steps_data,
            "success": total_reward > 0.0
        }
    
    def run_evaluation(self, num_episodes: int = 5) -> dict:
        """Run multiple episodes and return evaluation results."""
        results = []
        total_rewards = []
        
        for episode in range(num_episodes):
            result = self.run_episode()
            results.append(result)
            total_rewards.append(result["total_reward"])
        
        return {
            "task": self.task,
            "num_episodes": num_episodes,
            "episodes": results,
            "average_reward": sum(total_rewards) / len(total_rewards),
            "max_reward": max(total_rewards),
            "min_reward": min(total_rewards)
        }


if __name__ == "__main__":
    import json
    
    # Run baseline evaluation
    agent = BaselineAgent(task="easy")
    results = agent.run_evaluation(num_episodes=3)
    
    print(json.dumps(results, indent=2))
