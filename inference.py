"""Inference script for running bug triage episodes with OpenAI-compatible models."""

import os
import json
import sys
from typing import Optional
from datetime import datetime

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models.config import Config
from models.action import BugAction
from env import BugTriageEnv
from logging_config import setup_logging, get_logger


def parse_action_from_response(response_text: str, retry_count: int = 0) -> Optional[BugAction]:
    """
    Parse BugAction from model response with retry logic.
    
    Args:
        response_text: Response text from model API
        retry_count: Number of retries attempted
        
    Returns:
        BugAction object or None if parsing fails
    """
    logger = get_logger()
    
    try:
        # Try to extract JSON from response
        import re
        json_match = re.search(r'\{[^{}]*\}', response_text, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
            action_dict = json.loads(json_str)
            
            # Validate required fields
            required_fields = {"bug_type", "file", "fix"}
            if not all(field in action_dict for field in required_fields):
                raise ValueError(f"Missing required fields. Expected: {required_fields}")
            
            return BugAction(**action_dict)
        else:
            raise ValueError("No JSON object found in response")
    
    except json.JSONDecodeError as e:
        logger.error(f"JSON parsing failed (attempt {retry_count + 1}): {e}")
        if retry_count == 0:
            logger.warning("Retrying with correction prompt...")
            return None
    except Exception as e:
        logger.error(f"Failed to parse action from response: {e}")
    
    return None


def run_episode(
    env: BugTriageEnv,
    model_name: str,
    api_base_url: str,
    hf_token: str
) -> dict:
    """
    Run a single episode with the environment.
    
    Args:
        env: The BugTriageEnv instance
        model_name: Name of the model to use
        api_base_url: API base URL
        hf_token: HuggingFace token
        
    Returns:
        Episode results dictionary
    """
    logger = get_logger()
    
    # Log episode start
    task_name = env.config.task
    print(f"[START] task={task_name} env=bug_triage_env model={model_name}")
    logger.info(f"Episode started: task={task_name}, model={model_name}")
    
    # Reset environment
    observation = env.reset()
    
    steps_data = []
    total_reward = 0.0
    success = True
    error_msg = None
    
    # Run 3 steps
    for step_num in range(1, 4):
        try:
            # Create prompt for this step
            prompt = create_step_prompt(observation, step_num, env.config.task)
            
            # Call model API
            response = call_model_api(prompt, model_name, api_base_url, hf_token)
            
            # Parse action from response with retry on JSON failure
            action = parse_action_from_response(response, retry_count=0)
            
            if action is None:
                # Retry with correction prompt
                correction_prompt = f"""{response}

If your previous output was not valid JSON, return ONLY valid JSON using this exact schema:
{{"bug_type": "<bug_type>", "file": "<module_file>", "fix": "<fix_description>"}}

Do not include any explanations or extra text."""
                
                retry_response = call_model_api(correction_prompt, model_name, api_base_url, hf_token)
                action = parse_action_from_response(retry_response, retry_count=1)
            
            if action is None:
                raise ValueError("Failed to parse action from model response after retry")
            
            # Execute step
            observation, reward, done, info = env.step(action)
            total_reward += reward
            
            # Log step
            action_str = f"bug_type={action.bug_type}, file={action.file}"
            print(f"[STEP] step={step_num} action={action_str} reward={reward:.2f} done={done} error=null")
            logger.info(f"Step {step_num}: reward={reward:.2f}")
            
            steps_data.append({
                "step": step_num,
                "action": action.model_dump(),
                "reward": reward,
                "done": done
            })
            
            if done:
                break
        
        except Exception as e:
            error_msg = str(e)
            success = False
            print(f"[STEP] step={step_num} action=null reward=0.00 done=true error={error_msg}")
            logger.error(f"Step {step_num} failed: {error_msg}")
            break
    
    # Log episode end
    rewards_str = ",".join(f"{r:.2f}" for r in env.episode_rewards)
    print(f"[END] success={str(success).lower()} steps={len(steps_data)} score={total_reward:.2f} rewards={rewards_str}")
    logger.info(f"Episode ended: success={success}, score={total_reward:.2f}")
    
    return {
        "success": success,
        "steps": len(steps_data),
        "score": total_reward,
        "rewards": env.episode_rewards,
        "error": error_msg
    }


def create_step_prompt(observation, step: int, task: str) -> str:
    """
    Create a step-aware prompt for the model based on the current step.
    Enforces structured JSON output with controlled vocabulary.
    
    Args:
        observation: Current BugObservation
        step: Current step number (1, 2, or 3)
        task: Task difficulty
        
    Returns:
        Prompt string for the model
    """
    # Controlled bug type vocabulary
    allowed_bug_types = ["memory", "logic", "authentication", "database", "performance", "null_pointer", "session", "race_condition"]
    bug_type_list = ", ".join(allowed_bug_types)
    
    # Base instruction for structured output
    base_instruction = f"""You must output the action as valid JSON using this exact schema:
{{"bug_type": "<bug_type>", "file": "<module_file>", "fix": "<fix_description>"}}

CRITICAL RULES:
1. bug_type must be one of: {bug_type_list}
2. file must be a valid module name from the available modules
3. fix must be a brief description of the fix
4. Do not include any explanations, markdown, or extra text
5. Return ONLY the JSON object, nothing else"""
    
    if step == 1:
        return f"""Step 1: Classify the bug type from the vocabulary.

Bug Report: {observation.bug_report}

Available modules: {', '.join(observation.repo_modules)}

Allowed bug types: {bug_type_list}

{base_instruction}"""
    
    elif step == 2:
        return f"""Step 2: Identify the most likely module responsible for the bug.

Bug Report: {observation.bug_report}

Available modules: {', '.join(observation.repo_modules)}

Allowed bug types: {bug_type_list}

{base_instruction}"""
    
    else:  # step == 3
        return f"""Step 3: Propose a detailed fix description.

Bug Report: {observation.bug_report}

Available modules: {', '.join(observation.repo_modules)}

Allowed bug types: {bug_type_list}

{base_instruction}"""


def call_model_api(
    prompt: str,
    model_name: str,
    api_base_url: str,
    hf_token: str
) -> str:
    """
    Call model API with the given prompt.
    
    Args:
        prompt: The prompt to send to the model
        model_name: Name of the model to use
        api_base_url: API base URL
        hf_token: HuggingFace token
        
    Returns:
        Response text from the model
    """
    try:
        from openai import OpenAI
        
        # Create client with custom base URL
        client = OpenAI(
            api_key=hf_token,
            base_url=api_base_url
        )
        
        # Call API
        response = client.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=500
        )
        
        return response.choices[0].message.content
    
    except ImportError:
        raise ImportError("OpenAI library not installed. Install with: pip install openai")
    except Exception as e:
        raise RuntimeError(f"Model API call failed: {e}")


