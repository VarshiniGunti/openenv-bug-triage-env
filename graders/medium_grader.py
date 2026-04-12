"""Grader for Medium task - evaluates bug_type and file."""

from openenv.core.rubrics.base import Rubric
from utils.normalization import normalize_bug_type, normalize_file


class MediumGrader(Rubric):
    """
    Grader for Medium task difficulty.
    Extends openenv-core Rubric for validator compatibility.
    Step 1: bug_type, Step 2: file.
    Reward: 0.35 per correct field, 0.05 otherwise.
    """

    def __init__(self):
        super().__init__()

    def forward(self, action, observation) -> float:
        """
        Compute reward from action and observation.
        Called by the openenv-core validator via grader(action, observation).
        """
        try:
            if hasattr(action, "bug_type"):
                bug_type = normalize_bug_type(str(action.bug_type))
                file_val = normalize_file(str(action.file))
            elif isinstance(action, dict):
                bug_type = normalize_bug_type(str(action.get("bug_type", "")))
                file_val = normalize_file(str(action.get("file", "")))
            else:
                return 0.35

            if hasattr(observation, "ground_truth_type"):
                gt_type = normalize_bug_type(str(observation.ground_truth_type))
                gt_file = normalize_file(str(observation.ground_truth_file))
            elif isinstance(observation, dict):
                gt_type = normalize_bug_type(str(observation.get("ground_truth_type", "")))
                gt_file = normalize_file(str(observation.get("ground_truth_file", "")))
            else:
                return 0.35

            score = 0.0
            if bug_type == gt_type:
                score += 0.35
            else:
                score += 0.05
            if file_val == gt_file:
                score += 0.35
            else:
                score += 0.05
            # Return average to stay in (0,1)
            return min(max(score / 2, 0.05), 0.95)
        except Exception:
            return 0.35

    def grade(self, action, scenario, step: int) -> float:
        """Legacy grade method used by BugTriageEnvironment."""
        if step == 1:
            return 0.35 if action.bug_type == scenario.ground_truth_type else 0.05
        elif step == 2:
            return 0.35 if action.file == scenario.ground_truth_file else 0.05
        return 0.05

    def get_tasks(self):
        return [{"id": "medium_bug", "grader": self}]
