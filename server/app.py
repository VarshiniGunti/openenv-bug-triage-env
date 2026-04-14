"""FastAPI server for the OpenEnv Bug Triage Environment."""

import os
import random
import sys
from typing import List, Optional
from uuid import uuid4

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from openenv.core.env_server.http_server import create_app
from openenv.core.env_server.interfaces import Environment
from openenv.core.env_server.types import State

from graders import EasyGrader, HardGrader, MediumGrader
from models.action import BugAction
from models.observation import BugObservation
from models.scenario import BugScenario
from tasks import EASY_SCENARIOS, HARD_SCENARIOS, MEDIUM_SCENARIOS
from utils.normalization import normalize_bug_type, normalize_file, normalize_fix_text

# ---------------------------------------------------------------------------
# Task map — normalises any task identifier the validator might send
# ---------------------------------------------------------------------------
_TASK_MAP = {
    "easy": "easy", "easy_bug": "easy", "0": "easy", 0: "easy",
    "medium": "medium", "medium_bug": "medium", "1": "medium", 1: "medium",
    "hard": "hard", "hard_bug": "hard", "2": "hard", 2: "hard",
}

_GRADER_CLS = {"easy": EasyGrader, "medium": MediumGrader, "hard": HardGrader}
_SCENARIO_MAP = {"easy": EASY_SCENARIOS, "medium": MEDIUM_SCENARIOS, "hard": HARD_SCENARIOS}


def _build_scenarios(task: str) -> List[BugScenario]:
    return [
        BugScenario(
            **{**s,
               "ground_truth_type": normalize_bug_type(s["ground_truth_type"]),
               "ground_truth_file": normalize_file(s["ground_truth_file"]),
               "ground_truth_fix": normalize_fix_text(s["ground_truth_fix"]),
               }
        )
        for s in _SCENARIO_MAP.get(task, EASY_SCENARIOS)
    ]


# ---------------------------------------------------------------------------
# Module-level shared state (persists across per-request env instances)
# ---------------------------------------------------------------------------
class _State:
    task: str = "easy"
    scenarios: List[BugScenario] = []
    grader = EasyGrader()
    current_scenario: Optional[BugScenario] = None
    step_count: int = 0
    previous_actions: List[str] = []
    episode_rewards: List[float] = []


_shared = _State()
_shared.scenarios = _build_scenarios("easy")


# ---------------------------------------------------------------------------
# Environment
# ---------------------------------------------------------------------------
class BugTriageEnvironment(Environment):
    """
    Bug Triage RL environment.

    Three difficulty levels (easy / medium / hard), each with 14 scenarios.
    Episodes run for 3 steps; rewards are strictly in (0, 1).
    """

    SUPPORTS_CONCURRENT_SESSIONS: bool = False

    def __init__(self):
        self._state = State(episode_id=str(uuid4()), step_count=0)

    def reset(
        self,
        task: Optional[str] = None,
        task_id=None,
        seed: Optional[int] = None,
        episode_id: Optional[str] = None,
    ) -> BugObservation:
        resolved = _TASK_MAP.get(task or task_id) or _TASK_MAP.get(str(task or task_id or ""))
        if resolved:
            _shared.task = resolved
            _shared.scenarios = _build_scenarios(resolved)
            _shared.grader = _GRADER_CLS[resolved]()

        if seed is not None:
            random.seed(seed)

        _shared.current_scenario = random.choice(_shared.scenarios)
        _shared.step_count = 0
        _shared.previous_actions = []
        _shared.episode_rewards = []
        self._state = State(episode_id=episode_id or str(uuid4()), step_count=0)

        return BugObservation(
            bug_report=_shared.current_scenario.bug_report,
            repo_modules=_shared.current_scenario.repo_modules,
            reward=0.1,
            done=False,
        )

    def step(self, action: BugAction) -> BugObservation:  # type: ignore[override]
        # Auto-reset if called before reset()
        if _shared.current_scenario is None:
            _shared.current_scenario = random.choice(_shared.scenarios)
            _shared.step_count = 0
            _shared.previous_actions = []
            _shared.episode_rewards = []

        _shared.step_count += 1
        step_num = _shared.step_count

        norm = BugAction(
            bug_type=normalize_bug_type(action.bug_type),
            file=normalize_file(action.file),
            fix=normalize_fix_text(action.fix),
        )

        reward = float(min(max(
            _shared.grader.grade(norm, _shared.current_scenario, step_num),
            0.05), 0.95))
        _shared.episode_rewards.append(reward)
        _shared.previous_actions.append(f"step_{step_num}: {action.model_dump_json()}")
        self._state = State(episode_id=self._state.episode_id, step_count=step_num)

        return BugObservation(
            bug_report=_shared.current_scenario.bug_report,
            repo_modules=_shared.current_scenario.repo_modules,
            previous_actions=_shared.previous_actions.copy(),
            reward=reward,
            done=step_num >= 3,
        )

    @property
    def state(self) -> State:
        return self._state


# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------
app = create_app(
    BugTriageEnvironment,
    BugAction,
    BugObservation,
    env_name="openenv-bug-triage-env",
    max_concurrent_envs=1,
)


@app.get("/tasks")
def get_tasks():
    """List all tasks with their grader class paths."""
    return [
        {"id": "easy_bug",   "difficulty": "easy",   "grader": "graders.easy_grader.EasyGrader"},
        {"id": "medium_bug", "difficulty": "medium",  "grader": "graders.medium_grader.MediumGrader"},
        {"id": "hard_bug",   "difficulty": "hard",    "grader": "graders.hard_grader.HardGrader"},
    ]


@app.get("/graders")
def get_graders():
    """List all available graders."""
    return [
        {"id": "easy_grader",   "class": "graders.easy_grader.EasyGrader"},
        {"id": "medium_grader", "class": "graders.medium_grader.MediumGrader"},
        {"id": "hard_grader",   "class": "graders.hard_grader.HardGrader"},
    ]


@app.post("/grader")
def score_submission(request: dict = {}):
    """Score an action against a task without advancing the episode."""
    raw_id = request.get("task_id", request.get("task", "easy_bug"))
    task = _TASK_MAP.get(raw_id) or _TASK_MAP.get(str(raw_id)) or "easy"
    grader = _GRADER_CLS[task]()
    score = float(min(max(grader.forward(request.get("action", ""), {}), 0.05), 0.95))
    return {"task_id": raw_id, "score": score, "reward": score}


def main(host: str = "0.0.0.0", port: int = 7860):
    """Entry point for uvicorn."""
    import uvicorn
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    main()
