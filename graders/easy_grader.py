"""Grader for Easy task - evaluates bug_type only."""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.action import BugAction
from models.scenario import BugScenario


class EasyGrader:
    """
    Grader for Easy task difficulty.
    
    Evaluates only the bug_type field in step 1.
    Reward: 0.3 for correct bug_type, 0.0 otherwise.
    """
    
    def grade(self, action: BugAction, scenario: BugScenario, step: int) -> float:
        """
        Grade an action for the Easy task.
        
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
        else:
            # Steps 2 and 3: No reward for Easy task
            return 0.05  # Strictly between 0 and 1