def main():
    """Main entry point for the inference script."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run bug triage inference with OpenAI-compatible models")
    parser.add_argument("--task", default="easy", choices=["easy", "medium", "hard"],
                       help="Task difficulty level")
    parser.add_argument("--seed", type=int, help="Random seed for reproducibility")
    parser.add_argument("--episodes", type=int, default=1,
                       help="Number of episodes to run")
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging()
    logger = get_logger()
    
    # Read required environment variables
    api_base_url = os.getenv("API_BASE_URL")
    model_name = os.getenv("MODEL_NAME")
    hf_token = os.getenv("HF_TOKEN")
    
    if not api_base_url:
        raise ValueError("API_BASE_URL environment variable not set")
    if not model_name:
        raise ValueError("MODEL_NAME environment variable not set")
    if not hf_token:
        raise ValueError("HF_TOKEN environment variable not set")
    
    # Create configuration
    config = Config(
        task=args.task,
        max_steps=3,
        seed=args.seed
    )
    
    # Run episodes
    results = []
    for episode_num in range(args.episodes):
        env = BugTriageEnv(config)
        result = run_episode(env, model_name, api_base_url, hf_token)
        results.append(result)
        
        if args.episodes > 1:
            print()  # Blank line between episodes
    
    # Print summary
    if args.episodes > 1:
        successful = sum(1 for r in results if r["success"])
        avg_score = sum(r["score"] for r in results) / len(results)
        print(f"\nSummary: {successful}/{args.episodes} successful, avg_score={avg_score:.2f}")


if __name__ == "__main__":
    main()
