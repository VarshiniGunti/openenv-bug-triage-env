#!/usr/bin/env python
"""Comprehensive verification script for OpenEnv Bug Triage Environment submission."""

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
        
        return self.generate_report()


if __name__ == "__main__":
    verifier = SubmissionVerifier()
    exit_code = verifier.run_all_checks()
    sys.exit(exit_code)
