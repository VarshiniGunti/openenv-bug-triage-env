#!/usr/bin/env python
"""Verification script for the bug triage environment."""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from env import BugTriageEnv
from models.config import Config
from models.action import BugAction

def verify_environment():
    """Verify the environment works correctly."""
    
    print("=" * 60)
    print("OpenEnv Bug Triage Environment - Verification")
    print("=" * 60)
    
    # Test Easy task
    print("\n[1] Testing Easy task...")
    config = Config(task='easy', seed=42)
    env = BugTriageEnv(config)
    obs = env.reset()
    print(f"    ✓ Easy task initialized")
    print(f"      - Bug report length: {len(obs.bug_report)} chars")
    print(f"      - Modules: {len(obs.repo_modules)} modules")
    
    action = BugAction(bug_type='null_pointer', file='test.py', fix='test fix')
    obs, reward, done, info = env.step(action)
    print(f"    ✓ Step executed: reward={reward:.2f}")
    
    # Test Medium task
    print("\n[2] Testing Medium task...")
    config = Config(task='medium', seed=42)
    env = BugTriageEnv(config)
    obs = env.reset()
    print(f"    ✓ Medium task initialized")
    print(f"      - Modules: {len(obs.repo_modules)} modules")
    
    # Test Hard task
    print("\n[3] Testing Hard task...")
    config = Config(task='hard', seed=42)
    env = BugTriageEnv(config)
    obs = env.reset()
    print(f"    ✓ Hard task initialized")
    print(f"      - Modules: {len(obs.repo_modules)} modules")
    
    # Test state method
    print("\n[4] Testing state method...")
    state = env.state()
    print(f"    ✓ State method works")
    print(f"      - Task: {state['task_name']}")
    print(f"      - Step: {state['step_count']}/{state['max_steps']}")
    
    # Test full episode
    print("\n[5] Testing full 3-step episode...")
    config = Config(task='easy', seed=42)
    env = BugTriageEnv(config)
    obs = env.reset()
    
    total_reward = 0
    for step in range(3):
        action = BugAction(
            bug_type=env.current_scenario.ground_truth_type,
            file='test.py',
            fix='test fix'
        )
        obs, reward, done, info = env.step(action)
        total_reward += reward
        print(f"    Step {step+1}: reward={reward:.2f}, done={done}")
    
    print(f"    ✓ Episode completed: total_reward={total_reward:.2f}")
    # Test reproducibility
    print("\n[6] Testing reproducibility with seed...")
    config1 = Config(task='easy', seed=42)
    env1 = BugTriageEnv(config1)
    obs1 = env1.reset()
    
    config2 = Config(task='easy', seed=42)
    env2 = BugTriageEnv(config2)
    obs2 = env2.reset()
    
    if obs1.bug_report == obs2.bug_report:
        print(f"    ✓ Reproducibility verified")
    else:
        print(f"    ✗ Reproducibility failed")
        return False
    
    print("\n" + "=" * 60)
    print("✓ All verification tests passed!")
    print("=" * 60)
    return True

if __name__ == "__main__":
    success = verify_environment()
    sys.exit(0 if success else 1)
