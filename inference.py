"""
OpenEnv Bug Triage - Inference Script

This file serves dual purpose:
1. When imported by uvicorn: exposes the FastAPI `app` from server.app
2. When run directly: runs the inference loop with [START]/[STEP]/[END] output
"""

import os
import sys

# Read environment variables with defaults where required
API_BASE_URL = os.getenv("API_BASE_URL", "https://api.openai.com/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4.1-mini")
HF_TOKEN = os.getenv("HF_TOKEN")

# Re-export the FastAPI app for uvicorn (uvicorn inference:app)
from server.app import app  # noqa: F401, E402

if __name__ == "__main__":
    from openai import OpenAI
    from models.config import Config
    from models.action import BugAction
    from environment.env import BugTriageEnv
    from typing import Optional
    import argparse

    if HF_TOKEN is None:
        raise ValueError("HF_TOKEN environment variable is required")

    client = OpenAI(base_url=API_BASE_URL, api_key=HF_TOKEN)

    parser = argparse.ArgumentParser()
    parser.add_argument("--task", default="easy", choices=["easy", "medium", "hard"])
    parser.add_argument("--episodes", type=int, default=1)
    parser.add_argument("--seed", type=int, default=None)
    args = parser.parse_args()

    def log_start(task, env, model):
        print(f"[START] task={task} env={env} model={model}", flush=True)

    def log_step(step, action, reward, done, error):
        done_str = str(done).lower()
        error_str = error if error else "null"
        print(f"[STEP] step={step} action={action} reward={reward:.2f} done={done_str} error={error_str}", flush=True)

    def log_end(success, steps, rewards):
        rewards_str = ",".join(f"{r:.2f}" for r in rewards)
        print(f"[END] success={str(success).lower()} steps={steps} rewards={rewards_str}", flush=True)

    log_start(task=args.task, env="openenv-bug-triage-env", model=MODEL_NAME)

    all_rewards = []
    try:
        config = Config(task=args.task, max_steps=3, seed=args.seed)
        env = BugTriageEnv(config)
        obs = env.reset()
        bug_report = obs.bug_report if hasattr(obs, "bug_report") else str(obs)

        for step_num in range(1, 4):
            action = None
            try:
                response = client.chat.completions.create(
                    model=MODEL_NAME,
                    messages=[
                        {"role": "system", "content": "You are a bug triage expert. Respond with: bug_type: <type>\nfile: <file>\nfix: <description>"},
                        {"role": "user", "content": f"Bug report: {bug_report}\nStep {step_num}: classify and fix."},
                    ],
                    max_tokens=150,
                    temperature=0.3,
                )
                text = response.choices[0].message.content or ""
                parsed: dict = {}
                for line in text.strip().splitlines():
                    if ":" in line:
                        k, _, v = line.partition(":")
                        parsed[k.strip().lower()] = v.strip()
                if all(k in parsed for k in ("bug_type", "file", "fix")):
                    action = BugAction(
                        bug_type=parsed["bug_type"],
                        file=parsed["file"],
                        fix=parsed["fix"],
                    )
            except Exception:
                pass

            if action is None:
                action = BugAction(bug_type="logic", file="main.py", fix="Apply a fix to resolve the issue")

            obs, reward, done, info = env.step(action)
            all_rewards.append(reward)
            log_step(step=step_num, action=f"{action.bug_type}", reward=reward, done=done, error=None)
            if done:
                break

        success = any(r > 0.1 for r in all_rewards)
        log_end(success=success, steps=len(all_rewards), rewards=all_rewards)

    except Exception as e:
        log_end(success=False, steps=len(all_rewards), rewards=all_rewards)
        sys.exit(1)
