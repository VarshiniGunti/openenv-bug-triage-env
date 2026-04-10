"""Main BugTriageEnv environment implementation with OpenEnv server wrapper."""

import random
import sys
import os
import json
import importlib
from typing import Tuple, Dict, Any, Optional

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models.observation import BugObservation
from models.action import BugAction
from models.scenario import BugScenario
from models.config import Config
from tasks import EASY_SCENARIOS, MEDIUM_SCENARIOS, HARD_SCENARIOS
from graders import EasyGrader, MediumGrader, HardGrader
from logging_config import get_logger
from utils.normalization import normalize_bug_type, normalize_file, normalize_fix_text


def load_grader(grader_path: str):
    """
    Dynamically load and instantiate a grader from a module path.
    
    Args:
        grader_path: Full path to grader class (e.g., "graders.easy_grader.EasyGrader")
        
    Returns:
        Instantiated grader object
    """
    try:
        module_path, class_name = grader_path.rsplit(".", 1)
        module = importlib.import_module(module_path)
        grader_class = getattr(module, class_name)
        return grader_class()
    except Exception as e:
        raise RuntimeError(f"Failed to load grader {grader_path}: {e}")


def load_tasks_with_graders(tasks_dir: str = "tasks") -> Dict[str, Dict[str, Any]]:
    """
    Load all task definitions from JSON files in the tasks directory.
    
    Args:
        tasks_dir: Directory containing task JSON files
        
    Returns:
        Dictionary mapping task IDs to task definitions with loaded graders
    """
    tasks = {}
    
    # Get the absolute path to the tasks directory
    if not os.path.isabs(tasks_dir):
        tasks_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), tasks_dir)
    
    if not os.path.isdir(tasks_dir):
        raise RuntimeError(f"Tasks directory not found: {tasks_dir}")
    
    # Map task IDs to grader paths
    grader_map = {
        "easy_bug": "graders.easy_grader.EasyGrader",
        "medium_bug": "graders.medium_grader.MediumGrader",
        "hard_bug": "graders.hard_grader.HardGrader"
    }
    
    # Load all JSON files from the tasks directory
    for filename in sorted(os.listdir(tasks_dir)):
        if filename.endswith(".json"):
            filepath = os.path.join(tasks_dir, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    task = json.load(f)
                
                # Get task ID and map to grader
                task_id = task.get("id")
                if task_id in grader_map:
                    grader_path = grader_map[task_id]
                    task["grader_instance"] = load_grader(grader_path)
                
                tasks[task_id] = task
            except Exception as e:
                raise RuntimeError(f"Failed to load task from {filepath}: {e}")
    
    return tasks


class BugTriageEnv:
    """
    OpenEnv Bug Triage Environment.
    
    Implements the OpenEnv API with reset(), step(), and state() methods.
    Supports three task difficulties: easy, medium, hard.
    Episodes consist of exactly 3 steps with cumulative rewards.
    """
    
    def __init__(self, config: Optional[Config] = None):
        """
        Initialize the environment.
        
        Args:
            config: Configuration object (uses defaults if None)
        """
        self.config = config or Config()
        self.logger = get_logger()
        
        # Set random seed if provided
        if self.config.seed is not None:
            random.seed(self.config.seed)
        
        # Load tasks from directory with graders
        self.tasks = load_tasks_with_graders()
        self.current_task = None
        
        # Load scenarios based on task
        self.scenarios = self._load_scenarios()
        
        # Select grader based on task
        self.grader = self._select_grader()
        
        # Episode state
        self.current_scenario: Optional[BugScenario] = None
        self.step_count = 0
        self.previous_actions = []
        self.episode_rewards = []
        
        self.logger.info(f"Environment initialized with task={self.config.task}, max_steps={self.config.max_steps}")
        self.logger.info(f"Loaded {len(self.tasks)} tasks with graders")
        
        # Debug: Print task information
        print("TASK COUNT:", len(self.tasks))
        for task_id, task in self.tasks.items():
            grader = task.get("grader_instance")
            grader_type = type(grader).__name__ if grader else "None"
            print(f"TASK: {task_id} GRADER TYPE: {grader_type}")
    
    def _load_scenarios(self) -> list:
        """Load scenarios based on configured task and normalize ground truth values."""
        if self.config.task == "easy":
            scenarios = EASY_SCENARIOS
        elif self.config.task == "medium":
            scenarios = MEDIUM_SCENARIOS
        elif self.config.task == "hard":
            scenarios = HARD_SCENARIOS
        else:
            raise ValueError(f"Unknown task: {self.config.task}")
        
        # Normalize ground truth values in scenarios for consistent grading
        normalized_scenarios = []
        for scenario_dict in scenarios:
            normalized_dict = scenario_dict.copy()
            normalized_dict["ground_truth_type"] = normalize_bug_type(scenario_dict["ground_truth_type"])
            normalized_dict["ground_truth_file"] = normalize_file(scenario_dict["ground_truth_file"])
            normalized_dict["ground_truth_fix"] = normalize_fix_text(scenario_dict["ground_truth_fix"])
            normalized_scenarios.append(BugScenario(**normalized_dict))
        
        return normalized_scenarios
    
    def _select_grader(self):
        """Select grader based on configured task from loaded tasks."""
        # Map task difficulty to task ID
        task_id_map = {
            "easy": "easy_bug",
            "medium": "medium_bug",
            "hard": "hard_bug"
        }
        
        task_id = task_id_map.get(self.config.task)
        if not task_id or task_id not in self.tasks:
            raise ValueError(f"Unknown task: {self.config.task}")
        
        task = self.tasks[task_id]
        if "grader_instance" not in task:
            raise RuntimeError(f"Task {task_id} does not have a grader instance")
        
        return task["grader_instance"]
    
    def _generate_module_descriptions(self, modules: list) -> dict:
        """
        Generate simple descriptions for modules to help agent reasoning.
        
        Args:
            modules: List of module names
            
        Returns:
            Dictionary mapping module names to descriptions
        """
        descriptions = {}
        for module in modules:
            # Extract module name without extension
            module_name = module.replace(".py", "").lower()
            
            # Generate simple, non-leaking descriptions based on module name
            if "auth" in module_name:
                descriptions[module] = "Handles authentication and user session management"
            elif "user" in module_name:
                descriptions[module] = "Manages user profile data and user-related operations"
            elif "database" in module_name or "db" in module_name:
                descriptions[module] = "Provides database connection and query utilities"
            elif "cache" in module_name:
                descriptions[module] = "Implements caching layer for performance optimization"
            elif "api" in module_name or "server" in module_name:
                descriptions[module] = "Handles API endpoints and server request processing"
            elif "model" in module_name:
                descriptions[module] = "Defines data models and business logic"
            elif "util" in module_name or "helper" in module_name:
                descriptions[module] = "Provides utility functions and helper methods"
            elif "config" in module_name:
                descriptions[module] = "Manages application configuration and settings"
            elif "logger" in module_name or "log" in module_name:
                descriptions[module] = "Handles logging and debugging functionality"
            else:
                # Generic description for unknown modules
                descriptions[module] = f"Module for {module_name} functionality"
        
        return descriptions
    
    def reset(self) -> BugObservation:
        """
        Reset the environment and start a new episode.
        
        Returns:
            Initial BugObservation for the new episode
        """
        # Clear episode state
        self.step_count = 0
        self.previous_actions = []
        self.episode_rewards = []
        
        # Select random scenario
        self.current_scenario = random.choice(self.scenarios)
        
        self.logger.info(
            f"Episode reset: task={self.config.task}, "
            f"scenario_id={id(self.current_scenario)}"
        )
        
        # Generate module descriptions for this scenario
        module_descriptions = self._generate_module_descriptions(self.current_scenario.repo_modules)
        
        # Return initial observation with triage hint and module descriptions
        return BugObservation(
            bug_report=self.current_scenario.bug_report,
            repo_modules=self.current_scenario.repo_modules,
            previous_actions=[],
            triage_hint="Bug triage workflow: Classify bug type from vocabulary. Identify most likely affected module. Propose a short fix description.",
            module_descriptions=module_descriptions,
            last_action=None
        )
    
    def step(self, action: BugAction) -> Tuple[BugObservation, float, bool, Dict[str, Any]]:
        """
        Execute one step of the environment.
        
        Args:
            action: The agent's action
            
        Returns:
            Tuple of (observation, reward, done, info)
        """
        if self.current_scenario is None:
            raise RuntimeError("Environment not initialized. Call reset() first.")
        
        # Increment step counter
        self.step_count += 1
        
        # Normalize action for LLM robustness
        normalized_action = BugAction(
            bug_type=normalize_bug_type(action.bug_type),
            file=normalize_file(action.file),
            fix=normalize_fix_text(action.fix)
        )
        
        # Grade the normalized action
        reward = self.grader.grade(normalized_action, self.current_scenario, self.step_count)
        
        # Clamp reward to [0.0, 1.0] to prevent edge-case validator failures
        reward = min(max(reward, 0.0), 1.0)
        
        self.episode_rewards.append(reward)
        
        # Track action (use original action for logging)
        action_str = f"step_{self.step_count}: {action.model_dump_json()}"
        self.previous_actions.append(action_str)
        
        # Check if episode is done
        done = self.step_count >= self.config.max_steps
        
        self.logger.info(
            f"Step {self.step_count}: action={normalized_action.bug_type}, "
            f"reward={reward:.2f}, done={done}"
        )
        
        # Create observation for next step with triage hint and module descriptions
        module_descriptions = self._generate_module_descriptions(self.current_scenario.repo_modules)
        observation = BugObservation(
            bug_report=self.current_scenario.bug_report,
            repo_modules=self.current_scenario.repo_modules,
            previous_actions=self.previous_actions.copy(),
            triage_hint="Bug triage workflow: Classify bug type from vocabulary. Identify most likely affected module. Propose a short fix description.",
            module_descriptions=module_descriptions,
            last_action=normalized_action.model_dump()
        )
        
        # Create info dict
        info = {
            "step": self.step_count,
            "total_reward": sum(self.episode_rewards),
            "done": done
        }
        
        return observation, reward, done, info
    
    def state(self) -> Dict[str, Any]:
        """
        Get the current environment state without modifying it.
        
        Returns:
            Dictionary with state information
        """
        return {
            "task_name": self.config.task,
            "scenario_id": id(self.current_scenario) if self.current_scenario else None,
            "step_count": self.step_count,
            "max_steps": self.config.max_steps,
            "previous_actions": self.previous_actions.copy(),
            "current_scenario": self.current_scenario.model_dump() if self.current_scenario else None
        }
    
    def get_tasks(self) -> list:
        """
        Get all loaded tasks with their grader instances.
        
        Returns:
            List of tasks with grader instances that can be called
        """
        tasks_list = []
        for task_id, task in self.tasks.items():
            if "grader_instance" in task:
                task_info = {
                    "id": task.get("id"),
                    "input": task.get("input"),
                    "expected_output": task.get("expected_output"),
                    "grader": task["grader_instance"]
                }
                tasks_list.append(task_info)
        
        self.logger.debug(f"Returning {len(tasks_list)} tasks with graders")
        return tasks_list
    
    def get_tasks_with_graders(self) -> list:
        """
        Get all loaded tasks with their graders (alias for get_tasks).
        
        Returns:
            List of tasks with grader instances
        """
        return self.get_tasks()


# OpenEnv Server Wrapper
class OpenEnvServer:
    """
    OpenEnv-compliant HTTP server wrapper for BugTriageEnv.
    
    Exposes the environment via HTTP endpoints:
    - POST /reset
    - POST /step
    - POST /state
    """
    
    def __init__(self, env: BugTriageEnv, host: str = "0.0.0.0", port: int = 5000):
        """
        Initialize the OpenEnv server.
        
        Args:
            env: BugTriageEnv instance
            host: Server host
            port: Server port
        """
        self.env = env
        self.host = host
        self.port = port
        self.logger = get_logger()
        
        try:
            from flask import Flask, request, jsonify
            self.app = Flask(__name__)
            
            # Register routes
            @self.app.route("/reset", methods=["POST"])
            def reset():
                """Reset endpoint."""
                try:
                    obs = self.env.reset()
                    return jsonify({
                        "observation": {
                            "bug_report": obs.bug_report,
                            "repo_modules": obs.repo_modules,
                            "previous_actions": obs.previous_actions
                        }
                    })
                except Exception as e:
                    self.logger.error(f"Reset failed: {e}")
                    return jsonify({"error": str(e)}), 500
            
            @self.app.route("/step", methods=["POST"])
            def step():
                """Step endpoint."""
                try:
                    data = request.json
                    action = BugAction(**data)
                    obs, reward, done, info = self.env.step(action)
                    
                    return jsonify({
                        "observation": {
                            "bug_report": obs.bug_report,
                            "repo_modules": obs.repo_modules,
                            "previous_actions": obs.previous_actions
                        },
                        "reward": reward,
                        "done": done,
                        "info": info
                    })
                except Exception as e:
                    self.logger.error(f"Step failed: {e}")
                    return jsonify({"error": str(e)}), 500
            
            @self.app.route("/state", methods=["POST"])
            def state():
                """State endpoint."""
                try:
                    state = self.env.state()
                    return jsonify(state)
                except Exception as e:
                    self.logger.error(f"State failed: {e}")
                    return jsonify({"error": str(e)}), 500
            
            @self.app.route("/health", methods=["GET"])
            def health():
                """Health check endpoint."""
                return jsonify({"status": "healthy"})
        
        except ImportError:
            self.logger.error("Flask not installed. Install with: pip install flask")
            raise
    
    def run(self):
        """Run the server."""
        self.logger.info(f"Starting OpenEnv server on {self.host}:{self.port}")
        self.app.run(host=self.host, port=self.port, debug=False)


# Main entry point for server
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Run OpenEnv Bug Triage Environment server")
    parser.add_argument("--task", default="easy", choices=["easy", "medium", "hard"],
                       help="Task difficulty level")
    parser.add_argument("--host", default="0.0.0.0", help="Server host")
    parser.add_argument("--port", type=int, default=5000, help="Server port")
    parser.add_argument("--seed", type=int, help="Random seed for reproducibility")
    
    args = parser.parse_args()
    
    # Create environment
    config = Config(task=args.task, max_steps=3, seed=args.seed)
    env = BugTriageEnv(config)
    
    # Create and run server
    server = OpenEnvServer(env, host=args.host, port=args.port)
    server.run()
