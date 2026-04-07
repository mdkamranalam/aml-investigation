import random
from typing import Dict, Any

# Fixed Benchmark Tasks for reproducible scoring
TASKS = {
    "Easy": {
        "transaction_id": "TXN-1001",
        "amount_usd": 150.00,
        "kyc_data": {"status": "verified", "risk_score": "low"},
        "network_data": {"hops": 1, "known_bad_actors": 0},
        "history_data": {"past_transactions": 50, "suspicious_flags": 0},
        "expected_action": "approve_transaction"
    },
    "Medium": {
        "transaction_id": "TXN-2042",
        "amount_usd": 9500.00,
        "kyc_data": {"status": "verified", "risk_score": "medium"},
        "network_data": {"hops": 3, "known_bad_actors": 0},
        "history_data": {"past_transactions": 2, "suspicious_flags": 1},
        "expected_action": "freeze_account"
    },
    "Hard": {
        "transaction_id": "TXN-9999",
        "amount_usd": 450000.00,
        "kyc_data": {"status": "pending", "risk_score": "high", "notes": "Shell company suspicion"},
        "network_data": {"hops": 5, "known_bad_actors": 2, "jurisdictions": ["High Risk A", "High Risk B"]},
        "history_data": {"past_transactions": 0, "suspicious_flags": 3},
        "expected_action": "escalate_to_fincen"
    }
}

def generate_synthetic_task(difficulty: str = None) -> dict:
    """
    Generates a procedurally randomized AML task for infinite variety.
    Ideal for training RL agents to generalize across different risks.
    """
    if not difficulty:
        difficulty = random.choice(["Easy", "Medium", "Hard"])
    
    txn_id = f"SYNTH-{random.randint(1000, 9999)}"
    
    # Random jurisdictions for realism
    high_risk_zones = ["Cayman Islands", "Panama", "North Korea", "High Risk Zone Gamma"]
    safe_zones = ["USA", "Germany", "Japan", "UK"]

    if difficulty == "Easy":
        return {
            "transaction_id": txn_id,
            "amount_usd": round(random.uniform(50.0, 1000.0), 2),
            "kyc_data": {"status": "verified", "risk_score": "low", "flags": 0},
            "network_data": {"hops": random.randint(1, 2), "known_bad_actors": 0, "jurisdiction": random.choice(safe_zones)},
            "history_data": {"past_transactions": random.randint(20, 200), "suspicious_flags": 0},
            "expected_action": "approve_transaction"
        }
    elif difficulty == "Medium":
        return {
            "transaction_id": txn_id,
            "amount_usd": round(random.uniform(8000.0, 12000.0), 2),
            "kyc_data": {"status": random.choice(["verified", "pending"]), "risk_score": "medium"},
            "network_data": {"hops": random.randint(3, 4), "known_bad_actors": random.choice([0, 1])},
            "history_data": {"past_transactions": random.randint(1, 5), "suspicious_flags": random.randint(1, 2)},
            "expected_action": "freeze_account"
        }
    else: # Hard
        return {
            "transaction_id": txn_id,
            "amount_usd": round(random.uniform(100000.0, 5000000.0), 2),
            "kyc_data": {"status": "pending", "risk_score": "high", "notes": "Complex beneficiary structure"},
            "network_data": {
                "hops": random.randint(5, 12), 
                "known_bad_actors": random.randint(2, 6), 
                "jurisdictions": random.sample(high_risk_zones, 2)
            },
            "history_data": {"past_transactions": random.randint(0, 1), "suspicious_flags": random.randint(3, 8)},
            "expected_action": "escalate_to_fincen"
        }

def evaluate_decision(task: dict, terminal_action: str) -> float:
    """
    Deterministically evaluates a terminal decision against the hidden ground truth.
    Returns 1.0 for alignment, 0.0 for failure.
    """
    if task.get("expected_action") == terminal_action:
        return 1.0
    return 0.0
