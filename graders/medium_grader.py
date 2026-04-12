"""Grader for Medium task - evaluates bug_type and file."""

from utils.normalization import normalize_bug_type, normalize_file


class MediumGrader:
    """
    Grader for Medium task difficulty.
    Implements both grade() for internal use and forward() for openenv-core Rubric compatibility.
    Reward: 0.35 per correct field, 0.05 otherwise.
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
            file_val = normalize_file(
                str(action.file) if hasattr(action, "file")
                else str(action.get("file", "")) if isinstance(action, dict)
                else ""
            )
            gt_type = normalize_bug_type(
                str(observation.ground_truth_type) if hasattr(observation, "ground_truth_type")
                else str(observation.get("ground_truth_type", "")) if isinstance(observation, dict)
                else ""
            )
            gt_file = normalize_file(
                str(observation.ground_truth_file) if hasattr(observation, "ground_truth_file")
                else str(observation.get("ground_truth_file", "")) if isinstance(observation, dict)
                else ""
            )
            score = (0.35 if bug_type == gt_type else 0.05) + (0.35 if file_val == gt_file else 0.05)
            return min(max(score / 2, 0.05), 0.95)
        except Exception:
            return 0.35

    def __call__(self, action, observation) -> float:
        return self.forward(action, observation)

    def grade(self, action, scenario, step: int) -> float:
        """Legacy grade method used by BugTriageEnvironment."""
        if step == 1:
            return 0.35 if action.bug_type == scenario.ground_truth_type else 0.05
        elif step == 2:
            return 0.35 if action.file == scenario.ground_truth_file else 0.05
        return 0.05

    def get_tasks(self):
        return [{"id": "medium_bug", "grader": self}]
