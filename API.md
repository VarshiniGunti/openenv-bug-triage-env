# API Documentation: OpenEnv Bug Triage Environment

## Overview

This document provides comprehensive API documentation for the OpenEnv Bug Triage Environment.

## Core Classes

### BugTriageEnv

The main environment class implementing the OpenEnv API.

```python
class BugTriageEnv:
    def __init__(self, config: Optional[Config] = None) -> None
    def reset(self) -> BugObservation
    def step(self, action: BugAction) -> Tuple[BugObservation, float, bool, Dict[str, Any]]
    def state(self) -> Dict[str, Any]
```

#### Methods

##### `__init__(config: Optional[Config] = None)`

Initialize the environment.

**Parameters:**
- `config` (Optional[Config]): Configuration object. Uses defaults if None.

**Example:**
```python
from bug_triage_env.env import BugTriageEnv
from bug_triage_env.models.config import Config

config = Config(task="easy", max_steps=3, seed=42)
env = BugTriageEnv(config)
```

##### `reset() -> BugObservation`

Reset the environment and start a new episode.

**Returns:**
- `BugObservation`: Initial observation for the new episode

**Example:**
```python
observation = env.reset()
print(f"Bug Report: {observation.bug_report}")
print(f"Modules: {observation.repo_modules}")
```

##### `step(action: BugAction) -> Tuple[BugObservation, float, bool, Dict[str, Any]]`

Execute one step of the environment.

**Parameters:**
- `action` (BugAction): The agent's action

**Returns:**
- `observation` (BugObservation): Observation for the next step
- `reward` (float): Reward for this step (0.0-1.0)
- `done` (bool): Whether the episode is finished
- `info` (Dict): Additional information

**Example:**
```python
from bug_triage_env.models.action import BugAction

action = BugAction(
    bug_type="null_pointer",
    file="auth.py",
    fix="Add null check before accessing credentials"
)

observation, reward, done, info = env.step(action)
print(f"Reward: {reward:.2f}, Done: {done}")
```

##### `state() -> Dict[str, Any]`

Get the current environment state without modifying it.

**Returns:**
- Dictionary with keys:
  - `task_name` (str): Current task difficulty
  - `scenario_id` (int): ID of current scenario
  - `step_count` (int): Current step number
  - `max_steps` (int): Maximum steps per episode
  - `previous_actions` (List[str]): Actions taken so far
  - `current_scenario` (Dict): Current scenario details

**Example:**
```python
state = env.state()
print(f"Task: {state['task_name']}")
print(f"Step: {state['step_count']}/{state['max_steps']}")
```

## Pydantic Models

### BugObservation

Represents the observation provided to an agent.

```python
class BugObservation(BaseModel):
    bug_report: str
    repo_modules: List[str]
    previous_actions: List[str] = []
```

**Fields:**
- `bug_report` (str): Textual description of the bug
- `repo_modules` (List[str]): List of repository modules/files
- `previous_actions` (List[str]): Previous actions in this episode

**Validation:**
- `bug_report` must be non-empty
- `repo_modules` must contain at least one module

**Example:**
```python
from bug_triage_env.models.observation import BugObservation

obs = BugObservation(
    bug_report="NullPointerException when accessing user profile",
    repo_modules=["auth.py", "user.py", "database.py"],
    previous_actions=[]
)
```

### BugAction

Represents an action taken by an agent.

```python
class BugAction(BaseModel):
    bug_type: str
    file: str
    fix: str
```

**Fields:**
- `bug_type` (str): Classification of the bug (must be from controlled vocabulary)
- `file` (str): File or module where bug is located
- `fix` (str): Description of the proposed fix

**Validation:**
- `bug_type` must be one of: memory, logic, authentication, database, performance, null_pointer, session, race_condition
- `file` must be non-empty
- `fix` must be non-empty

**Example:**
```python
from bug_triage_env.models.action import BugAction

action = BugAction(
    bug_type="memory",
    file="cache.py",
    fix="Implement proper cache eviction policy"
)
```

### BugScenario

Represents a complete bug scenario with ground truth.

```python
class BugScenario(BaseModel):
    bug_report: str
    ground_truth_type: str
    ground_truth_file: str
    ground_truth_fix: str
    repo_modules: List[str]
```

**Fields:**
- `bug_report` (str): Description of the bug
- `ground_truth_type` (str): Correct bug type
- `ground_truth_file` (str): Correct file location
- `ground_truth_fix` (str): Correct fix description
- `repo_modules` (List[str]): List of repository modules

### Config

Configuration for the environment.

```python
class Config(BaseModel):
    task: str = "easy"
    max_steps: int = 3
    seed: Optional[int] = None
```

**Fields:**
- `task` (str): Task difficulty (easy, medium, hard)
- `max_steps` (int): Maximum steps per episode
- `seed` (Optional[int]): Random seed for reproducibility

**Example:**
```python
from bug_triage_env.models.config import Config

config = Config(task="hard", max_steps=3, seed=42)
```

## Graders

### EasyGrader

Evaluates only the bug type in step 1.

```python
class EasyGrader:
    def grade(self, action: BugAction, scenario: BugScenario, step: int) -> float
```

**Reward:**
- Step 1: 0.3 if bug_type matches, 0.0 otherwise
- Steps 2-3: 0.0

### MediumGrader

Evaluates bug type and file location.

