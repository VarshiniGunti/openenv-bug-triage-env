"""BugAction model for agent actions."""

from pydantic import Field
from openenv.core.env_server.types import Action

# Controlled vocabulary for bug types
BUG_TYPES = [
    "memory", "logic", "authentication", "database",
    "performance", "null_pointer", "session", "race_condition"
]


class BugAction(Action):
    """
    Action for the Bug Triage environment.
    Extends openenv-core Action base class.
    """

    bug_type: str = Field(default="logic", description="Type of bug from controlled vocabulary")
    file: str = Field(default="main.py", description="File or module where bug is located")
    fix: str = Field(default="Apply a fix to resolve the issue", description="Proposed fix or solution")
