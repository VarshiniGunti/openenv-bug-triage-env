"""Simulate Phase 2 remote validator checks."""
import requests, json, sys

base = "https://varshini28-openenv-bug-triage-env.hf.space"
passed = 0
failed = 0

def ok(msg): 
    global passed; passed += 1; print(f"  [PASS] {msg}")

def fail(msg): 
    global failed; failed += 1; print(f"  [FAIL] {msg}")

print("\n=== Phase 2 Simulation ===\n")

# 1. Health
r = requests.get(f"{base}/health", timeout=15)
if r.status_code == 200 and r.json().get("status") == "healthy":
    ok("health")
else:
    fail(f"health: {r.status_code} {r.text[:100]}")

# 2. /tasks returns 3+ tasks with graders
r = requests.get(f"{base}/tasks", timeout=15)
tasks = r.json() if r.status_code == 200 else []
tasks_with_graders = [t for t in tasks if t.get("grader") or t.get("grader_class")]
if len(tasks_with_graders) >= 3:
    ok(f"/tasks: {len(tasks_with_graders)} tasks with graders")
    for t in tasks_with_graders:
        print(f"       - {t['id']}: {t.get('grader')}")
else:
    fail(f"/tasks: only {len(tasks_with_graders)} tasks with graders (need 3+)")

# 3. Graders instantiable from class paths
import importlib
for t in tasks_with_graders:
    path = t.get("grader") or t.get("grader_class", "")
    try:
        mod, cls = path.rsplit(".", 1)
        grader = getattr(importlib.import_module(mod), cls)()
        ok(f"grader instantiable: {path}")
    except Exception as e:
        fail(f"grader not instantiable: {path} -> {e}")

# 4. Reset + step for each task, check score strictly (0,1)
for task_name in ["easy", "medium", "hard"]:
    r = requests.post(f"{base}/reset", json={"task": task_name}, timeout=15)
    if r.status_code != 200:
        fail(f"reset({task_name}): {r.status_code}")
        continue
    r2 = requests.post(f"{base}/step", 
        json={"action": {"bug_type": "logic", "file": "main.py", "fix": "fix the issue now"}},
        timeout=15)
    reward = r2.json().get("reward", -1)
    if 0 < reward < 1:
        ok(f"step({task_name}) reward={reward} strictly in (0,1)")
    else:
        fail(f"step({task_name}) reward={reward} OUT OF RANGE (must be strictly between 0 and 1)")

# 5. /metadata, /schema, /mcp
for endpoint, method in [("/metadata","GET"), ("/schema","GET"), ("/mcp","POST")]:
    r = requests.request(method, f"{base}{endpoint}", json={}, timeout=15)
    if r.status_code == 200:
        ok(f"{endpoint}: 200")
    else:
        fail(f"{endpoint}: {r.status_code}")

print(f"\n=== Results: {passed} passed, {failed} failed ===")
sys.exit(0 if failed == 0 else 1)
