"""FastAPI server for OpenEnv Bug Triage Environment using openenv-core create_app."""

import os
import sys
import random
from typing import Optional, Dict, Any, List
from uuid import uuid4

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from openenv.core.env_server.interfaces import Environment
from openenv.core.env_server.types import State
from openenv.core.env_server.http_server import create_app

from models.config import Config
from models.action import BugAction
from models.observation import BugObservation
from tasks import EASY_SCENARIOS, MEDIUM_SCENARIOS, HARD_SCENARIOS
from graders import EasyGrader, MediumGrader, HardGrader
from utils.normalization import normalize_bug_type, normalize_file, normalize_fix_text
from models.scenario import BugScenario


class BugTriageEnvironment(Environment):
    """
    OpenEnv Bug Triage Environment implementing the openenv-core Environment interface.
    Supports three task difficulties: easy, medium, hard.
    """

    SUPPORTS_CONCURRENT_SESSIONS: bool = True

    def __init__(self):
        self._state = State(episode_id=str(uuid4()), step_count=0)
        self._task: str = "easy"
        self._max_steps: int = 3
        self._current_scenario: Optional[BugScenario] = None
        self._previous_actions: List[str] = []
        self._episode_rewards: List[float] = []
        self._grader = EasyGrader()
        self._scenarios: List[BugScenario] = self._load_scenarios("easy")

    def _load_scenarios(self, task: str) -> List[BugScenario]:
        raw = {"easy": EASY_SCENARIOS, "medium": MEDIUM_SCENARIOS, "hard": HARD_SCENARIOS}.get(task, EASY_SCENARIOS)
        result = []
        for s in raw:
            d = s.copy()
            d["ground_truth_type"] = normalize_bug_type(d["ground_truth_type"])
            d["ground_truth_file"] = normalize_file(d["ground_truth_file"])
            d["ground_truth_fix"] = normalize_fix_text(d["ground_truth_fix"])
            result.append(BugScenario(**d))
        return result

    def _select_grader(self, task: str):
        return {"easy": EasyGrader, "medium": MediumGrader, "hard": HardGrader}.get(task, EasyGrader)()

    def reset(
        self,
        task: Optional[str] = None,
        seed: Optional[int] = None,
        episode_id: Optional[str] = None,
    ) -> BugObservation:
        if task and task in ("easy", "medium", "hard"):
            self._task = task
            self._scenarios = self._load_scenarios(task)
            self._grader = self._select_grader(task)

        if seed is not None:
            random.seed(seed)

        self._previous_actions = []
        self._episode_rewards = []
        self._current_scenario = random.choice(self._scenarios)

        self._state = State(
            episode_id=episode_id or str(uuid4()),
            step_count=0,
        )

        return BugObservation(
            bug_report=self._current_scenario.bug_report,
            repo_modules=self._current_scenario.repo_modules,
            previous_actions=[],
        )

    def step(self, action: BugAction) -> BugObservation:  # type: ignore[override]
        if self._current_scenario is None:
            return BugObservation(
                bug_report="No active episode. Call reset() first.",
                repo_modules=["main.py"],
                previous_actions=[],
                reward=0.0,
                done=True,
            )

        self._state.step_count += 1
        step_num = self._state.step_count

        norm_action = BugAction(
            bug_type=normalize_bug_type(action.bug_type),
            file=normalize_file(action.file),
            fix=normalize_fix_text(action.fix),
        )

        reward = self._grader.grade(norm_action, self._current_scenario, step_num)
        reward = float(min(max(reward, 0.0), 1.0))
        self._episode_rewards.append(reward)

        action_str = f"step_{step_num}: {action.model_dump_json()}"
        self._previous_actions.append(action_str)

        done = step_num >= self._max_steps

        return BugObservation(
            bug_report=self._current_scenario.bug_report,
            repo_modules=self._current_scenario.repo_modules,
            previous_actions=self._previous_actions.copy(),
            reward=reward,
            done=done,
        )

    @property
    def state(self) -> State:
        return self._state


# Create the app using openenv-core's create_app
app = create_app(
    BugTriageEnvironment,
    BugAction,
    BugObservation,
    env_name="openenv-bug-triage-env",
    max_concurrent_envs=10,
)


def main(host: str = "0.0.0.0", port: int = 7860):
    """Entry point for the server."""
    import uvicorn
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=7860)
    args = parser.parse_args()
    main()