"""OpenEnv Bug Triage Environment implementation."""

import random
import sys
import os
import json
import importlib
from typing import Tuple, Dict, Any, Optional, List

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.observation import BugObservation
from models.action import BugAction
from models.scenario import BugScenario
from models.config import Config
from tasks import EASY_SCENARIOS, MEDIUM_SCENARIOS, HARD_SCENARIOS
from graders import EasyGrader, MediumGrader, HardGrader
try:
    from core.logging_config import get_logger
except ImportError:
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


def get_tasks() -> List[Dict[str, Any]]:
    """Get all available tasks with grader instances."""
    tasks_dict = load_tasks_with_graders()
    tasks_list = []
    for task_id, task in tasks_dict.items():
        if "grader_instance" in task:
            task_info = {
                "id": task.get("id"),
                "input": task.get("input"),
                "expected_output": task.get("expected_output"),
                "grader": task["grader_instance"]
            }
            tasks_list.append(task_info)
    return tasks_list


def get_graders() -> List[Dict[str, Any]]:
    """Get all available graders."""
    return [
        {
            "name": "EasyGrader",
            "class": "graders.easy_grader.EasyGrader",
            "description": "Grader for easy-level bug triage tasks"
        },
        {
            "name": "MediumGrader",
            "class": "graders.medium_grader.MediumGrader",
            "description": "Grader for medium-level bug triage tasks"
        },
        {
            "name": "HardGrader",
            "class": "graders.hard_grader.HardGrader",
            "description": "Grader for hard-level bug triage tasks"
        }
    ]


class BugTriageEnv:
    """
    OpenEnv Bug Triage Environment.
    
    Implements the OpenEnv API with reset(), step(), and state() methods.
    Supports three task difficulties: easy, medium, hard.
    Episodes consist of exactly 3 steps with cumulative rewards.
    """
    
    def __init__(self, config: Optional[Config] = None):
        """Initialize the environment."""
        self.config = config or Config()
        self.logger = get_logger()
        
        if self.config.seed is not None:
            random.seed(self.config.seed)
        
        self.scenarios = self._load_scenarios()
        self.grader = self._select_grader()
        
        self.current_scenario: Optional[BugScenario] = None
        self.step_count = 0
        self.previous_actions = []
        self.episode_rewards = []
        
        self.logger.info(f"Environment initialized with task={self.config.task}")
    
    def _load_scenarios(self) -> list:
        """Load scenarios based on configured task."""
        if self.config.task == "easy":
            scenarios = EASY_SCENARIOS
        elif self.config.task == "medium":
            scenarios = MEDIUM_SCENARIOS
        elif self.config.task == "hard":
            scenarios = HARD_SCENARIOS
        else:
            raise ValueError(f"Unknown task: {self.config.task}")
        
        normalized_scenarios = []
        for scenario_dict in scenarios:
            normalized_dict = scenario_dict.copy()
            normalized_dict["ground_truth_type"] = normalize_bug_type(scenario_dict["ground_truth_type"])
            normalized_dict["ground_truth_file"] = normalize_file(scenario_dict["ground_truth_file"])
            normalized_dict["ground_truth_fix"] = normalize_fix_text(scenario_dict["ground_truth_fix"])
            normalized_scenarios.append(BugScenario(**normalized_dict))
        
        return normalized_scenarios
    
    def _select_grader(self):
        """Select grader based on configured task."""
        if self.config.task == "easy":
            return EasyGrader()
        elif self.config.task == "medium":
            return MediumGrader()
        elif self.config.task == "hard":
            return HardGrader()
        else:
            raise ValueError(f"Unknown task: {self.config.task}")
    
    def reset(self) -> BugObservation:
        """Reset the environment and start a new episode."""
        self.step_count = 0
        self.previous_actions = []
        self.episode_rewards = []
        
        self.current_scenario = random.choice(self.scenarios)
        
        self.logger.info(f"Episode reset: task={self.config.task}")
        
        return BugObservation(
            bug_report=self.current_scenario.bug_report,
            repo_modules=self.current_scenario.repo_modules,
            previous_actions=[]
        )
    
    def step(self, action: BugAction) -> Tuple[BugObservation, float, bool, Dict[str, Any]]:
        """Execute one step of the environment."""
        if self.current_scenario is None:
            raise RuntimeError("Environment not initialized. Call reset() first.")
        
        self.step_count += 1
        
        normalized_action = BugAction(
            bug_type=normalize_bug_type(action.bug_type),
            file=normalize_file(action.file),
            fix=normalize_fix_text(action.fix)
        )
        
        reward = self.grader.grade(normalized_action, self.current_scenario, self.step_count)
        reward = min(max(reward, 0.0), 1.0)
        
        self.episode_rewards.append(reward)
        
        action_str = f"step_{self.step_count}: {action.model_dump_json()}"
        self.previous_actions.append(action_str)
        
        done = self.step_count >= self.config.max_steps
        
        self.logger.info(f"Step {self.step_count}: reward={reward:.2f}, done={done}")
        
        observation = BugObservation(
            bug_report=self.current_scenario.bug_report,
            repo_modules=self.current_scenario.repo_modules,
            previous_actions=self.previous_actions.copy()
        )
        
        info = {
            "step": self.step_count,
            "total_reward": sum(self.episode_rewards),
            "done": done
        }
        
        return observation, reward, done, info
    
    def state(self) -> Dict[str, Any]:
        """Get the current environment state."""
        return {
            "task_name": self.config.task,
            "step_count": self.step_count,
            "max_steps": self.config.max_steps,
            "previous_actions": self.previous_actions.copy()
        }
