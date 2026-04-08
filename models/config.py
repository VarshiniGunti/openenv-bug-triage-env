"""Configuration model for environment settings."""

from pydantic import BaseModel, Field, field_validator
from typing import Optional


class Config(BaseModel):
    """
    Configuration for the BugTriageEnv environment.
    
    Attributes:
        task: Task difficulty level (easy, medium, hard)
        max_steps: Maximum steps per episode (default: 3)
        seed: Random seed for reproducibility (optional)
    """
    
    task: str = Field(default="easy", description="Task difficulty: easy, medium, or hard")
    max_steps: int = Field(default=3, description="Maximum steps per episode")
    seed: Optional[int] = Field(default=None, description="Random seed for reproducibility")
    
    @field_validator("task")
    @classmethod
    def validate_task(cls, v: str) -> str:
        """Validate that task is one of the supported difficulties."""
        valid_tasks = ["easy", "medium", "hard"]
        if v not in valid_tasks:
            raise ValueError(f"task must be one of {valid_tasks}, got '{v}'")
        return v
    
    @field_validator("max_steps")
    @classmethod
    def validate_max_steps(cls, v: int) -> int:
        """Validate that max_steps is positive."""
        if v <= 0:
            raise ValueError("max_steps must be positive")
        return v
    
    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "task": "easy",
                "max_steps": 3,
                "seed": 42
            }
        }
