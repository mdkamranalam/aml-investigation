---
title: AML Investigation Env
colorFrom: blue
colorTo: green
sdk: docker
app_port: 8000
---
# AML Investigation Environment

A rigorous, real-world Markov Decision Process (MDP) RL environment built on the `openenv-core` framework. Designed to evaluate an autonomous agent's ability to operate under a "Fog of War" doing high-stakes financial compliance work (Anti-Money Laundering analysis).

## Environment Description & Motivation (Real-World Task)
In the real world, human analysts are constantly screening thousands of automated wire transfers. They are routinely given sparse initialization data (e.g., just a Transaction ID and Dollar amount) and must actively spend operational time/resources "investigating" multiple streams of data before making irreversible, legally binding terminal decisions.

**The Problem this Solves:** Most LLM benchmarks treat financial compliance as a single-turn classification string match. The **AML Investigation Environment** acts as a true interactive space where agents must mathematically balance the "cost" of investigating against the extreme penalties of making a blind terminal mistake, completely modeling actual banking operations.

---

## Action & Observation Spaces
The OpenEnv state is strictly governed by Pydantic models mapping a dynamic Hidden Ground Truth interface.

### The Observation Space (`AMLObservation`)
The environment enforces incomplete information. An agent initializes starting out totally blind:
*   `transaction_id` (str)
*   `amount_usd` (float)
*   *(Hidden)* `kyc_data` (Only unlocked on request)
*   *(Hidden)* `network_data` (Only unlocked on request)
*   *(Hidden)* `history_data` (Only unlocked on request)
*   `system_message`: A messaging layer the environment uses to feed boundary errors back to the AI. 

### The Action Space (`AMLAction`)
The agent can choose between two fundamental action modes. **All actions strictly require a typed `rationale` reasoning string.**
1. **Investigative Actions (-0.05 step penalty):** Keeps the episode alive `done=False`. Requesting `request_kyc`, `trace_network`, or `check_history` reveals those specific hidden chunks of data in the following Observation. 
2. **Terminal Actions:** Immediately ends the episode `done=True` and submits to the grader. `approve_transaction`, `freeze_account`, or `escalate_to_fincen`.

### Anti-Exploit Mechanics
*   **Amnesia Prevention:** Applying an action like `request_kyc` twice aggressively penalizes the agent by `-0.20` and fails to yield new information.
*   **Infinite Loop Safety:** Hard cap cutoff bounds at 6 steps. Auto-terminates with `0.0` points if an agent refuses a terminal decision.

---

## Task Difficulties & Graders
The tasks are automatically and randomly seeded dynamically natively inside `src/tasks.py`. The Grader compares the terminal action to the explicitly defined hidden reality to dispense a strictly bounded `0.0` (Fail) or `1.0` (Success).

1.  **Easy Task:** A standard $150 transaction with perfect KYC data and no bad actors. Success requires taking investigative actions and verifying nothing is out of place before hitting `approve_transaction`. 
2.  **Medium Task:** A tricky $9500 edge-case transaction where risk bounds are slightly elevated. History highlights weird spikes in suspicious flags requiring deeper probing. The strict correct conclusion is to temporarily `freeze_account`.
3.  **Hard Task:** A massive $450,000 movement hidden behind 5 network "hops", high-risk jurisdictions, shell company affiliations, and fake KYC data. To solve this, the LLM must peel back multiple layers of investigation before recognizing pattern severity and correctly using `escalate_to_fincen`.

---

## Setup & Usage Instructions

### Docker Run (HF Space Compatible)
The project natively wraps into an isolated container instance for massive scalability scoring:
```bash
docker build -t aml-investigation-env .
docker run -p 8000:8000 aml-investigation-env 
```

### Local Dev Run (uv)
To dynamically spawn the API server on `http://127.0.0.1:8000`:
```bash
# Start the Env HTTP Router Let
uv run server/app.py 
```

### Baseline Inference execution
Run the inference loop to sequentially benchmark all tasks under local strict logs:
```bash
HF_TOKEN="your_key" uv run python3 inference.py
```

---

## Baseline Score 
Using standard endpoint evaluation running over OpenAI API formatting.

| Model | Task Difficulty | Action Steps Used | Final Score |
| :--- | :--- | :--- | :--- |
| `Qwen/Qwen2.5-72B-Instruct` | Easy | 3 | **0.900** |
| `Qwen/Qwen2.5-72B-Instruct` | Medium | 4 | **0.850** |
| `Qwen/Qwen2.5-72B-Instruct` | Hard | 4 | **0.850** |

*Note: The model loses `0.05` points for every investigation action intentionally requested, proving it properly managed the MDP Fog-of-War costs while maximizing task safety correctly.*
