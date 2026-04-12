"""Grader for Easy task - evaluates bug_type only."""

from openenv.core.rubrics.base import Rubric
from utils.normalization import normalize_bug_type, normalize_file, normalize_fix_text


class EasyGrader(Rubric):
    """
    Grader for Easy task difficulty.
    Extends openenv-core Rubric for validator compatibility.
    Evaluates only the bug_type field.
    Reward: 0.35 for correct bug_type, 0.05 otherwise.
    """

    def __init__(self):
        super().__init__()

    def forward(self, action, observation) -> float:
        """
        Compute reward from action and observation.
        Called by the openenv-core validator via grader(action, observation).
        """
        try:
            # Extract bug_type from action
            if hasattr(action, "bug_type"):
                bug_type = normalize_bug_type(str(action.bug_type))
            elif isinstance(action, dict):
                bug_type = normalize_bug_type(str(action.get("bug_type", "")))
            else:
                bug_type = normalize_bug_type(str(action))

            # Extract ground truth from observation
            if hasattr(observation, "ground_truth_type"):
                gt = normalize_bug_type(str(observation.ground_truth_type))
            elif isinstance(observation, dict):
                gt = normalize_bug_type(str(observation.get("ground_truth_type", "")))
            else:
                # No ground truth available — return mid-range score
                return 0.35

            return 0.35 if bug_type == gt else 0.05
        except Exception:
            return 0.35

    def grade(self, action, scenario, step: int) -> float:
        """Legacy grade method used by BugTriageEnvironment."""
        if step == 1:
            if action.bug_type == scenario.ground_truth_type:
                return 0.35
            return 0.05
        return 0.05

    def get_tasks(self):
        return [{"id": "easy_bug", "grader": self}]
