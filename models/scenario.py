"""BugScenario model for bug scenarios."""

from pydantic import BaseModel, Field, field_validator
from typing import List


class BugScenario(BaseModel):
    """
    Represents a complete bug scenario with ground truth information.
    
    Attributes:
        bug_report: Description of the bug
        ground_truth_type: Correct bug type classification
        ground_truth_file: Correct file location
        ground_truth_fix: Correct fix description
        repo_modules: List of repository modules/files
        difficulty: Difficulty level (easy, medium, hard)
        scenario_id: Unique identifier for the scenario
    """
    
    bug_report: str = Field(..., description="Description of the bug")
    ground_truth_type: str = Field(..., description="Correct bug type")
    ground_truth_file: str = Field(..., description="Correct file location")
    ground_truth_fix: str = Field(..., description="Correct fix description")
    repo_modules: List[str] = Field(..., description="List of repository modules")
    difficulty: str = Field(default="easy", description="Difficulty level: easy, medium, or hard")
    scenario_id: str = Field(default="", description="Unique scenario identifier")
    
    @field_validator("bug_report", "ground_truth_type", "ground_truth_file", "ground_truth_fix")
    @classmethod
    def validate_non_empty(cls, v: str) -> str:
        """Validate that string fields are non-empty."""
        if not v or not v.strip():
            raise ValueError("Field must be non-empty")
        return v
    
    @field_validator("repo_modules")
    @classmethod
    def validate_repo_modules(cls, v: List[str]) -> List[str]:
        """Validate that repo_modules contains at least one module."""
        if not v or len(v) == 0:
            raise ValueError("repo_modules must contain at least one module")
        return v
