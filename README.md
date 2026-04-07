---
title: AML Investigation Env
colorFrom: blue
colorTo: green
sdk: docker
app_port: 8000
---

# AML Investigation Environment

A rigorous, real-world Markov Decision Process (MDP) RL environment built on the `openenv-core` framework. Designed to evaluate an autonomous agent's ability to operate under a "Fog of War" doing high-stakes financial compliance work (Anti-Money Laundering analysis).

## Links:

* [Hugging Face Space](https://huggingface.co/spaces/TheDevCrew/aml_investigation_env)
* [GitHub Repository](https://github.com/mdkamranalam/aml-investigation)

## Environment Description & Motivation (Real-World Task)

In the real world, human analysts are constantly screening thousands of automated wire transfers. They are routinely given sparse initialization data (e.g., just a Transaction ID and Dollar amount) and must actively spend operational time/resources "investigating" multiple streams of data before making irreversible, legally binding terminal decisions.

**The Problem this Solves:** Most LLM benchmarks treat financial compliance as a single-turn classification string match. The **AML Investigation Environment** acts as a true interactive space where agents must mathematically balance the "cost" of investigating against the extreme penalties of making a blind terminal mistake, completely modeling actual banking operations.

---

## Action & Observation Spaces

The OpenEnv state is strictly governed by Pydantic models mapping a dynamic Hidden Ground Truth interface.

### The Observation Space (`AMLObservation`)

The environment enforces incomplete information. An agent initializes starting out totally blind:

* `transaction_id` (str)
* `amount_usd` (float)
* *(Hidden)* `kyc_data` (Only unlocked on request)
* *(Hidden)* `network_data` (Only unlocked on request)
* *(Hidden)* `history_data` (Only unlocked on request)
* `system_message`: A messaging layer the environment uses to feed boundary errors back to the AI.

### The Action Space (`AMLAction`)

The `AMLAction` model requires two exact parameters per step:

1. `action_type` (str): Must be exactly one of the six allowed enumeration strings below.
2. `rationale` (str): A mandated reasoning string simulating Analyst notes (e.g., "Need to check history because amount is high"). If missing, Pydantic fails validation.

**Investigative Actions (-0.05 step penalty):** Keeps the episode alive (`done=False`) and reveals data.

* `request_kyc`: Investigates the sender's identity. Unlocks the `kyc_data` block.
* `trace_network`: Investigates wire tracing and connections. Unlocks `network_data`.
* `check_history`: Pulls past transaction anomaly alerts. Unlocks `history_data`.

**Terminal Actions:** Instantly ends the episode (`done=True`) and submits to the Grader.

* `approve_transaction`: Use when data safely proves the transaction is benign.
* `freeze_account`: Use when data is highly suspicious and requires a manual hold.
* `escalate_to_fincen`: Use when severe corporate/money laundering risk is identified.

### Anti-Exploit Mechanics

* **Amnesia Prevention:** Applying an action like `request_kyc` twice aggressively penalizes the agent by `-0.20` and fails to yield new information.
* **Infinite Loop Safety:** Hard cap cutoff bounds at 6 steps. Auto-terminates with `0.0` points if an agent refuses a terminal decision.

---

## Task Difficulties & Graders

The tasks are automatically and randomly seeded dynamically natively inside `src/tasks.py`. The Grader compares the terminal action to the explicitly defined hidden reality to dispense a strictly bounded `0.0` (Fail) or `1.0` (Success).

1. **Easy Task:** A standard $150 transaction with perfect KYC data and no bad actors. Success requires taking investigative actions and verifying nothing is out of place before hitting `approve_transaction`.
2. **Medium Task:** A tricky $9500 edge-case transaction where risk bounds are slightly elevated. History highlights weird spikes in suspicious flags requiring deeper probing. The strict correct conclusion is to temporarily `freeze_account`.
3. **Hard Task:** A massive $450,000 movement hidden behind 5 network "hops", high-risk jurisdictions, shell company affiliations, and fake KYC data. To solve this, the LLM must peel back multiple layers of investigation before recognizing pattern severity and correctly using `escalate_to_fincen`.

---

## Procedural Simulation Mode

Beyond the fixed benchmark set, the environment features a **Synthetic Case Generator** for high-fidelity RL training.

By default, the `reset()` function uses a **Mixture Mode**:

* **70% Deterministic:** Resets to one of the three "Golden" benchmark tasks (Easy, Medium, or Hard) for consistent scoring.
* **30% Synthetic:** Generates a completely unique transaction with randomized IDs (`SYNTH-####`), amounts, jurisdictions (e.g., Panama, Caymans, UK), and risk notes.

This hybrid approach ensures that agents can be both **evaluated** (on the fixed set) and **trained** (on the infinite synthetic set) to generalize their compliance reasoning.

---

## How to use on Hugging Face (Gradio Playground)

When you access the Hugging Face Space URL, OpenEnv automatically provides an interactive web UI (Playground) allowing humans to play the environment!

1. **Reset**: Click the **Reset** button to initialize a new random episode. The *Raw JSON response* box will populate with initial sparse data.
2. **Action Selection**: Under **Action Type**, select an investigative or terminal action.
3. **Rationale**: You must type a reason in the **Rationale** text box (simulating analyst notes).
4. **Step**: Click the **Step** button to process the action.

### Glossary of Actions

* `request_kyc`: Investigates sender identity (-0.05).
* `trace_network`: Investigates wire tracing and connections (-0.05).
* `check_history`: Pulls past transaction anomaly alerts (-0.05).
* `approve_transaction`: Ends episode. Use for verified safe entities.
* `freeze_account`: Ends episode. Use for suspicious but non-definitive risk.
* `escalate_to_fincen`: Ends episode. Use for severe laundering/terrorist risk.

---

### Try it Yourself: Test Cases

The environment uses a **70% mixture of fixed benchmark tasks**. Click **Reset** until the `amount_usd` matches one of the values below to follow the manual walkthrough:

**1. The "Clean Transfer" (Easy - $150.00)**

* **Action 1**: `request_kyc` (Rationale: "Routine ID verification"). → Verify `kyc_data` says `status: verified`.
* **Action 2**: `approve_transaction` (Rationale: "Low risk and verified").
* **Trajectory Score**: **0.95** (1.00 base - 0.05 investigative cost).

**2. The "Structuring Risk" (Medium - $9,500.00)**

* **Action 1**: `check_history` (Rationale: "Checking past alerts for sub-10k transfer"). → Verify `history_data` shows `suspicious_flags: 1`.
* **Action 2**: `trace_network` (Rationale: "Investigating jurisdictional hops"). → Verify `network_data` shows `hops: 3`.
* **Action 3**: `freeze_account` (Rationale: "Risk flags and multiple hops found").
* **Trajectory Score**: **0.90** (1.00 base - 0.10 investigative cost).

**3. The "Shell Network" (Hard - $450,000.00)**

* **Action 1**: `request_kyc` (Rationale: "Investigating shell affiliations"). → Verify `kyc_data` says `Shell company suspicion`.
* **Action 2**: `trace_network` (Rationale: "Tracing beneficiary hops"). → Verify `network_data` shows `hops: 5`.
* **Action 3**: `escalate_to_fincen` (Rationale: "Definitive money laundering network").
* **Trajectory Score**: **0.90** (1.00 base - 0.10 investigative cost).

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
uv run server/app.py 
```

### Baseline Inference execution

Run the inference loop to sequentially benchmark all tasks under local strict logs:

```bash
HF_TOKEN="your_key" uv run python3 inference.py
```

---

## Baseline Benchmark Scores

Evaluated using `Qwen2.5-72B-Instruct` over the standard OpenEnv interface.

| Difficulty | Best Score | Success Rate (3 Runs) | AI Behavior Notes |
| :--- | :--- | :--- | :--- |
| **Easy** | **0.900** | 100% (3/3) | Flawlessly solves low-risk verifications. |
| **Medium** | **0.850** | 33% (1/3) | High variance. Frequently struggles with ambiguity, preferring to over-escalate. |
| **Hard** | **0.850** | 66% (2/3) | Strong performance. Generally recognizes definitive networking scale risks. |

*Note: As demonstrated by the empirical evaluation variance above, frontier models like Qwen-72B are capable of perfectly navigating the "Fog of War" across all difficulties. However, the Medium/Hard boundary requires deliberate, non-binary reasoning that forces the AI into inconsistent edge-case failures, proving the environment's rigorous utility.*
