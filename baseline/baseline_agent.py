"""Baseline agent for OpenEnv Bug Triage Environment."""

import random
import sys
import os
from typing import Dict, Any, List

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from environment.env import BugTriageEnv
from models.config import Config
from models.action import BugAction


class BaselineAgent:
    """Intelligent baseline agent with heuristic-based predictions."""
    
    BUG_TYPES = [
        "memory", "logic", "authentication", "database",
        "performance", "null_pointer", "session", "race_condition"
    ]
    
    # Heuristic keywords for bug type detection
    BUG_TYPE_KEYWORDS = {
        "memory": ["memory", "leak", "heap", "allocation", "garbage", "gc", "oom"],
        "logic": ["logic", "calculation", "algorithm", "incorrect", "wrong", "result"],
        "authentication": ["auth", "login", "password", "credential", "token", "session"],
        "database": ["database", "db", "query", "sql", "connection", "pool"],
        "performance": ["slow", "timeout", "performance", "lag", "delay", "hang"],
        "null_pointer": ["null", "npe", "undefined", "none", "crash", "exception"],
        "session": ["session", "cookie", "expire", "timeout", "logout"],
        "race_condition": ["concurrent", "race", "thread", "parallel", "lock", "mutex"]
    }
    
    # File type heuristics
    FILE_KEYWORDS = {
        "auth": ["auth", "login", "credential", "password", "token"],
        "database": ["db", "database", "query", "model", "connection"],
        "cache": ["cache", "memory", "pool", "buffer"],
        "config": ["config", "setting", "env", "constant"],
        "utils": ["util", "helper", "common", "tool"],
        "middleware": ["middleware", "handler", "interceptor"],
        "api": ["api", "endpoint", "route", "controller"],
        "service": ["service", "manager", "handler", "processor"]
    }
    
    def __init__(self, task: str = "easy"):
        """Initialize the baseline agent."""
        self.task = task
        self.env = BugTriageEnv(Config(task=task))
    
    def _extract_bug_type_from_report(self, bug_report: str) -> str:
        """Extract likely bug type from bug report using heuristics."""
        report_lower = bug_report.lower()
        
        # Score each bug type based on keyword matches
        scores = {}
        for bug_type, keywords in self.BUG_TYPE_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in report_lower)
            scores[bug_type] = score
        
        # Return highest scoring bug type, or random if no matches
        if max(scores.values()) > 0:
            return max(scores, key=scores.get)
        return random.choice(self.BUG_TYPES)
    
    def _select_likely_file(self, modules: List[str], bug_type: str) -> str:
        """Select likely problematic file based on bug type and module names."""
        # Score each module based on relevance to bug type
        scores = {}
        for module in modules:
            module_lower = module.lower()
            score = 0
            
            # Check for direct bug type match
            if bug_type.replace("_", "").lower() in module_lower:
                score += 3
            
            # Check for file type keywords
            for file_type, keywords in self.FILE_KEYWORDS.items():
                if any(kw in module_lower for kw in keywords):
                    # Boost score if file type matches bug type
                    if bug_type in file_type or file_type in bug_type:
                        score += 2
                    else:
                        score += 1
            
            scores[module] = score
        
        # Return highest scoring module, or random if no matches
        if max(scores.values()) > 0:
            return max(scores, key=scores.get)
        return random.choice(modules)
    
    def _generate_fix_suggestion(self, bug_type: str, file_name: str) -> str:
        """Generate a reasonable fix suggestion based on bug type."""
        fix_templates = {
            "memory": "Implement proper memory management with cleanup handlers and resource pooling",
            "logic": "Review and fix the algorithm logic to ensure correct computation",
            "authentication": "Strengthen authentication checks and credential validation",
            "database": "Optimize database queries and implement connection pooling",
            "performance": "Add caching, optimize algorithms, and reduce computational overhead",
            "null_pointer": "Add null/undefined checks before accessing object properties",
            "session": "Fix session management and timeout configuration",
            "race_condition": "Add synchronization primitives (locks, mutexes) to protect shared resources"
        }
        return fix_templates.get(bug_type, "Fix the issue by addressing the root cause")
    
    def run_episode(self) -> Dict[str, Any]:
        """Run a single episode and return results."""
        obs = self.env.reset()
        total_reward = 0.0
        steps_data = []
        
        # Extract bug type from report for intelligent predictions
        predicted_bug_type = self._extract_bug_type_from_report(obs.bug_report)
        predicted_file = self._select_likely_file(obs.repo_modules, predicted_bug_type)
        
        for step in range(3):
            # Make intelligent predictions based on step
            if step == 0:
                # Step 1: Focus on bug type
                action = BugAction(
                    bug_type=predicted_bug_type,
                    file=random.choice(obs.repo_modules),
                    fix="Analyze the bug"
                )
            elif step == 1:
                # Step 2: Focus on file
                action = BugAction(
                    bug_type=predicted_bug_type,
                    file=predicted_file,
                    fix="Locate the problematic code"
                )
            else:
                # Step 3: Focus on fix
                action = BugAction(
                    bug_type=predicted_bug_type,
                    file=predicted_file,
                    fix=self._generate_fix_suggestion(predicted_bug_type, predicted_file)
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
            "success": total_reward > 0.0,
            "predicted_bug_type": predicted_bug_type,
            "predicted_file": predicted_file
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
