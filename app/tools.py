"""
app/tools.py - Domain Tools & Guardrails Layer
Track: E-Commerce & Retail (Nykaa)
"""

from typing import Dict, Any, Optional, Tuple, List
import sys
from pathlib import Path

# Add project root directory to sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from agents.tools import (
    check_order_status_tool,
    policy_rag_search_tool,
    LeastAutonomyViolation,
)
from agents.guardrails import (
    mask_pii,
    check_prompt_injection,
    validate_groundedness,
    apply_input_guardrails,
    STANDARD_REFUSAL,
)

__all__ = [
    "check_order_status_tool",
    "policy_rag_search_tool",
    "LeastAutonomyViolation",
    "mask_pii",
    "check_prompt_injection",
    "validate_groundedness",
    "apply_input_guardrails",
    "STANDARD_REFUSAL",
]

if __name__ == "__main__":
    res = apply_input_guardrails("Call me at +91 9988776655 regarding my order")
    print("Guardrail sanitization:", res)