```python
class MediumGrader:
    def grade(self, action: BugAction, scenario: BugScenario, step: int) -> float
```

**Reward:**
- Step 1: 0.3 if bug_type matches, 0.0 otherwise
- Step 2: 0.3 if file matches, 0.0 otherwise
- Step 3: 0.0

### HardGrader

Evaluates bug type, file, and fix with keyword matching.

```python
class HardGrader:
    def grade(self, action: BugAction, scenario: BugScenario, step: int) -> float
    def extract_keywords(self, text: str) -> set
    def keyword_match(self, action_fix: str, ground_truth_fix: str) -> bool
```

**Reward:**
- Step 1: 0.3 if bug_type matches, 0.0 otherwise
- Step 2: 0.3 if file matches, 0.0 otherwise
- Step 3: 0.4 if keywords match, 0.0 otherwise

**Keyword Matching:**
- Extracts meaningful keywords from ground truth fix
- Removes common stopwords
- Case-insensitive matching
- Requires at least one keyword to match

## Configuration Management

### ConfigManager

Manages environment configuration from openenv.yaml.

```python
class ConfigManager:
    @staticmethod
    def load_config(config_path: Optional[str] = None) -> Config
    @staticmethod
    def get_default_config() -> Config
    @staticmethod
    def save_config(config: Config, config_path: Optional[str] = None) -> None
```

**Example:**
```python
from bug_triage_env.config_manager import ConfigManager

# Load configuration
config = ConfigManager.load_config("openenv.yaml")

# Get default configuration
default_config = ConfigManager.get_default_config()

# Save configuration
ConfigManager.save_config(config, "custom_config.yaml")
```

## Logging

### setup_logging

Configure logging with file and console handlers.

```python
def setup_logging(log_dir: str = "logs") -> logging.Logger
```

**Example:**
```python
from bug_triage_env.logging_config import setup_logging

logger = setup_logging("logs")
logger.info("Environment initialized")
```

## Task Datasets

### Easy Task

```python
from bug_triage_env.tasks import EASY_SCENARIOS

# EASY_SCENARIOS is a list of 9+ dictionaries
for scenario in EASY_SCENARIOS:
    print(scenario["bug_report"])
    print(scenario["ground_truth_type"])
```

### Medium Task

```python
from bug_triage_env.tasks import MEDIUM_SCENARIOS

# MEDIUM_SCENARIOS is a list of 9+ dictionaries
for scenario in MEDIUM_SCENARIOS:
    print(scenario["bug_report"])
```

### Hard Task

```python
from bug_triage_env.tasks import HARD_SCENARIOS

# HARD_SCENARIOS is a list of 9+ dictionaries
for scenario in HARD_SCENARIOS:
    print(scenario["bug_report"])
```

## Inference Script

### Running Inference

```bash
python -m bug_triage_env.scripts.inference --task easy --model gpt-3.5-turbo
```

**Arguments:**
- `--task`: Task difficulty (easy, medium, hard)
- `--model`: OpenAI model name
- `--api-key`: OpenAI API key (or set OPENAI_API_KEY env var)
- `--api-base-url`: OpenAI API base URL
- `--seed`: Random seed for reproducibility
- `--episodes`: Number of episodes to run

**Output Format:**
```
[START] task=easy env=bug_triage_env model=gpt-3.5-turbo
[STEP] step=1 action=bug_type=null_pointer, file=auth.py reward=0.30 done=false error=null
[STEP] step=2 action=bug_type=null_pointer, file=auth.py reward=0.00 done=false error=null
[STEP] step=3 action=bug_type=null_pointer, file=auth.py reward=0.00 done=true error=null
[END] success=true steps=3 score=0.30 rewards=0.30,0.00,0.00
```

## Complete Example

```python
from bug_triage_env.env import BugTriageEnv
from bug_triage_env.models.config import Config
from bug_triage_env.models.action import BugAction
from bug_triage_env.logging_config import setup_logging

# Setup logging
setup_logging()

# Create environment
config = Config(task="medium", max_steps=3, seed=42)
env = BugTriageEnv(config)

# Run episode
observation = env.reset()
print(f"Bug: {observation.bug_report}")

total_reward = 0
for step in range(3):
    action = BugAction(
        bug_type="null_pointer",
        file="auth.py",
        fix="Add null check"
    )
    
    observation, reward, done, info = env.step(action)
    total_reward += reward
    
    print(f"Step {step+1}: Reward={reward:.2f}, Done={done}")
    
    if done:
        break

print(f"Total Reward: {total_reward:.2f}")
print(f"State: {env.state()}")
```

## Error Handling

The environment raises descriptive errors for invalid inputs:

```python
from pydantic import ValidationError

try:
    action = BugAction(
        bug_type="invalid_type",  # Not in vocabulary
        file="test.py",
        fix="test"
    )
except ValidationError as e:
    print(f"Invalid action: {e}")

try:
    env = BugTriageEnv()
    env.step(action)  # Without calling reset first
except RuntimeError as e:
    print(f"Environment error: {e}")
```

## Performance Characteristics

- `reset()`: < 100ms
- `step()`: < 50ms
- Supports 1000+ episodes without memory leaks
- Deterministic with seeding

## Type Hints

All functions and methods have complete type hints for IDE support and type checking:

```python
from typing import Tuple, Dict, Any, Optional, List

def step(self, action: BugAction) -> Tuple[BugObservation, float, bool, Dict[str, Any]]:
    ...
```
