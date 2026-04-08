"""Tests for grading system."""

import pytest
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.action import BugAction
from models.scenario import BugScenario
from graders import EasyGrader, MediumGrader, HardGrader


class TestEasyGrader:
    """Tests for Easy task grader."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.grader = EasyGrader()
        self.scenario = BugScenario(
            bug_report="NullPointerException",
            ground_truth_type="null_pointer",
            ground_truth_file="auth.py",
            ground_truth_fix="Add null check",
            repo_modules=["auth.py", "user.py"]
        )
    
    def test_correct_bug_type_step1(self):
        """Test correct bug type in step 1."""
        action = BugAction(
            bug_type="null_pointer",
            file="auth.py",
            fix="Add null check"
        )
        reward = self.grader.grade(action, self.scenario, step=1)
        assert reward == 0.3
    
    def test_incorrect_bug_type_step1(self):
        """Test incorrect bug type in step 1."""
        action = BugAction(
            bug_type="logic",
            file="auth.py",
            fix="Add null check"
        )
        reward = self.grader.grade(action, self.scenario, step=1)
        assert reward == 0.0
    
    def test_no_reward_step2(self):
        """Test no reward in step 2."""
        action = BugAction(
            bug_type="null_pointer",
            file="auth.py",
            fix="Add null check"
        )
        reward = self.grader.grade(action, self.scenario, step=2)
        assert reward == 0.0
    
    def test_no_reward_step3(self):
        """Test no reward in step 3."""
        action = BugAction(
            bug_type="null_pointer",
            file="auth.py",
            fix="Add null check"
        )
        reward = self.grader.grade(action, self.scenario, step=3)
        assert reward == 0.0


class TestMediumGrader:
    """Tests for Medium task grader."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.grader = MediumGrader()
        self.scenario = BugScenario(
            bug_report="Performance issue",
            ground_truth_type="performance",
            ground_truth_file="database.py",
            ground_truth_fix="Add index",
            repo_modules=["database.py", "query.py", "cache.py"]
        )
    
    def test_correct_bug_type_step1(self):
        """Test correct bug type in step 1."""
        action = BugAction(
            bug_type="performance",
            file="database.py",
            fix="Add index"
        )
        reward = self.grader.grade(action, self.scenario, step=1)
        assert reward == 0.3
    
    def test_incorrect_bug_type_step1(self):
        """Test incorrect bug type in step 1."""
        action = BugAction(
            bug_type="logic",
            file="database.py",
            fix="Add index"
        )
        reward = self.grader.grade(action, self.scenario, step=1)
        assert reward == 0.0
    
    def test_correct_file_step2(self):
        """Test correct file in step 2."""
        action = BugAction(
            bug_type="performance",
            file="database.py",
            fix="Add index"
        )
        reward = self.grader.grade(action, self.scenario, step=2)
        assert reward == 0.3
    
    def test_incorrect_file_step2(self):
        """Test incorrect file in step 2."""
        action = BugAction(
            bug_type="performance",
            file="cache.py",
            fix="Add index"
        )
        reward = self.grader.grade(action, self.scenario, step=2)
        assert reward == 0.0
    
    def test_no_reward_step3(self):
        """Test no reward in step 3."""
        action = BugAction(
            bug_type="performance",
            file="database.py",
            fix="Add index"
        )
        reward = self.grader.grade(action, self.scenario, step=3)
        assert reward == 0.0


class TestHardGrader:
    """Tests for Hard task grader."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.grader = HardGrader()
        self.scenario = BugScenario(
            bug_report="Memory leak in cache",
            ground_truth_type="memory",
            ground_truth_file="cache.py",
            ground_truth_fix="Implement proper cache eviction policy",
            repo_modules=["cache.py", "memory.py", "utils.py"]
        )
    
    def test_correct_bug_type_step1(self):
        """Test correct bug type in step 1."""
        action = BugAction(
            bug_type="memory",
            file="cache.py",
            fix="Implement cache eviction"
        )
        reward = self.grader.grade(action, self.scenario, step=1)
        assert reward == 0.3
    
    def test_correct_file_step2(self):
        """Test correct file in step 2."""
        action = BugAction(
            bug_type="memory",
            file="cache.py",
            fix="Implement cache eviction"
        )
        reward = self.grader.grade(action, self.scenario, step=2)
        assert reward == 0.3
    
    def test_keyword_match_step3(self):
        """Test keyword matching in step 3."""
        action = BugAction(
            bug_type="memory",
            file="cache.py",
            fix="Add cache eviction mechanism"
        )
        reward = self.grader.grade(action, self.scenario, step=3)
        assert reward == 0.4
    
    def test_no_keyword_match_step3(self):
        """Test no keyword match in step 3."""
        action = BugAction(
            bug_type="memory",
            file="cache.py",
            fix="Fix the bug"
        )
        reward = self.grader.grade(action, self.scenario, step=3)
        assert reward == 0.0
    
    def test_keyword_extraction(self):
        """Test keyword extraction."""
        keywords = self.grader.extract_keywords("Implement proper cache eviction policy")
        assert "implement" in keywords
        assert "cache" in keywords
        assert "eviction" in keywords
        assert "policy" in keywords
        # Stopwords should be excluded
        assert "the" not in keywords  # Stopword
    
    def test_case_insensitive_matching(self):
        """Test case-insensitive keyword matching."""
        action = BugAction(
            bug_type="memory",
            file="cache.py",
            fix="IMPLEMENT CACHE EVICTION POLICY"
        )
        reward = self.grader.grade(action, self.scenario, step=3)
        assert reward == 0.4
