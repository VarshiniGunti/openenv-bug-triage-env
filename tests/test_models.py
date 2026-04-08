"""Tests for Pydantic models."""

import pytest
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.action import BugAction, BUG_TYPES
from models.observation import BugObservation
from models.scenario import BugScenario
from models.config import Config


class TestBugAction:
    """Tests for BugAction model."""
    
    def test_valid_action(self):
        """Test creating a valid BugAction."""
        action = BugAction(
            bug_type="null_pointer",
            file="auth.py",
            fix="Add null check"
        )
        assert action.bug_type == "null_pointer"
        assert action.file == "auth.py"
        assert action.fix == "Add null check"
    
    def test_invalid_bug_type(self):
        """Test that invalid bug_type raises error."""
        with pytest.raises(ValueError):
            BugAction(
                bug_type="invalid_type",
                file="auth.py",
                fix="Add null check"
            )
    
    def test_empty_bug_type(self):
        """Test that empty bug_type raises error."""
        with pytest.raises(ValueError):
            BugAction(
                bug_type="",
                file="auth.py",
                fix="Add null check"
            )
    
    def test_empty_file(self):
        """Test that empty file raises error."""
        with pytest.raises(ValueError):
            BugAction(
                bug_type="null_pointer",
                file="",
                fix="Add null check"
            )
    
    def test_empty_fix(self):
        """Test that empty fix raises error."""
        with pytest.raises(ValueError):
            BugAction(
                bug_type="null_pointer",
                file="auth.py",
                fix=""
            )
    
    def test_all_bug_types_valid(self):
        """Test that all bug types in vocabulary are valid."""
        for bug_type in BUG_TYPES:
            action = BugAction(
                bug_type=bug_type,
                file="test.py",
                fix="test fix"
            )
            assert action.bug_type == bug_type
    
    def test_json_serialization(self):
        """Test JSON serialization."""
        action = BugAction(
            bug_type="logic",
            file="calculator.py",
            fix="Fix arithmetic"
        )
        json_str = action.model_dump_json()
        assert "logic" in json_str
        assert "calculator.py" in json_str
    
    def test_json_deserialization(self):
        """Test JSON deserialization."""
        json_str = '{"bug_type": "memory", "file": "cache.py", "fix": "Add cleanup"}'
        action = BugAction.model_validate_json(json_str)
        assert action.bug_type == "memory"
        assert action.file == "cache.py"


class TestBugObservation:
    """Tests for BugObservation model."""
    
    def test_valid_observation(self):
        """Test creating a valid BugObservation."""
        obs = BugObservation(
            bug_report="NullPointerException in auth",
            repo_modules=["auth.py", "user.py"],
            previous_actions=[]
        )
        assert obs.bug_report == "NullPointerException in auth"
        assert len(obs.repo_modules) == 2
        assert obs.previous_actions == []
    
    def test_empty_bug_report(self):
        """Test that empty bug_report raises error."""
        with pytest.raises(ValueError):
            BugObservation(
                bug_report="",
                repo_modules=["auth.py"]
            )
    
    def test_empty_repo_modules(self):
        """Test that empty repo_modules raises error."""
        with pytest.raises(ValueError):
            BugObservation(
                bug_report="Bug report",
                repo_modules=[]
            )
    
    def test_json_serialization(self):
        """Test JSON serialization."""
        obs = BugObservation(
            bug_report="Test bug",
            repo_modules=["file1.py", "file2.py"]
        )
        json_str = obs.model_dump_json()
        assert "Test bug" in json_str
        assert "file1.py" in json_str


class TestBugScenario:
    """Tests for BugScenario model."""
    
    def test_valid_scenario(self):
        """Test creating a valid BugScenario."""
        scenario = BugScenario(
            bug_report="Memory leak in cache",
            ground_truth_type="memory",
            ground_truth_file="cache.py",
            ground_truth_fix="Add cleanup",
            repo_modules=["cache.py", "utils.py"]
        )
        assert scenario.ground_truth_type == "memory"
        assert scenario.ground_truth_file == "cache.py"
    
    def test_empty_fields(self):
        """Test that empty fields raise errors."""
        with pytest.raises(ValueError):
            BugScenario(
                bug_report="",
                ground_truth_type="memory",
                ground_truth_file="cache.py",
                ground_truth_fix="Fix",
                repo_modules=["cache.py"]
            )


class TestConfig:
    """Tests for Config model."""
    
    def test_default_config(self):
        """Test default configuration."""
        config = Config()
        assert config.task == "easy"
        assert config.max_steps == 3
        assert config.seed is None
    
    def test_custom_config(self):
        """Test custom configuration."""
        config = Config(task="hard", max_steps=5, seed=42)
        assert config.task == "hard"
        assert config.max_steps == 5
        assert config.seed == 42
    
    def test_invalid_task(self):
        """Test that invalid task raises error."""
        with pytest.raises(ValueError):
            Config(task="invalid")
    
    def test_invalid_max_steps(self):
        """Test that invalid max_steps raises error."""
        with pytest.raises(ValueError):
            Config(max_steps=0)
    
    def test_valid_tasks(self):
        """Test all valid tasks."""
        for task in ["easy", "medium", "hard"]:
            config = Config(task=task)
            assert config.task == task
