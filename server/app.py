"""FastAPI server for OpenEnv Bug Triage Environment using openenv-core create_app."""

import os
import sys
import random
from typing import Optional, List
from uuid import uuid4

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from openenv.core.env_server.interfaces import Environment
from openenv.core.env_server.types import State
from openenv.core.env_server.http_server import create_app

from models.action import BugAction
from models.observation import BugObservation
from tasks import EASY_SCENARIOS, MEDIUM_SCENARIOS, HARD_SCENARIOS
from graders import EasyGrader, MediumGrader, HardGrader
from utils.normalization import normalize_bug_type, normalize_file, normalize_fix_text
from models.scenario import BugScenario


# ---------------------------------------------------------------------------
# Shared state — persists across the per-request env instances that
# create_app creates.  All BugTriageEnvironment instances read/write here.
# ---------------------------------------------------------------------------
class _SharedState:
    task: str = "easy"
    max_steps: int = 3
    current_scenario: Optional[BugScenario] = None
    previous_actions: List[str] = []
    episode_rewards: List[float] = []
    step_count: int = 0
    grader = EasyGrader()
    scenarios: List[BugScenario] = []

_shared = _SharedState()


def _load_scenarios(task: str) -> List[BugScenario]:
    raw = {"easy": EASY_SCENARIOS, "medium": MEDIUM_SCENARIOS, "hard": HARD_SCENARIOS}.get(task, EASY_SCENARIOS)
    result = []
    for s in raw:
        d = s.copy()
        d["ground_truth_type"] = normalize_bug_type(d["ground_truth_type"])
        d["ground_truth_file"] = normalize_file(d["ground_truth_file"])
        d["ground_truth_fix"] = normalize_fix_text(d["ground_truth_fix"])
        result.append(BugScenario(**d))
    return result


# Pre-load scenarios
_shared.scenarios = _load_scenarios("easy")


class BugTriageEnvironment(Environment):
    """
    OpenEnv Bug Triage Environment.
    Uses class-level shared state so reset()/step() work across
    the per-request instances that create_app creates.
    """

    SUPPORTS_CONCURRENT_SESSIONS: bool = False

    def __init__(self):
        self._state = State(episode_id=str(uuid4()), step_count=0)

    def reset(
        self,
        task: Optional[str] = None,
        seed: Optional[int] = None,
        episode_id: Optional[str] = None,
    ) -> BugObservation:
        global _shared

        if task and task in ("easy", "medium", "hard"):
            _shared.task = task
            _shared.scenarios = _load_scenarios(task)
            _shared.grader = {"easy": EasyGrader, "medium": MediumGrader, "hard": HardGrader}[task]()

        if seed is not None:
            random.seed(seed)

        _shared.previous_actions = []
        _shared.episode_rewards = []
        _shared.step_count = 0
        _shared.current_scenario = random.choice(_shared.scenarios)

        self._state = State(episode_id=episode_id or str(uuid4()), step_count=0)

        return BugObservation(
            bug_report=_shared.current_scenario.bug_report,
            repo_modules=_shared.current_scenario.repo_modules,
            previous_actions=[],
            reward=0.0,
            done=False,
        )

    def step(self, action: BugAction) -> BugObservation:  # type: ignore[override]
        global _shared

        if _shared.current_scenario is None:
            return BugObservation(
                bug_report="No active episode. Call reset() first.",
                repo_modules=["main.py"],
                previous_actions=[],
                reward=0.05,
                done=True,
            )

        _shared.step_count += 1
        step_num = _shared.step_count

        norm_action = BugAction(
            bug_type=normalize_bug_type(action.bug_type),
            file=normalize_file(action.file),
            fix=normalize_fix_text(action.fix),
        )

        reward = _shared.grader.grade(norm_action, _shared.current_scenario, step_num)
        # Ensure strictly between 0 and 1 (exclusive)
        reward = float(min(max(reward, 0.05), 0.95))
        _shared.episode_rewards.append(reward)

        action_str = f"step_{step_num}: {action.model_dump_json()}"
        _shared.previous_actions.append(action_str)

        done = step_num >= _shared.max_steps

        self._state = State(episode_id=self._state.episode_id, step_count=step_num)

        return BugObservation(
            bug_report=_shared.current_scenario.bug_report,
            repo_modules=_shared.current_scenario.repo_modules,
            previous_actions=_shared.previous_actions.copy(),
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
    max_concurrent_envs=1,
)

# ---------------------------------------------------------------------------
# Additional endpoints required by the hackathon Phase 2 validator
# ---------------------------------------------------------------------------
from fastapi import FastAPI
from fastapi.routing import APIRoute

@app.get("/tasks")
def get_tasks():
    """Return all tasks with grader class paths — required by Phase 2 validator."""
    return [
        {
            "id": "easy_bug",
            "description": "Easy bug triage - classify bug type",
            "grader": "graders.easy_grader.EasyGrader",
            "grader_class": "graders.easy_grader.EasyGrader",
        },
        {
            "id": "medium_bug",
            "description": "Medium bug triage - classify bug type and file",
            "grader": "graders.medium_grader.MediumGrader",
            "grader_class": "graders.medium_grader.MediumGrader",
        },
        {
            "id": "hard_bug",
            "description": "Hard bug triage - classify bug type, file, and fix",
            "grader": "graders.hard_grader.HardGrader",
            "grader_class": "graders.hard_grader.HardGrader",
        },
    ]


@app.get("/graders")
def get_graders():
    """Return all graders — required by Phase 2 validator."""
    return [
        {"id": "easy_grader", "class": "graders.easy_grader.EasyGrader"},
        {"id": "medium_grader", "class": "graders.medium_grader.MediumGrader"},
        {"id": "hard_grader", "class": "graders.hard_grader.HardGrader"},
    ]


def main(host: str = "0.0.0.0", port: int = 7860):
    """Entry point for the server."""
    import uvicorn
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    main()
