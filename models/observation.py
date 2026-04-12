"""BugObservation model for environment observations."""

from pydantic import Field
from typing import List, Optional
from openenv.core.env_server.types import Observation


class BugObservation(Observation):
    """
    Observation returned from the Bug Triage environment.
    Extends openenv-core Observation (which provides reward and done fields).
    """

    bug_report: str = Field(default="", description="Textual description of the bug")
    repo_modules: List[str] = Field(default_factory=list, description="List of repository modules/files")
    previous_actions: List[str] = Field(default_factory=list, description="Previous actions in episode")
    triage_hint: str = Field(
        default="Bug triage workflow: Classify bug type from vocabulary. Identify most likely affected module. Propose a short fix description.",
        description="Guidance on bug triage workflow"
    )
    module_descriptions: dict = Field(default_factory=dict)
    last_action: Optional[dict] = Field(default=None)
