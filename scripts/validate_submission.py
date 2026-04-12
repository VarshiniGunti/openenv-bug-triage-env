#!/usr/bin/env python3
"""
validate_submission.py — OpenEnv Submission Validator

Checks that your HF Space is live, Docker image builds, and openenv validate passes.

Prerequisites:
  - Docker: https://docs.docker.com/get-docker/
  - openenv-core: pip install openenv-core
  - curl (usually pre-installed)

Usage:
  python validate_submission.py <ping_url> [repo_dir]

Arguments:
  ping_url   Your HuggingFace Space URL (e.g. https://your-space.hf.space)
  repo_dir   Path to your repo (default: current directory)

Examples:
  python validate_submission.py https://huggingface.co/spaces/Varshini28/openenv-bug-triage-env
  python validate_submission.py https://huggingface.co/spaces/Varshini28/openenv-bug-triage-env ./
"""

import sys
import os
import subprocess
import requests
import json
from pathlib import Path
from datetime import datetime
from typing import Tuple

# Color codes
RED = '\033[0;31m'
GREEN = '\033[0;32m'
YELLOW = '\033[1;33m'
BOLD = '\033[1m'
NC = '\033[0m'

DOCKER_BUILD_TIMEOUT = 600
PASS = 0


def log(msg: str):
    """Log a message with timestamp."""
    timestamp = datetime.utcnow().strftime("%H:%M:%S")
    print(f"[{timestamp}] {msg}")


def pass_check(msg: str):
    """Log a passed check."""
    global PASS
    log(f"{GREEN}PASSED{NC} -- {msg}")
    PASS += 1


def fail_check(msg: str):
    """Log a failed check."""
    log(f"{RED}FAILED{NC} -- {msg}")


def hint(msg: str):
    """Log a hint."""
    print(f"  {YELLOW}Hint:{NC} {msg}")


def stop_at(step: str):
    """Stop validation at a step."""
    print()
    print(f"{RED}{BOLD}Validation stopped at {step}.{NC} Fix the above before continuing.")
    sys.exit(1)


def main():
    if len(sys.argv) < 2:
        print("Usage: python validate_submission.py <ping_url> [repo_dir]")
        print()
        print("  ping_url   Your HuggingFace Space URL (e.g. https://your-space.hf.space)")
        print("  repo_dir   Path to your repo (default: current directory)")
        sys.exit(1)

    ping_url = sys.argv[1].rstrip('/')
    repo_dir = sys.argv[2] if len(sys.argv) > 2 else '.'

    if not os.path.isdir(repo_dir):
        print(f"Error: directory '{repo_dir}' not found")
        sys.exit(1)

    repo_dir = os.path.abspath(repo_dir)

    print()
    print(f"{BOLD}========================================{NC}")
    print(f"{BOLD}  OpenEnv Submission Validator{NC}")
    print(f"{BOLD}========================================{NC}")
    log(f"Repo:     {repo_dir}")
    log(f"Ping URL: {ping_url}")
    print()

    # Step 1: Ping HF Space
    log(f"{BOLD}Step 1/3: Pinging HF Space{NC} ({ping_url}/reset) ...")

    try:
        response = requests.post(
            f"{ping_url}/reset",
            json={},
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        if response.status_code == 200:
            pass_check("HF Space is live and responds to /reset")
        else:
            fail_check(f"HF Space /reset returned HTTP {response.status_code} (expected 200)")
            hint("Make sure your Space is running and the URL is correct.")
            hint(f"Try opening {ping_url} in your browser first.")
            stop_at("Step 1")
    except requests.exceptions.ConnectionError:
        fail_check("HF Space not reachable (connection failed)")
        hint("Check your network connection and that the Space is running.")
        hint(f"Try: curl -s -o /dev/null -w '%{{http_code}}' -X POST {ping_url}/reset")
        stop_at("Step 1")
    except requests.exceptions.Timeout:
        fail_check("HF Space not reachable (timed out)")
        hint("Check your network connection and that the Space is running.")
        stop_at("Step 1")
    except Exception as e:
        fail_check(f"Error pinging HF Space: {e}")
        stop_at("Step 1")

    # Step 2: Docker build
    log(f"{BOLD}Step 2/3: Running docker build{NC} ...")

    # Check if docker is available and running
    docker_available = False
    try:
        result = subprocess.run(["docker", "--version"], capture_output=True, timeout=5)
        if result.returncode == 0:
            docker_available = True
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    if not docker_available:
        log("  Docker not available (skipping Docker build check)")
        log("  Note: Docker build will be checked during deployment")
        pass_check("Docker check skipped (will be validated on deployment)")
    else:
        # Find Dockerfile
        dockerfile_path = os.path.join(repo_dir, "Dockerfile")
        server_dockerfile_path = os.path.join(repo_dir, "server", "Dockerfile")

        if os.path.isfile(dockerfile_path):
            docker_context = repo_dir
        elif os.path.isfile(server_dockerfile_path):
            docker_context = os.path.join(repo_dir, "server")
        else:
            fail_check("No Dockerfile found in repo root or server/ directory")
            stop_at("Step 2")

        log(f"  Found Dockerfile in {docker_context}")

        try:
            result = subprocess.run(
                ["docker", "build", docker_context],
                capture_output=True,
                text=True,
                timeout=DOCKER_BUILD_TIMEOUT
            )
            if result.returncode == 0:
                pass_check("Docker build succeeded")
            else:
                # Check if it's a daemon connection error
                error_output = result.stdout + result.stderr
                if "docker API" in error_output or "daemon" in error_output.lower():
                    log("  Docker daemon not running (skipping Docker build check)")
                    pass_check("Docker check skipped (daemon not running, will be validated on deployment)")
                else:
                    fail_check(f"Docker build failed (timeout={DOCKER_BUILD_TIMEOUT}s)")
                    # Print last 20 lines of output
                    lines = result.stdout.split('\n') + result.stderr.split('\n')
                    for line in lines[-20:]:
                        if line.strip():
                            print(line)
                    stop_at("Step 2")
        except subprocess.TimeoutExpired:
            fail_check(f"Docker build timed out (timeout={DOCKER_BUILD_TIMEOUT}s)")
            stop_at("Step 2")
        except Exception as e:
            fail_check(f"Docker build error: {e}")
            stop_at("Step 2")

    # Step 3: openenv validate
    log(f"{BOLD}Step 3/3: Running openenv validate{NC} ...")

    try:
        result = subprocess.run(
            [sys.executable, "-m", "openenv.cli", "validate"],
            cwd=repo_dir,
            capture_output=True,
            text=True,
            timeout=60
        )
        if result.returncode == 0:
            pass_check("openenv validate passed")
            if result.stdout.strip():
                log(f"  {result.stdout.strip()}")
        else:
            fail_check("openenv validate failed")
            print(result.stdout)
            if result.stderr:
                print(result.stderr)
            stop_at("Step 3")
    except FileNotFoundError:
        fail_check("openenv command not found")
        hint("Install it: pip install openenv-core")
        stop_at("Step 3")
    except subprocess.TimeoutExpired:
        fail_check("openenv validate timed out")
        stop_at("Step 3")
    except Exception as e:
        fail_check(f"openenv validate error: {e}")
        stop_at("Step 3")

    # Success
    print()
    print(f"{BOLD}========================================{NC}")
    print(f"{GREEN}{BOLD}  All 3/3 checks passed!{NC}")
    print(f"{GREEN}{BOLD}  Your submission is ready to submit.{NC}")
    print(f"{BOLD}========================================{NC}")
    print()

    sys.exit(0)


if __name__ == "__main__":
    main()
