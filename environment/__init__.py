"""OpenEnv Bug Triage Environment package."""

def __getattr__(name):
    if name == "BugTriageEnv":
        from environment.env import BugTriageEnv
        return BugTriageEnv
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

__all__ = ["BugTriageEnv"]
