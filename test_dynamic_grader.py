#!/usr/bin/env python
"""Test script to verify dynamic grader loading."""

from core.env import BugTriageEnv
from models.config import Config
from models.action import BugAction

# Test easy task
print("Testing Easy Task...")
env = BugTriageEnv(Config(task='easy'))
obs = env.reset()
print(f"✓ Episode started with grader: {type(env.grader).__name__}")

# Take 3 steps
for i in range(3):
    action = BugAction(bug_type='authentication', file='auth.py', fix='Add null check')
    obs, reward, done, info = env.step(action)
    print(f"  Step {i+1}: reward={reward:.2f}, total_reward={info['total_reward']:.2f}, done={done}")

print("✓ Easy task episode completed successfully\n")

# Test medium task
print("Testing Medium Task...")
env = BugTriageEnv(Config(task='medium'))
obs = env.reset()
print(f"✓ Episode started with grader: {type(env.grader).__name__}")

for i in range(3):
    action = BugAction(bug_type='database', file='connection_pool.py', fix='Add timeout')
    obs, reward, done, info = env.step(action)
    print(f"  Step {i+1}: reward={reward:.2f}, total_reward={info['total_reward']:.2f}, done={done}")

print("✓ Medium task episode completed successfully\n")

# Test hard task
print("Testing Hard Task...")
env = BugTriageEnv(Config(task='hard'))
obs = env.reset()
print(f"✓ Episode started with grader: {type(env.grader).__name__}")

for i in range(3):
    action = BugAction(bug_type='memory', file='cache_handler.py', fix='Add cache eviction')
    obs, reward, done, info = env.step(action)
    print(f"  Step {i+1}: reward={reward:.2f}, total_reward={info['total_reward']:.2f}, done={done}")

print("✓ Hard task episode completed successfully\n")

print("=" * 60)
print("✓ ALL TESTS PASSED - Dynamic grader loading works!")
print("=" * 60)
