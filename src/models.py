from pydantic import BaseModel, Field
from typing import Optional, Dict, Literal

class AMLAction(BaseModel):
    action_type: Literal[
        "request_kyc", 
        "trace_network", 
        "check_history", 
        "approve_transaction", 
        "freeze_account", 
        "escalate_to_fincen"
    ] = Field(..., description="The type of action to perform. Can be investigative or terminal.")
    rationale: str = Field(..., description="The rationale for taking this action.")

class AMLObservation(BaseModel):
    transaction_id: str
    amount_usd: float
    kyc_data: Optional[Dict] = None
    network_data: Optional[Dict] = None
    history_data: Optional[Dict] = None
    system_message: Optional[str] = None
    done: bool = False
    reward: float = 0.0
