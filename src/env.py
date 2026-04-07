import random
from typing import Dict, Any, Tuple
from uuid import uuid4

from openenv.core.env_server.interfaces import Environment
from openenv.core.env_server.types import State

from .models import AMLAction, AMLObservation
from .tasks import TASKS, evaluate_decision, generate_synthetic_task

class AMLInvestigationEnv(Environment):
    """
    Automated Audit Triage + AML Investigation Environment.
    A multi-step MDP simulating a Fog-of-War compliance analyst task.
    """
    SUPPORTS_CONCURRENT_SESSIONS: bool = True

    def __init__(self, max_steps: int = 6):
        """
        Initializes the AML Investigation Environment setting the max steps.
        Also initiates the strict openenv base State container.
        """
        self.max_steps = max_steps
        self._state = State(episode_id=str(uuid4()), step_count=0)
        self.reset()
        
    def reset(self, task_name: str = None) -> AMLObservation:
        """
        Resets the environment. 
        Supports fixed benchmarks ("Easy", "Medium", "Hard") or 
        procedural generation if task_name is None.
        """
        if task_name in TASKS:
            self.hidden_truth = TASKS[task_name].copy()
        else:
            # Generate a fresh, unique synthetic task for infinite variety 🧬
            self.hidden_truth = generate_synthetic_task()
            task_name = task_name or "Synthetic"
            
        self.hidden_truth["task_name"] = task_name
        self._state = State(episode_id=str(uuid4()), step_count=0)
        
        self.current_obs = AMLObservation(
            transaction_id=self.hidden_truth["transaction_id"],
            amount_usd=self.hidden_truth["amount_usd"],
            done=False,
            reward=0.0
        )
        
        self.used_actions = set()
        self.accumulated_reward = 0.0
        
        return self.current_obs

    def step(self, action: AMLAction) -> AMLObservation:
        """
        Processes a single Markov Decision Process (MDP) step.
        Supports Investigative Actions (unlocking Fog of War) and 
        Terminal Decisions (closing the case with the grader).
        """
        if self.current_obs.done:
            self.current_obs.system_message = "Episode is already completed."
            return self.current_obs

        self._state.step_count += 1
        step_reward = 0.0
        self.current_obs.system_message = None
        action_type = action.action_type

        # Constraint: Infinite Loop Prevention
        if self._state.step_count >= self.max_steps and action_type not in ["approve_transaction", "freeze_account", "escalate_to_fincen"]:
            self.current_obs.done = True
            self.current_obs.system_message = "Max steps reached without a terminal decision. Auto-terminating."
            self.current_obs.reward = 0.0
            return self.current_obs
            
        is_investigative = action_type in ["request_kyc", "trace_network", "check_history"]
        
        if is_investigative:
            # Constraint: Amnesia Prevention (Penalize redundancy)
            if action_type in self.used_actions:
                self.current_obs.system_message = f"Error: Action '{action_type}' already used."
                step_reward = -0.2
            else:
                self.used_actions.add(action_type)
                step_reward = -0.05
                # Reveal specific data pieces from hidden ground truth
                if action_type == "request_kyc":
                    self.current_obs.kyc_data = self.hidden_truth.get("kyc_data")
                elif action_type == "trace_network":
                    self.current_obs.network_data = self.hidden_truth.get("network_data")
                elif action_type == "check_history":
                    self.current_obs.history_data = self.hidden_truth.get("history_data")
        else:
            # Terminal action logic with deterministic grading
            self.current_obs.done = True
            step_reward = evaluate_decision(self.hidden_truth, action_type)
            
        self.accumulated_reward += step_reward
        self.current_obs.reward = step_reward
        
        return self.current_obs
        
    @property
    def state(self) -> State:
        """ Returns the environment's openenv base state container. """
        return self._state
        
    def get_full_state(self) -> Dict[str, Any]:
        """ Helper helper to fetch the raw environment state (for debugging/logs). """
        obs_dict = self.current_obs.model_dump() if hasattr(self.current_obs, "model_dump") else self.current_obs.dict()
        return {
            "step": self._state.step_count,
            "accumulated_reward": self.accumulated_reward,
            "observation": obs_dict,
            "hidden_truth": self.hidden_truth,
            "done": self.current_obs.done
        }
