#!/usr/bin/env python
"""
Comprehensive verification script for OpenEnv Bug Triage Environment submission.

This script validates:
1. Project structure
2. OpenEnv API compliance
3. Environment variables
4. Logging format
5. Docker build
6. Inference script execution
"""

import os
import sys
import subprocess
import json
from pathlib import Path
from datetime import datetime


class SubmissionVerifier:
    """Verifies OpenEnv submission readiness."""
    
    def __init__(self):
        """Initialize verifier."""
        self.results = {}
        self.passed = 0
        self.failed = 0
        self.workspace_root = Path(__file__).parent
        self.bug_triage_env = self.workspace_root / "bug_triage_env"
    
    def log(self, message: str, level: str = "INFO"):
        """Log a message."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
    
    def check(self, name: str, condition: bool, details: str = ""):
        """Record a check result."""
        status = "✅ PASS" if condition else "❌ FAIL"
        self.results[name] = condition
        self.log(f"{status} - {name}", "CHECK")
        if details:
            self.log(f"  Details: {details}", "INFO")
        if condition:
            self.passed += 1
        else:
            self.failed += 1
        return condition
    
    def verify_project_structure(self):
        """Verify required project files exist."""
        self.log("=" * 60, "INFO")
        self.log("STEP 1: Verifying Project Structure", "INFO")
        self.log("=" * 60, "INFO")
        
        required_files = [
            "bug_triage_env/env.py",
            "bug_triage_env/inference.py",
            "bug_triage_env/requirements.txt",
            "bug_triage_env/Dockerfile",
            "bug_triage_env/README.md",
            "bug_triage_env/openenv.yaml",
        ]
        
        for file_path in required_files:
            full_path = self.workspace_root / file_path
            exists = full_path.exists()
            self.check(f"File exists: {file_path}", exists)
        
        # Check inference.py location
        inference_path = self.bug_triage_env / "inference.py"
        self.check("inference.py at bug_triage_env root", inference_path.exists())
    
    def verify_openenv_api(self):
        """Verify OpenEnv API compliance."""
        self.log("=" * 60, "INFO")
        self.log("STEP 2: Verifying OpenEnv API Compliance", "INFO")
        self.log("=" * 60, "INFO")
        
        try:
            # Import environment
            sys.path.insert(0, str(self.bug_triage_env))
            from env import BugTriageEnv
            from models.config import Config
            
            # Check reset() method
            env = BugTriageEnv(Config(task="easy", max_steps=3))
            obs = env.reset()
            self.check("reset() method exists and returns observation", obs is not None)
            
            # Check step() method
            from models.action import BugAction
            action = BugAction(
                bug_type="null_pointer",
                file="auth.py",
                fix="Add null check before accessing"
            )
            obs, reward, done, info = env.step(action)
            self.check("step() method exists and returns (obs, reward, done, info)", 
                      obs is not None and isinstance(reward, float) and isinstance(done, bool))
            
            # Check state() method
            state = env.state()
            self.check("state() method exists and returns dict", isinstance(state, dict))
            
            # Check HTTP endpoints
            from env import OpenEnvServer
            self.check("OpenEnvServer class exists", OpenEnvServer is not None)
            
        except Exception as e:
            self.check("OpenEnv API compliance", False, str(e))
    
    def verify_environment_variables(self):
        """Verify environment variable usage."""
        self.log("=" * 60, "INFO")
        self.log("STEP 3: Verifying Environment Variables", "INFO")
        self.log("=" * 60, "INFO")
        
        inference_file = self.bug_triage_env / "inference.py"
        content = inference_file.read_text()
        
        # Check for required variables
        has_api_base_url = "API_BASE_URL" in content
        has_model_name = "MODEL_NAME" in content
        has_hf_token = "HF_TOKEN" in content
        has_openai_key = "OPENAI_API_KEY" in content
        
        self.check("Uses API_BASE_URL environment variable", has_api_base_url)
        self.check("Uses MODEL_NAME environment variable", has_model_name)
        self.check("Uses HF_TOKEN environment variable", has_hf_token)
        self.check("Does NOT use OPENAI_API_KEY", not has_openai_key, 
                  "OPENAI_API_KEY should not be used")
    
    def verify_logging_format(self):
        """Verify logging format."""
        self.log("=" * 60, "INFO")
        self.log("STEP 4: Verifying Logging Format", "INFO")
        self.log("=" * 60, "INFO")
        
        inference_file = self.bug_triage_env / "inference.py"
        content = inference_file.read_text()
        
        # Check for logging format
        has_start = "[START]" in content
        has_step = "[STEP]" in content
        has_end = "[END]" in content
        
        self.check("Uses [START] logging format", has_start)
        self.check("Uses [STEP] logging format", has_step)
        self.check("Uses [END] logging format", has_end)
        
        # Check for required fields
        has_task = "task=" in content
        has_action = "action=" in content
        has_reward = "reward=" in content
        has_done = "done=" in content
        has_error = "error=" in content
        
        self.check("Logs include 'task' field", has_task)
        self.check("Logs include 'action' field", has_action)
        self.check("Logs include 'reward' field", has_reward)
        self.check("Logs include 'done' field", has_done)
        self.check("Logs include 'error' field", has_error)
    
    def verify_dockerfile(self):
        """Verify Dockerfile configuration."""
        self.log("=" * 60, "INFO")
        self.log("STEP 5: Verifying Dockerfile", "INFO")
        self.log("=" * 60, "INFO")
        
        dockerfile = self.bug_triage_env / "Dockerfile"
        content = dockerfile.read_text()
        
        # Check for required elements
        has_python = "python" in content.lower()
        has_requirements = "requirements.txt" in content
        has_copy = "COPY" in content
        has_expose = "EXPOSE" in content or "5000" in content
        has_cmd = "CMD" in content
        
        self.check("Dockerfile uses Python base image", has_python)
        self.check("Dockerfile installs requirements", has_requirements)
        self.check("Dockerfile copies project files", has_copy)
        self.check("Dockerfile exposes port 5000", has_expose)
        self.check("Dockerfile has CMD entrypoint", has_cmd)
    
    def verify_docker_build(self):
        """Verify Docker build works."""
        self.log("=" * 60, "INFO")
        self.log("STEP 6: Verifying Docker Build", "INFO")
        self.log("=" * 60, "INFO")
        
        try:
            # Check if Docker is available
            result = subprocess.run(
                ["docker", "--version"],
                capture_output=True,
                timeout=10
            )
            docker_available = result.returncode == 0
            self.check("Docker is installed", docker_available)
            
            if docker_available:
                self.log("Building Docker image (this may take a minute)...", "INFO")
                result = subprocess.run(
                    ["docker", "build", "-t", "bug-triage-env:test", "."],
                    cwd=str(self.bug_triage_env),
                    capture_output=True,
                    timeout=300
                )
                build_success = result.returncode == 0
                self.check("Docker build succeeds", build_success,
                          f"Return code: {result.returncode}")
                
                if not build_success:
                    self.log(f"Build stderr: {result.stderr.decode()}", "ERROR")
        
        except subprocess.TimeoutExpired:
            self.check("Docker build completes in time", False, "Build timed out")
        except Exception as e:
            self.check("Docker build verification", False, str(e))
    
    def verify_pytest(self):
        """Verify pytest runs successfully."""
        self.log("=" * 60, "INFO")
        self.log("STEP 7: Verifying Tests", "INFO")
        self.log("=" * 60, "INFO")
        
        try:
            result = subprocess.run(
                ["python", "-m", "pytest", "bug_triage_env/tests/", "-q"],
                cwd=str(self.workspace_root),
                capture_output=True,
                timeout=60
            )
            tests_pass = result.returncode == 0
            self.check("All tests pass", tests_pass,
                      f"Return code: {result.returncode}")
            
            # Extract test count
            output = result.stdout.decode()
            if "passed" in output:
                self.log(f"Test output: {output.split('=')[-1].strip()}", "INFO")
        
        except subprocess.TimeoutExpired:
            self.check("Tests complete in time", False, "Tests timed out")
        except Exception as e:
            self.check("Test verification", False, str(e))
    
    def verify_inference_script(self):
        """Verify inference script can run."""
        self.log("=" * 60, "INFO")
        self.log("STEP 8: Verifying Inference Script", "INFO")
        self.log("=" * 60, "INFO")
        
        try:
            # Set required environment variables
            env_vars = os.environ.copy()
            env_vars["API_BASE_URL"] = "https://api.openai.com/v1"
            env_vars["MODEL_NAME"] = "gpt-3.5-turbo"
            env_vars["HF_TOKEN"] = "test-token"
            
            # Run inference script with --help to verify it works
            result = subprocess.run(
                ["python", "inference.py", "--help"],
                cwd=str(self.bug_triage_env),
                capture_output=True,
                timeout=10,
                env=env_vars
            )
            help_works = result.returncode == 0
            self.check("Inference script --help works", help_works)
            
            # Check that script accepts required arguments
            output = result.stdout.decode()
            has_task_arg = "--task" in output
            has_episodes_arg = "--episodes" in output
            
            self.check("Inference script has --task argument", has_task_arg)
            self.check("Inference script has --episodes argument", has_episodes_arg)
        
        except subprocess.TimeoutExpired:
            self.check("Inference script responds quickly", False, "Script timed out")
        except Exception as e:
            self.check("Inference script verification", False, str(e))
    
    def verify_requirements(self):
        """Verify requirements.txt is valid."""
        self.log("=" * 60, "INFO")
        self.log("STEP 9: Verifying Requirements", "INFO")
        self.log("=" * 60, "INFO")
        
        try:
            requirements_file = self.bug_triage_env / "requirements.txt"
            content = requirements_file.read_text()
            
            # Check for key dependencies
            has_pydantic = "pydantic" in content.lower()
            has_flask = "flask" in content.lower()
            has_openai = "openai" in content.lower()
            has_scikit = "scikit" in content.lower()
            
            self.check("requirements.txt includes pydantic", has_pydantic)
            self.check("requirements.txt includes flask", has_flask)
            self.check("requirements.txt includes openai", has_openai)
            self.check("requirements.txt includes scikit-learn", has_scikit)
        
        except Exception as e:
            self.check("Requirements verification", False, str(e))
    
    def verify_readme(self):
        """Verify README documentation."""
        self.log("=" * 60, "INFO")
        self.log("STEP 10: Verifying Documentation", "INFO")
        self.log("=" * 60, "INFO")
        
        try:
            readme_file = self.bug_triage_env / "README.md"
            content = readme_file.read_text()
            
            # Check for key sections
            has_features = "Features" in content or "features" in content
            has_installation = "Installation" in content or "installation" in content
            has_quick_start = "Quick Start" in content or "quick start" in content
            has_api = "API" in content
            
            self.check("README has Features section", has_features)
            self.check("README has Installation section", has_installation)
            self.check("README has Quick Start section", has_quick_start)
            self.check("README has API documentation", has_api)
        
        except Exception as e:
            self.check("Documentation verification", False, str(e))
    
    def generate_report(self):
        """Generate final verification report."""
        self.log("=" * 60, "INFO")
        self.log("FINAL VERIFICATION REPORT", "INFO")
        self.log("=" * 60, "INFO")
        
        total = self.passed + self.failed
        percentage = (self.passed / total * 100) if total > 0 else 0
        
        self.log(f"Total Checks: {total}", "INFO")
        self.log(f"Passed: {self.passed} ✅", "INFO")
        self.log(f"Failed: {self.failed} ❌", "INFO")
        self.log(f"Success Rate: {percentage:.1f}%", "INFO")
        
        if self.failed == 0:
            self.log("=" * 60, "INFO")
            self.log("🎉 ALL CHECKS PASSED - READY FOR SUBMISSION 🎉", "INFO")
            self.log("=" * 60, "INFO")
            return 0
        else:
            self.log("=" * 60, "ERROR")
            self.log(f"⚠️  {self.failed} CHECK(S) FAILED - REVIEW REQUIRED", "ERROR")
            self.log("=" * 60, "ERROR")
            return 1
    
    def run_all_checks(self):
        """Run all verification checks."""
        self.log("Starting OpenEnv Submission Verification", "INFO")
        self.log(f"Workspace: {self.workspace_root}", "INFO")
        
        self.verify_project_structure()
        self.verify_openenv_api()
        self.verify_environment_variables()
        self.verify_logging_format()
        self.verify_dockerfile()
        self.verify_requirements()
        self.verify_readme()
        self.verify_pytest()
        self.verify_inference_script()
        self.verify_docker_build()
        
        return self.generate_report()


if __name__ == "__main__":
    verifier = SubmissionVerifier()
    exit_code = verifier.run_all_checks()
    sys.exit(exit_code)
