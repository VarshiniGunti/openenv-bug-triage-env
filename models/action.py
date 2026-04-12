"""BugAction model for agent actions."""

from pydantic import BaseModel, Field, field_validator
from typing import List

# Controlled vocabulary for bug types
BUG_TYPES = [
    "memory",
    "logic",
    "authentication",
    "database",
    "performance",
    "null_pointer",
    "session",
    "race_condition"
]


class BugAction(BaseModel):
    """
    Represents an action taken by an agent in response to a bug observation.
    
    Attributes:
        bug_type: Classification of the bug (must be from controlled vocabulary)
        file: The file or module where the bug is located
        fix: Description of the proposed fix or solution
    """
    
    bug_type: str = Field(..., description="Type of bug from controlled vocabulary")
    file: str = Field(..., description="File or module where bug is located")
    fix: str = Field(..., description="Proposed fix or solution")
    
    @field_validator("bug_type")
    @classmethod
    def validate_bug_type(cls, v: str) -> str:
        """Validate that bug_type is non-empty."""
        if not v or not v.strip():
            raise ValueError("bug_type must be non-empty")
        return v
    
    @field_validator("file")
    @classmethod
    def validate_file(cls, v: str) -> str:
        """Validate that file is non-empty."""
        if not v or not v.strip():
            raise ValueError("file must be non-empty")
        return v
    
    @field_validator("fix")
    @classmethod
    def validate_fix(cls, v: str) -> str:
        """Validate that fix is non-empty."""
        if not v or not v.strip():
            raise ValueError("fix must be non-empty")
        return v
    
    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "bug_type": "null_pointer",
                "file": "user.py",
                "fix": "Add null check before accessing user profile"
            }
        }
