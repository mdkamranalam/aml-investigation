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

def evaluate_decision(task: dict, terminal_action: str) -> float:
    """
    Evaluates the terminal action against the task's expected action.
    Returns 1.0 if correct, 0.0 if incorrect.
    """
    if task["expected_action"] == terminal_action:
        return 1.0
    return 0.0
