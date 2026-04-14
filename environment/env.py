"""Bug Triage environment — used by inference.py and baseline agent."""

import random
from typing import Any, Dict, List, Optional, Tuple

from graders import EasyGrader, HardGrader, MediumGrader
from models.action import BugAction
from models.config import Config
from models.observation import BugObservation
from models.scenario import BugScenario
from tasks import EASY_SCENARIOS, HARD_SCENARIOS, MEDIUM_SCENARIOS
from utils.normalization import normalize_bug_type, normalize_file, normalize_fix_text

try:
    from core.logging_config import get_logger
except ImportError:
    import logging
    def get_logger():
        return logging.getLogger(__name__)


class BugTriageEnv:
    """
    Bug Triage environment for direct use (inference / baseline agent).

    Supports three difficulty levels: easy, medium, hard.
    Each episode runs for exactly 3 steps.
    """

    _SCENARIOS = {"easy": EASY_SCENARIOS, "medium": MEDIUM_SCENARIOS, "hard": HARD_SCENARIOS}
    _GRADERS = {"easy": EasyGrader, "medium": MediumGrader, "hard": HardGrader}

    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config()
        self.logger = get_logger()

        if self.config.seed is not None:
            random.seed(self.config.seed)

        self.scenarios = self._load_scenarios()
        self.grader = self._GRADERS[self.config.task]()
        self.current_scenario: Optional[BugScenario] = None
        self.step_count = 0
        self.previous_actions: List[str] = []
        self.episode_rewards: List[float] = []

    def _load_scenarios(self) -> List[BugScenario]:
        raw = self._SCENARIOS.get(self.config.task, EASY_SCENARIOS)
        return [
            BugScenario(
                **{**s,
                   "ground_truth_type": normalize_bug_type(s["ground_truth_type"]),
                   "ground_truth_file": normalize_file(s["ground_truth_file"]),
                   "ground_truth_fix": normalize_fix_text(s["ground_truth_fix"]),
                   }
            )
            for s in raw
        ]

    def reset(self) -> BugObservation:
        self.step_count = 0
        self.previous_actions = []
        self.episode_rewards = []
        self.current_scenario = random.choice(self.scenarios)
        self.logger.info(f"Episode reset: task={self.config.task}")
        return BugObservation(
            bug_report=self.current_scenario.bug_report,
            repo_modules=self.current_scenario.repo_modules,
        )

    def step(self, action: BugAction) -> Tuple[BugObservation, float, bool, Dict[str, Any]]:
        if self.current_scenario is None:
            raise RuntimeError("Call reset() before step().")

        self.step_count += 1
        norm = BugAction(
            bug_type=normalize_bug_type(action.bug_type),
            file=normalize_file(action.file),
            fix=normalize_fix_text(action.fix),
        )
        reward = float(min(max(
            self.grader.grade(norm, self.current_scenario, self.step_count),
            0.05), 0.95))
        self.episode_rewards.append(reward)
        self.previous_actions.append(f"step_{self.step_count}: {action.model_dump_json()}")
        done = self.step_count >= self.config.max_steps
        self.logger.info(f"Step {self.step_count}: reward={reward:.2f}, done={done}")

        obs = BugObservation(
            bug_report=self.current_scenario.bug_report,
            repo_modules=self.current_scenario.repo_modules,
            previous_actions=self.previous_actions.copy(),
        )
        return obs, reward, done, {"step": self.step_count, "done": done}

    def state(self) -> Dict[str, Any]:
        return {
            "task": self.config.task,
            "step_count": self.step_count,
            "max_steps": self.config.max_steps,
        }
