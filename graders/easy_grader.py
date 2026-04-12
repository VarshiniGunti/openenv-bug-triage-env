"""Grader for Easy task - evaluates bug_type only."""

from models.action import BugAction
from models.scenario import BugScenario
from utils.normalization import normalize_bug_type


class EasyGrader:
    """
    Grader for Easy task difficulty.
    Implements both grade() for internal use and forward() for openenv-core Rubric compatibility.
    Reward: 0.35 for correct bug_type, 0.05 otherwise.
    """

    def __init__(self):
        pass

    def forward(self, action, observation) -> float:
        """Called by openenv-core validator as grader(action, observation)."""
        try:
            bug_type = normalize_bug_type(
                str(action.bug_type) if hasattr(action, "bug_type")
                else str(action.get("bug_type", "")) if isinstance(action, dict)
                else str(action)
            )
            gt = normalize_bug_type(
                str(observation.ground_truth_type) if hasattr(observation, "ground_truth_type")
                else str(observation.get("ground_truth_type", "")) if isinstance(observation, dict)
                else ""
            )
            return 0.35 if (bug_type and gt and bug_type == gt) else 0.05
        except Exception:
            return 0.35

    def __call__(self, action, observation) -> float:
        """Make grader callable — required by openenv-core Rubric interface."""
        return self.forward(action, observation)

    def grade(self, action, scenario, step: int) -> float:
        """Legacy grade method used by BugTriageEnvironment."""
        if step == 1:
            return 0.35 if action.bug_type == scenario.ground_truth_type else 0.05
        return 0.05

    def get_tasks(self):
        return [{"id": "easy_bug", "grader": self}]
