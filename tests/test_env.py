"""Tests for BugTriageEnv environment."""

import pytest
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.config import Config
from models.action import BugAction
from models.observation import BugObservation
from env import BugTriageEnv


class TestBugTriageEnv:
    """Tests for BugTriageEnv class."""
    
    def test_env_initialization(self):
        """Test environment initialization."""
        config = Config(task="easy", seed=42)
        env = BugTriageEnv(config)
        assert env.config.task == "easy"
        assert env.step_count == 0
        assert env.previous_actions == []
    
    def test_reset_returns_observation(self):
        """Test that reset returns a valid observation."""
        env = BugTriageEnv(Config(task="easy"))
        obs = env.reset()
        assert obs.bug_report is not None
        assert len(obs.repo_modules) > 0
        assert obs.previous_actions == []
    
    def test_reset_clears_state(self):
        """Test that reset clears episode state."""
        env = BugTriageEnv(Config(task="easy"))
        
        # First episode
        env.reset()
        action = BugAction(bug_type="null_pointer", file="auth.py", fix="Add check")
        env.step(action)
        
        # Reset
        env.reset()
        assert env.step_count == 0
        assert env.previous_actions == []
        assert env.episode_rewards == []
    
    def test_step_increments_counter(self):
        """Test that step increments the step counter."""
        env = BugTriageEnv(Config(task="easy"))
        env.reset()
        
        action = BugAction(bug_type="null_pointer", file="auth.py", fix="Add check")
        env.step(action)
        assert env.step_count == 1
        
        env.step(action)
        assert env.step_count == 2
    
    def test_step_returns_tuple(self):
        """Test that step returns correct tuple."""
        env = BugTriageEnv(Config(task="easy"))
        env.reset()
        
        action = BugAction(bug_type="null_pointer", file="auth.py", fix="Add check")
        result = env.step(action)
        
        assert len(result) == 4
        obs, reward, done, info = result
        assert obs is not None
        assert isinstance(reward, float)
        assert isinstance(done, bool)
        assert isinstance(info, dict)
    
    def test_done_flag_after_3_steps(self):
        """Test that done flag is set after 3 steps."""
        env = BugTriageEnv(Config(task="easy", max_steps=3))
        env.reset()
        
        action = BugAction(bug_type="null_pointer", file="auth.py", fix="Add check")
        
        # Steps 1 and 2 should not be done
        _, _, done, _ = env.step(action)
        assert done is False
        
        _, _, done, _ = env.step(action)
        assert done is False
        
        # Step 3 should be done
        _, _, done, _ = env.step(action)
        assert done is True
    
    def test_state_method(self):
        """Test state method returns correct information."""
        env = BugTriageEnv(Config(task="medium", seed=42))
        env.reset()
        
        state = env.state()
        assert state["task_name"] == "medium"
        assert state["step_count"] == 0
        assert state["max_steps"] == 3
        assert state["previous_actions"] == []
        assert state["current_scenario"] is not None
    
    def test_reproducibility_with_seed(self):
        """Test that same seed produces same scenarios."""
        config1 = Config(task="easy", seed=42)
        env1 = BugTriageEnv(config1)
        obs1 = env1.reset()
        
        config2 = Config(task="easy", seed=42)
        env2 = BugTriageEnv(config2)
        obs2 = env2.reset()
        
        assert obs1.bug_report == obs2.bug_report
        assert obs1.repo_modules == obs2.repo_modules
    
    def test_different_seeds_different_scenarios(self):
        """Test that different seeds produce different scenarios."""
        config1 = Config(task="easy", seed=42)
        env1 = BugTriageEnv(config1)
        obs1 = env1.reset()
        
        config2 = Config(task="easy", seed=43)
        env2 = BugTriageEnv(config2)
        obs2 = env2.reset()
        
        # Very likely to be different (though not guaranteed)
        assert obs1.bug_report != obs2.bug_report or obs1.repo_modules != obs2.repo_modules
    
    def test_easy_task_grading(self):
        """Test Easy task grading."""
        env = BugTriageEnv(Config(task="easy", seed=42))
        env.reset()
        
        # Get the correct bug type from the scenario
        correct_type = env.current_scenario.ground_truth_type
        
        action = BugAction(
            bug_type=correct_type,
            file="test.py",
            fix="test fix"
        )
        _, reward, _, _ = env.step(action)
        assert reward == 0.3
    
    def test_medium_task_grading(self):
        """Test Medium task grading."""
        env = BugTriageEnv(Config(task="medium", seed=42))
        env.reset()
        
        correct_type = env.current_scenario.ground_truth_type
        correct_file = env.current_scenario.ground_truth_file
        
        # Step 1: correct bug type
        action1 = BugAction(bug_type=correct_type, file="wrong.py", fix="test fix")
        _, reward1, _, _ = env.step(action1)
        assert reward1 == 0.3
        
        # Step 2: correct file
        action2 = BugAction(bug_type=correct_type, file=correct_file, fix="test fix")
        _, reward2, _, _ = env.step(action2)
        assert reward2 == 0.3
    
    def test_hard_task_grading(self):
        """Test Hard task grading."""
        env = BugTriageEnv(Config(task="hard", seed=42))
        env.reset()
        
        correct_type = env.current_scenario.ground_truth_type
        correct_file = env.current_scenario.ground_truth_file
        correct_fix = env.current_scenario.ground_truth_fix
        
        # Step 1: correct bug type
        action1 = BugAction(bug_type=correct_type, file="wrong.py", fix="test fix")
        _, reward1, _, _ = env.step(action1)
        assert reward1 == 0.3
        
        # Step 2: correct file
        action2 = BugAction(bug_type=correct_type, file=correct_file, fix="test fix")
        _, reward2, _, _ = env.step(action2)
        assert reward2 == 0.3
        
        # Step 3: fix with keywords
        action3 = BugAction(bug_type=correct_type, file=correct_file, fix=correct_fix)
        _, reward3, _, _ = env.step(action3)
        assert reward3 == 0.4
    
    def test_full_episode_easy(self):
        """Test full 3-step episode with Easy task."""
        env = BugTriageEnv(Config(task="easy", seed=42))
        obs = env.reset()
        
        assert obs.bug_report is not None
        assert len(obs.repo_modules) >= 3
        
        action = BugAction(
            bug_type=env.current_scenario.ground_truth_type,
            file="test.py",
            fix="test fix"
        )
        
        total_reward = 0
        for step in range(3):
            obs, reward, done, info = env.step(action)
            total_reward += reward
            
            if step < 2:
                assert done is False
            else:
                assert done is True
        
        assert total_reward == 0.3  # Only step 1 gives reward for Easy
    
    def test_full_episode_medium(self):
        """Test full 3-step episode with Medium task."""
        env = BugTriageEnv(Config(task="medium", seed=42))
        env.reset()
        
        correct_type = env.current_scenario.ground_truth_type
        correct_file = env.current_scenario.ground_truth_file
        
        total_reward = 0
        
        # Step 1
        action1 = BugAction(bug_type=correct_type, file="wrong.py", fix="test fix")
        _, reward1, _, _ = env.step(action1)
        total_reward += reward1
        
        # Step 2
        action2 = BugAction(bug_type=correct_type, file=correct_file, fix="test fix")
        _, reward2, done, _ = env.step(action2)
        total_reward += reward2
        
        # Step 3
        action3 = BugAction(bug_type=correct_type, file=correct_file, fix="test fix")
        _, reward3, done, _ = env.step(action3)
        total_reward += reward3
        
        assert done is True
        assert total_reward == 0.6  # 0.3 + 0.3 + 0.0
    
    def test_full_episode_hard(self):
        """Test full 3-step episode with Hard task."""
        env = BugTriageEnv(Config(task="hard", seed=42))
        env.reset()
        
        correct_type = env.current_scenario.ground_truth_type
        correct_file = env.current_scenario.ground_truth_file
        correct_fix = env.current_scenario.ground_truth_fix
        
        total_reward = 0
        
        # Step 1
        action1 = BugAction(bug_type=correct_type, file="wrong.py", fix="test fix")
        _, reward1, _, _ = env.step(action1)
        total_reward += reward1
        
        # Step 2
        action2 = BugAction(bug_type=correct_type, file=correct_file, fix="test fix")
        _, reward2, _, _ = env.step(action2)
        total_reward += reward2
        
        # Step 3
        action3 = BugAction(bug_type=correct_type, file=correct_file, fix=correct_fix)
        _, reward3, done, _ = env.step(action3)
        total_reward += reward3
        
        assert done is True
        assert total_reward == 1.0  # 0.3 + 0.3 + 0.4
    
    def test_multiple_episodes(self):
        """Test running multiple episodes sequentially."""
        env = BugTriageEnv(Config(task="easy"))
        
        for episode in range(5):
            obs = env.reset()
            assert obs.bug_report is not None
            
            action = BugAction(bug_type="null_pointer", file="test.py", fix="test fix")
            for step in range(3):
                obs, reward, done, info = env.step(action)
                if step == 2:
                    assert done is True

    def test_reset_last_action_is_none(self):
        """Test that reset() returns observation with last_action=None."""
        env = BugTriageEnv(Config(task="easy"))
        obs = env.reset()
        
        assert obs.last_action is None
        assert isinstance(obs, BugObservation)
    
    def test_step_last_action_populated(self):
        """Test that step() returns observation with last_action populated."""
        env = BugTriageEnv(Config(task="easy"))
        env.reset()
        
        action = BugAction(bug_type="null_pointer", file="test.py", fix="test fix")
        obs, reward, done, info = env.step(action)
        
        assert obs.last_action is not None
        assert obs.last_action["bug_type"] == "null_pointer"
        assert obs.last_action["file"] == "test.py"
        assert obs.last_action["fix"] == "test fix"
    
    def test_step_last_action_echoes_normalized_action(self):
        """Test that last_action contains normalized action values."""
        env = BugTriageEnv(Config(task="easy"))
        env.reset()
        
        # Use action with values that might be normalized
        action = BugAction(bug_type="memory", file="cache.py", fix="clear cache when session expires")
        obs, reward, done, info = env.step(action)
        
        assert obs.last_action is not None
        assert isinstance(obs.last_action, dict)
        assert "bug_type" in obs.last_action
        assert "file" in obs.last_action
        assert "fix" in obs.last_action
    
    def test_multiple_steps_last_action_updates(self):
        """Test that last_action updates with each step."""
        env = BugTriageEnv(Config(task="easy"))
        env.reset()
        
        action1 = BugAction(bug_type="null_pointer", file="user.py", fix="add null check")
        obs1, _, _, _ = env.step(action1)
        assert obs1.last_action["bug_type"] == "null_pointer"
        assert obs1.last_action["file"] == "user.py"
        
        action2 = BugAction(bug_type="memory", file="cache.py", fix="clear cache properly")
        obs2, _, _, _ = env.step(action2)
        assert obs2.last_action["bug_type"] == "memory"
        assert obs2.last_action["file"] == "cache.py"
