"""Grader for Medium task - evaluates bug_type and file."""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.action import BugAction
from models.scenario import BugScenario


class MediumGrader:
    """
    Grader for Medium task difficulty.
    
    Step 1: Evaluates bug_type (0.3 reward)
    Step 2: Evaluates file (0.3 reward)
    Step 3: No reward
    Total normalized reward: [0.0, 1.0]
    """
    
    def grade(self, action: BugAction, scenario: BugScenario, step: int) -> float:
        """
        Grade an action for the Medium task.
        
        Args:
            action: The agent's action
            scenario: The bug scenario with ground truth
            step: The current step (1, 2, or 3)
            
        Returns:
            Reward value strictly between 0 and 1 (exclusive)
        """
        if step == 1:
            # Step 1: Evaluate bug_type
            if action.bug_type == scenario.ground_truth_type:
                return 0.35  # Strictly between 0 and 1
            else:
                return 0.05  # Strictly between 0 and 1
        elif step == 2:
            # Step 2: Evaluate file
            if action.file == scenario.ground_truth_file:
                return 0.35  # Strictly between 0 and 1
            else:
                return 0.05  # Strictly between 0 and 1
        else:
            # Step 3: No reward for Medium task
            return 0.05  # Strictly between 0 and 1
