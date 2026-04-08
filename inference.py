import json
import os
import textwrap
from typing import List, Optional
from openai import OpenAI

from src.env import AMLInvestigationEnv
from src.models import AMLAction
from src.tasks import TASKS

# Environment settings from pre-submission logic requirements
API_BASE_URL = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "Qwen/Qwen2.5-72B-Instruct")
HF_TOKEN = os.getenv("HF_TOKEN")

# Optional - if you use from_docker_image():
LOCAL_IMAGE_NAME = os.getenv("LOCAL_IMAGE_NAME")
BENCHMARK = "aml_investigation"
MAX_STEPS = 6

def log_start(task: str, env: str, model: str) -> None:
    print(f"[START] task={task} env={env} model={model}", flush=True)

def log_step(step: int, action: str, reward: float, done: bool, error: Optional[str]) -> None:
    error_val = error if error else "null"
    done_val = str(done).lower()
    print(
        f"[STEP] step={step} action={action} reward={reward:.2f} done={done_val} error={error_val}",
        flush=True,
    )

def log_end(success: bool, steps: int, score: float, rewards: List[float]) -> None:
    rewards_str = ",".join(f"{r:.2f}" for r in rewards)
    print(f"[END] success={str(success).lower()} steps={steps} score={score:.3f} rewards={rewards_str}", flush=True)

def get_observation_json(obs):
    if hasattr(obs, 'model_dump_json'):
        return obs.model_dump_json()
    return obs.json()

def run_task(client: OpenAI, env: AMLInvestigationEnv, task_name: str):
    obs = env.reset(task_name=task_name)
    log_start(task=task_name, env=BENCHMARK, model=MODEL_NAME)

    messages = [
        {
            "role": "system", 
            "content": textwrap.dedent("""
                You are an expert compliance analyst AI operating an AML Investigation Environment. 
                At each step, analyze the data to decide whether to investigate further 
                (request_kyc, trace_network, check_history) or take a terminal action 
                (approve_transaction, freeze_account, escalate_to_fincen). 
                Output your response strictly as a JSON object matching this schema: 
                {"action_type": "<action>", "rationale": "<reasoning>"}
            """).strip()
        }
    ]

    rewards: List[float] = []
    steps_taken = 0
    score = 0.0
    success = False

    try:
        while not obs.done:
            steps_taken += 1
            messages.append({
                "role": "user", 
                "content": f"Current Observation: {get_observation_json(obs)}"
            })

            error = None
            try:
                response = client.chat.completions.create(
                    model=MODEL_NAME,
                    messages=messages,
                    response_format={"type": "json_object"}
                )
                ai_response_content = response.choices[0].message.content
            except Exception as e:
                ai_response_content = '{"action_type": "request_kyc", "rationale": "Fallback after API error"}'
                error = f"API Error: {e}"

            messages.append({
                "role": "assistant",
                "content": ai_response_content
            })

            try:
                action_dict = json.loads(ai_response_content)
                action = AMLAction(**action_dict)
                action_str = action.action_type
            except Exception as e:
                action = AMLAction(action_type="request_kyc", rationale="Fallback due to parsing error.")
                action_str = "request_kyc"
                error = f"Parse Error: {e}"

            obs = env.step(action)
            reward = obs.reward or 0.0
            
            rewards.append(reward)
            log_step(step=steps_taken, action=f"{action_str}", reward=reward, done=obs.done, error=error)

        state = env.get_full_state()
        final_reward = state["accumulated_reward"]
        
        score = final_reward
        score = min(max(score, 0.0), 1.0)  # clamp to [0, 1]
        success = (rewards[-1] == 1.0) if len(rewards) > 0 else False

    except Exception as e:
        print(f"[DEBUG] Runtime error: {e}", flush=True)
    finally:
        log_end(success=success, steps=steps_taken, score=score, rewards=rewards)


def main():
    client = OpenAI(
        api_key=HF_TOKEN,
        base_url=API_BASE_URL
    )
    env = AMLInvestigationEnv(max_steps=MAX_STEPS)
    
    # Run the baseline sequentially on all 3 tasks to produce a reproducible baseline score.
    for task_name in ["Easy", "Medium", "Hard"]:
        run_task(client, env, task_name)


if __name__ == "__main__":
    main()
