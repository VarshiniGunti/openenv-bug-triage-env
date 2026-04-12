"""BugObservation model for environment observations."""

from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .action import BugAction


class BugObservation(BaseModel):
    """
    Represents the observation provided to an agent at each step.
    """
    
    bug_report: str = Field(..., description="Textual description of the bug")
    repo_modules: List[str] = Field(..., description="List of repository modules/files")
    previous_actions: List[str] = Field(default_factory=list, description="Previous actions in episode")
    triage_hint: str = Field(
        default="Bug triage workflow: Classify bug type from vocabulary. Identify most likely affected module. Propose a short fix description.",
        description="Guidance on bug triage workflow"
    )
    module_descriptions: dict = Field(
        default_factory=dict,
        description="Descriptions of module purposes (module_name -> description)"
    )
    last_action: Optional[dict] = Field(
        default=None,
        description="The most recent action taken by the agent (echoed for reasoning consistency)"
    )
    # Required by openenv-core serialization
    reward: float = Field(default=0.0, description="Reward from the last step")
    done: bool = Field(default=False, description="Whether the episode is done")
    
    @field_validator("bug_report")
    @classmethod
    def validate_bug_report(cls, v: str) -> str:
        """Validate that bug_report is non-empty."""
        if not v or not v.strip():
            raise ValueError("bug_report must be non-empty")
        return v
    
    @field_validator("repo_modules")
    @classmethod
    def validate_repo_modules(cls, v: List[str]) -> List[str]:
        """Validate that repo_modules contains at least one module."""
        if not v or len(v) == 0:
            raise ValueError("repo_modules must contain at least one module")
        return v
    
    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "bug_report": "NullPointerException when accessing user profile",
                "repo_modules": ["auth.py", "user.py", "database.py"],
                "previous_actions": [],
                "triage_hint": "Bug triage workflow: Classify bug type from vocabulary. Identify most likely affected module. Propose a short fix description.",
                "module_descriptions": {
                    "auth.py": "Handles user authentication and session management",
                    "user.py": "Manages user profile data and operations",
                    "database.py": "Provides database connection and query utilities"
                },
                "last_action": {
                    "bug_type": "null_pointer",
                    "file": "user.py",
                    "fix": "Add null check before accessing user profile"
                }
            }
        }
