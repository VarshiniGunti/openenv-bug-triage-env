---
title: openenv-bug-triage-env
emoji: �
colorFrom: blue
colorTo: indigo
sdk: docker
pinned: false
---

# OpenEnv Bug Triage Environment

[![Python](https://img.shields.io/badge/Python-3.10-blue)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green)](https://fastapi.tiangolo.com)
[![OpenEnv](https://img.shields.io/badge/OpenEnv-Compatible-purple)](https://github.com/meta-pytorch/OpenEnv)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue)](https://docker.com)
[![HF Space](https://img.shields.io/badge/HuggingFace-Running-yellow)](https://huggingface.co/spaces/Varshini28/openenv-bug-triage-env)

A production-ready **Reinforcement Learning environment** for training and evaluating AI agents on software bug triage tasks. Built for the **Meta × OpenEnv Hackathon** and deployed as a live HuggingFace Space.

Agents interact with realistic bug reports, classify issues, locate affected files, and propose fixes — receiving reward signals that guide learning across three progressive difficulty levels.

---

## Overview

Bug triage is a critical software engineering workflow. This environment simulates it as an RL problem:

- The agent receives a **bug report** and a list of **repository modules**
- Over **3 steps**, it must classify the bug type, identify the affected file, and propose a fix
- A **grader** evaluates each action and returns a reward strictly in **(0, 1)**
- 42 diverse scenarios across **Easy**, **Medium**, and **Hard** difficulty levels

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| API Framework | FastAPI + Uvicorn |
| RL Environment | openenv-core (Meta / HuggingFace) |
| LLM Integration | OpenAI Python SDK |
| Data Validation | Pydantic v2 |
| Semantic Grading | scikit-learn (TF-IDF cosine similarity) |
| Containerisation | Docker |
| Deployment | HuggingFace Spaces |
| Language | Python 3.10 |

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                   FastAPI Server                     │
│  /reset  /step  /state  /tasks  /grader  /metadata  │
│  /schema  /mcp  /health  /ws                        │
└──────────────┬──────────────────────────────────────┘
               │
       ┌───────▼────────┐
       │ BugTriageEnv   │  openenv-core Environment interface
       │  reset()       │
       │  step()        │
       └───────┬────────┘
               │
    ┌──────────▼──────────┐
    │   Graders           │
    │  EasyGrader         │  bug_type accuracy
    │  MediumGrader       │  bug_type + file accuracy
    │  HardGrader         │  bug_type + file + fix (TF-IDF)
    └──────────┬──────────┘
               │
    ┌──────────▼──────────┐
    │   42 Scenarios      │
    │  14 Easy            │
    │  14 Medium          │
    │  14 Hard            │
    └─────────────────────┘
```

---

## Task Design

### Easy — Bug Classification
- **Goal**: Identify the bug type from the report
- **Reward**: `0.35` correct · `0.05` incorrect
- **Scenarios**: 14 (3–5 modules each)

### Medium — Classification + Localisation
- **Goal**: Identify bug type AND the affected file
- **Reward**: `0.35` per correct field
- **Scenarios**: 14 (8–15 modules each)

### Hard — Full Triage
- **Goal**: Bug type + file + propose a fix
- **Reward**: `0.35` per field; fix scored via hybrid keyword + TF-IDF semantic similarity
- **Scenarios**: 14 (20–30 modules each)

### Bug Type Vocabulary (8 categories)
`memory` · `logic` · `authentication` · `database` · `performance` · `null_pointer` · `session` · `race_condition`

---

## API Reference

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/reset` | POST | Start a new episode |
| `/step` | POST | Submit an action, receive reward |
| `/state` | GET | Current episode state |
| `/tasks` | GET | List all tasks with grader paths |
| `/graders` | GET | List all graders |
| `/grader` | POST | Score an action without advancing episode |
| `/metadata` | GET | Environment metadata |
| `/schema` | GET | Action / observation / state schemas |
| `/mcp` | POST | JSON-RPC 2.0 endpoint |
| `/ws` | WS | WebSocket for persistent sessions |

### Reset
```bash
curl -X POST https://varshini28-openenv-bug-triage-env.hf.space/reset \
  -H "Content-Type: application/json" -d '{}'
```
```json
{
  "observation": {
    "bug_report": "Login fails for users with special characters in their password.",
    "repo_modules": ["auth.py", "validation.py", "security.py", "utils.py"]
  },
  "reward": 0.1,
  "done": false
}
```

### Step
```bash
curl -X POST https://varshini28-openenv-bug-triage-env.hf.space/step \
  -H "Content-Type: application/json" \
  -d '{"action": {"bug_type": "authentication", "file": "auth.py", "fix": "Add proper escaping for special characters"}}'
```
```json
{"reward": 0.35, "done": false, "observation": {...}}
```

---

## Project Structure

```
openenv-bug-triage-env/
├── inference.py              # Entry point — re-exports app + standalone inference loop
├── Dockerfile                # Container definition (port 7860)
├── pyproject.toml            # Package config with [project.scripts]
├── openenv.yaml              # OpenEnv spec (spec_version: 1)
│
├── server/
│   └── app.py                # FastAPI app via openenv-core create_app
│
├── environment/
│   └── env.py                # BugTriageEnv (used by inference & baseline)
│
├── graders/
│   ├── easy_grader.py        # Bug type accuracy
│   ├── medium_grader.py      # Bug type + file accuracy
│   └── hard_grader.py        # Full triage with TF-IDF semantic scoring
│
├── models/
│   ├── action.py             # BugAction (extends openenv-core Action)
│   ├── observation.py        # BugObservation (extends openenv-core Observation)
│   ├── scenario.py           # BugScenario (ground truth)
│   └── config.py             # Episode config
│
├── tasks/
│   ├── easy_task.py          # 14 easy scenarios
│   ├── medium_task.py        # 14 medium scenarios
│   ├── hard_task.py          # 14 hard scenarios
│   ├── task1.json            # Easy task definition
│   ├── task2.json            # Medium task definition
│   └── task3.json            # Hard task definition
│
├── utils/
│   └── normalization.py      # Action normalisation (aliases, casing, paths)
│
├── baseline/
│   └── baseline_agent.py     # Reference agent implementation
│
├── scripts/
│   └── validate_submission.py # Submission validator
│
└── tests/
    ├── test_env.py
    ├── test_graders.py
    ├── test_models.py
    └── test_normalization.py
```

---

## Local Setup

```bash
git clone https://github.com/VarshiniGunti/openenv-bug-triage-env.git
cd openenv-bug-triage-env
pip install -e .
uvicorn server.app:app --host 0.0.0.0 --port 7860
```

### Run Inference

```bash
export API_BASE_URL="https://api.openai.com/v1"
export MODEL_NAME="gpt-4.1-mini"
export HF_TOKEN="your-token"

python inference.py --task easy --episodes 1
```

Output format:
```
[START] task=easy env=openenv-bug-triage-env model=gpt-4.1-mini
[STEP] step=1 action=authentication reward=0.35 done=false error=null
[STEP] step=2 action=authentication reward=0.05 done=false error=null
[STEP] step=3 action=authentication reward=0.05 done=true error=null
[END] success=true steps=3 rewards=0.35,0.05,0.05
```

### Run Tests

```bash
pytest tests/ -v
```

### Docker

```bash
docker build -t bug-triage-env .
docker run -p 7860:7860 \
  -e API_BASE_URL="https://api.openai.com/v1" \
  -e MODEL_NAME="gpt-4.1-mini" \
  -e HF_TOKEN="your-token" \
  bug-triage-env
```

---

## Grading System

### Reward Design
All rewards are strictly in **(0, 1)** — never exactly 0 or 1.

| Task | Step 1 (bug_type) | Step 2 (file) | Step 3 (fix) |
|------|-------------------|---------------|--------------|
| Easy | 0.35 / 0.05 | — | — |
| Medium | 0.35 / 0.05 | 0.35 / 0.05 | — |
| Hard | 0.35 / 0.05 | 0.35 / 0.05 | 0.05–0.90 |

### Hard Task Fix Scoring (Hybrid)
1. **Keyword match** → high reward (0.90)
2. **TF-IDF cosine similarity ≥ 0.65** → 0.72
3. **TF-IDF cosine similarity ≥ 0.45** → 0.50
4. **TF-IDF cosine similarity ≥ 0.35** → 0.27 (reasoning credit)
5. **Below threshold** → 0.05

### Action Normalisation
The environment normalises agent actions before grading:
- `"Null Pointer"` → `"null_pointer"`
- `"src/auth.py"` → `"auth.py"`
- `"Add null check!"` → `"add null check"`
- 40+ bug type aliases supported

---

## Live Deployment

- **HuggingFace Space**: https://huggingface.co/spaces/Varshini28/openenv-bug-triage-env
- **API Base URL**: https://varshini28-openenv-bug-triage-env.hf.space
- **API Docs**: https://varshini28-openenv-bug-triage-env.hf.space/docs

---

## Environment Variables

| Variable | Default | Required |
|----------|---------|----------|
| `API_BASE_URL` | `https://api.openai.com/v1` | No |
| `MODEL_NAME` | `gpt-4.1-mini` | No |
| `HF_TOKEN` | — | Yes (inference only) |

---

## License

MIT License — see [LICENSE](LICENSE) for details.

---

*Built by Varshini Gunti · Meta × OpenEnv Hackathon 2026*
