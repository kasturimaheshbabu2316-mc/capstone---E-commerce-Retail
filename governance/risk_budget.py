"""
governance/risk_budget.py - AI Governance Framework & Runtime Budget Controls
Track: E-Commerce & Retail (Nykaa)
Task 15: Least Autonomy Segregation, Operational Risk Categorization & Token Budget Guard.
"""

from typing import Dict, Any, Tuple
import os
import sys
from pathlib import Path

# Add project root directory to sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# Enterprise AI Operational Risk Classification
OPERATIONAL_RISK_PROFILE = {
    "system_name": "Nykaa Enterprise Domain Support Agent",
    "domain": "E-Commerce & Retail Customer Support",
    "risk_classification": "Medium Risk",
    "risk_rationale": (
        "Handles post-order customer inquiries, return/refund authorizations, "
        "and logistics escalation routing. Decisions impact customer satisfaction "
        "and logistics triage but do not directly execute unauthorized financial debits "
        "or safety-critical automated actions."
    ),
    "governance_controls": [
        "Principle of Least Autonomy (RBAC role-isolated tool invocation)",
        "Deterministic MOCK_LLM execution with zero external egress",
        "Deterministic PII regex redaction for phone numbers and payment card digits",
        "Dual-Agent AutoGen compliance and grounding audit prior to final delivery",
        "Runtime token and character budget caps with HTTP 429 backpressure",
        "ELK-ready single-line JSON transaction auditing",
    ],
}

MAX_SIMULATED_TOKEN_BUDGET = 500  # Token limit per inbound customer request
CHARS_PER_TOKEN = 4               # Standard heuristic: ~4 chars per token


class BudgetExceededError(ValueError):
    """Raised when an inbound customer query breaches the runtime token budget."""
    pass


def estimate_tokens(text: str) -> int:
    """Estimates token count using character length heuristic."""
    return max(1, len(text.strip()) // CHARS_PER_TOKEN)


def enforce_runtime_budget(query: str, max_tokens: int = MAX_SIMULATED_TOKEN_BUDGET) -> Tuple[bool, int, str]:
    """
    Evaluates query size against upper token budget.
    Raises BudgetExceededError / HTTP 429 condition if oversized.
    """
    token_count = estimate_tokens(query)
    if token_count > max_tokens:
        err_msg = (
            f"HTTP 429 BudgetExceeded: Inbound request estimated at {token_count} tokens "
            f"exceeds maximum allowed runtime budget of {max_tokens} tokens."
        )
        return False, token_count, err_msg
    return True, token_count, "Within budget limits."


if __name__ == "__main__":
    print("--- AI GOVERNANCE RISK CLASSIFICATION ---")
    print(f"System: {OPERATIONAL_RISK_PROFILE['system_name']}")
    print(f"Risk Tier: {OPERATIONAL_RISK_PROFILE['risk_classification']}")
    print(f"Rationale: {OPERATIONAL_RISK_PROFILE['risk_rationale']}")

    print("\n--- RUNTIME TOKEN BUDGET ENFORCEMENT ---")
    normal_q = "How many days is the return window for beauty items?"
    ok, count, msg = enforce_runtime_budget(normal_q)
    print(f"Normal Query: Tokens={count} | OK={ok} | {msg}")

    huge_q = "Order help! " * 250  # ~3000 chars -> ~750 tokens
    ok2, count2, msg2 = enforce_runtime_budget(huge_q)
    print(f"Oversized Query: Tokens={count2} | OK={ok2} | {msg2}")
