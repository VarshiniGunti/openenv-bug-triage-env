#!/usr/bin/env python
"""Final submission verification script."""

import os
import sys
import yaml

print("=" * 70)
print("FINAL SUBMISSION VERIFICATION")
print("=" * 70)

# Check 1: Required files exist
print("\n[1] Checking required files...")
required_files = [
    'openenv.yaml',
    'Dockerfile',
    'inference.py',
    'pyproject.toml',
    'README.md'
]

all_files_exist = True
for file in required_files:
    exists = os.path.exists(file)
    status = "[OK]" if exists else "[FAIL]"
    print(f"  {status} {file}")
    if not exists:
        all_files_exist = False

# Check 2: Required directories exist
print("\n[2] Checking required directories...")
required_dirs = [
    'graders',
    'tasks',
    'models',
    'environment',
    'baseline'
]

all_dirs_exist = True
for dir in required_dirs:
    exists = os.path.isdir(dir)
    status = "[OK]" if exists else "[FAIL]"
    print(f"  {status} {dir}/")
    if not exists:
        all_dirs_exist = False

# Check 3: openenv.yaml structure
print("\n[3] Checking openenv.yaml structure...")
try:
    with open('openenv.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    has_tasks = 'tasks' in config and len(config['tasks']) >= 3
    has_graders = 'graders' in config and len(config['graders']) >= 3
    has_entrypoint = 'entrypoint' in config and config['entrypoint'] == 'inference.py'
    
    print(f"  {'[OK]' if has_tasks else '[FAIL]'} Has 3+ tasks: {len(config.get('tasks', []))} tasks")
    print(f"  {'[OK]' if has_graders else '[FAIL]'} Has 3+ graders: {len(config.get('graders', []))} graders")
    print(f"  {'[OK]' if has_entrypoint else '[FAIL]'} Entrypoint is inference.py")
    
    yaml_valid = has_tasks and has_graders and has_entrypoint
except Exception as e:
    print(f"  ✗ Error parsing openenv.yaml: {e}")
    yaml_valid = False

# Check 4: Graders can be imported
print("\n[4] Checking graders...")
try:
    from graders import EasyGrader, MediumGrader, HardGrader
    from tasks import EASY_SCENARIOS, MEDIUM_SCENARIOS, HARD_SCENARIOS
    
    print(f"  [OK] EasyGrader imported")
    print(f"  [OK] MediumGrader imported")
    print(f"  [OK] HardGrader imported")
    print(f"  [OK] EASY_SCENARIOS: {len(EASY_SCENARIOS)} scenarios")
    print(f"  [OK] MEDIUM_SCENARIOS: {len(MEDIUM_SCENARIOS)} scenarios")
    print(f"  [OK] HARD_SCENARIOS: {len(HARD_SCENARIOS)} scenarios")
    
    graders_valid = True
except Exception as e:
    print(f"  ✗ Error importing graders: {e}")
    graders_valid = False

# Check 5: FastAPI app
print("\n[5] Checking FastAPI app...")
try:
    from inference import app
    
    routes = [route.path for route in app.routes]
    required_routes = ['/', '/health', '/reset', '/step', '/state', '/tasks', '/graders']
    
    all_routes_present = all(route in routes for route in required_routes)
    
    for route in required_routes:
        status = "[OK]" if route in routes else "[FAIL]"
        print(f"  {status} {route}")
    
    app_valid = all_routes_present
except Exception as e:
    print(f"  ✗ Error importing FastAPI app: {e}")
    app_valid = False

# Check 6: Grader scores
print("\n[6] Checking grader scores...")
try:
    from graders import EasyGrader, MediumGrader, HardGrader
    from tasks import EASY_SCENARIOS, MEDIUM_SCENARIOS, HARD_SCENARIOS
    from models.action import BugAction
    from models.scenario import BugScenario
    
    easy_grader = EasyGrader()
    medium_grader = MediumGrader()
    hard_grader = HardGrader()
    
    easy_scenario = BugScenario(**EASY_SCENARIOS[0])
    medium_scenario = BugScenario(**MEDIUM_SCENARIOS[0])
    hard_scenario = BugScenario(**HARD_SCENARIOS[0])
    
    test_action = BugAction(bug_type='null_pointer', file='auth.py', fix='Add null check')
    
    easy_score = easy_grader.grade(test_action, easy_scenario, 1)
    medium_score = medium_grader.grade(test_action, medium_scenario, 1)
    hard_score = hard_grader.grade(test_action, hard_scenario, 1)
    
    easy_valid = 0 < easy_score < 1
    medium_valid = 0 < medium_score < 1
    hard_valid = 0 < hard_score < 1
    
    print(f"  {'[OK]' if easy_valid else '[FAIL]'} Easy grader score: {easy_score:.2f} (valid: {easy_valid})")
    print(f"  {'[OK]' if medium_valid else '[FAIL]'} Medium grader score: {medium_score:.2f} (valid: {medium_valid})")
    print(f"  {'[OK]' if hard_valid else '[FAIL]'} Hard grader score: {hard_score:.2f} (valid: {hard_valid})")
    
    scores_valid = easy_valid and medium_valid and hard_valid
except Exception as e:
    print(f"  ✗ Error checking grader scores: {e}")
    scores_valid = False

# Check 7: Baseline agent
print("\n[7] Checking baseline agent...")
try:
    from baseline.baseline_agent import BaselineAgent
    
    agent = BaselineAgent(task='easy')
    result = agent.run_episode()
    
    has_reward = 'total_reward' in result
    has_steps = 'steps' in result and len(result['steps']) > 0
    has_success = 'success' in result
    
    print(f"  {'[OK]' if has_reward else '[FAIL]'} Episode has reward: {result.get('total_reward', 'N/A')}")
    print(f"  {'[OK]' if has_steps else '[FAIL]'} Episode has steps: {len(result.get('steps', []))} steps")
    print(f"  {'[OK]' if has_success else '[FAIL]'} Episode has success flag: {result.get('success', 'N/A')}")
    
    agent_valid = has_reward and has_steps and has_success
except Exception as e:
    print(f"  ✗ Error checking baseline agent: {e}")
    agent_valid = False

# Check 8: Dockerfile
print("\n[8] Checking Dockerfile...")
try:
    with open('Dockerfile', 'r') as f:
        dockerfile_content = f.read()
    
    has_python = 'python:3.10' in dockerfile_content
    has_workdir = 'WORKDIR /app' in dockerfile_content
    has_copy = 'COPY . /app' in dockerfile_content
    has_pip = 'pip install' in dockerfile_content
    has_expose = '7860' in dockerfile_content
    has_cmd = 'uvicorn' in dockerfile_content and 'inference:app' in dockerfile_content
    
    print(f"  {'[OK]' if has_python else '[FAIL]'} Python 3.10 base image")
    print(f"  {'[OK]' if has_workdir else '[FAIL]'} WORKDIR set to /app")
    print(f"  {'[OK]' if has_copy else '[FAIL]'} COPY command present")
    print(f"  {'[OK]' if has_pip else '[FAIL]'} pip install command present")
    print(f"  {'[OK]' if has_expose else '[FAIL]'} Port 7860 exposed")
    print(f"  {'[OK]' if has_cmd else '[FAIL]'} CMD with uvicorn and inference:app")
    
    dockerfile_valid = all([has_python, has_workdir, has_copy, has_pip, has_expose, has_cmd])
except Exception as e:
    print(f"  ✗ Error checking Dockerfile: {e}")
    dockerfile_valid = False

# Final summary
print("\n" + "=" * 70)
print("VERIFICATION SUMMARY")
print("=" * 70)

all_checks = [
    ("Required files", all_files_exist),
    ("Required directories", all_dirs_exist),
    ("openenv.yaml structure", yaml_valid),
    ("Graders", graders_valid),
    ("FastAPI app", app_valid),
    ("Grader scores", scores_valid),
    ("Baseline agent", agent_valid),
    ("Dockerfile", dockerfile_valid)
]

passed = sum(1 for _, result in all_checks if result)
total = len(all_checks)

for check_name, result in all_checks:
    status = "[PASS]" if result else "[FAIL]"
    print(f"{status}: {check_name}")

print("\n" + "=" * 70)
if passed == total:
    print(f"[PASS] ALL CHECKS PASSED ({passed}/{total})")
    print("Project is ready for submission!")
    print("=" * 70)
    sys.exit(0)
else:
    print(f"[FAIL] SOME CHECKS FAILED ({passed}/{total})")
    print("Please fix the issues above before submission.")
    print("=" * 70)
    sys.exit(1)
