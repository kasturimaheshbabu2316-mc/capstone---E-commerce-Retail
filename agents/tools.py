"""
agents/tools.py - Domain Tools & Least-Autonomy Role-Based Access Enforcement
Track: E-Commerce & Retail (Nykaa)
Tasks 6 & 15: Parameterized Escalation Scoring & Programmatic RBAC Tool Dispatch.
"""

from typing import Dict, Any, Optional
import sys
from pathlib import Path

# Add project root directory to sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from dataset import check_order_status as dataset_check_status
from rag.evaluation import query_with_grounded_fallback


class LeastAutonomyViolation(PermissionError):
    """Raised when an agent attempts to invoke a tool beyond its assigned scope."""
    pass


def check_order_status_tool(record_id: str, caller_agent_role: str = "Lookup Agent") -> Dict[str, Any]:
    """
    Lookup Agent Tool: Inspects transactional database for order state and escalation metrics.
    Least Autonomy Constraint: ONLY the Lookup Agent is authorized to call this tool.
    """
    if caller_agent_role != "Lookup Agent":
        raise LeastAutonomyViolation(
            f"Security Violation: Agent with role '{caller_agent_role}' is not authorized "
            f"to invoke 'check_order_status'. Only 'Lookup Agent' possesses transactional access."
        )

    return dataset_check_status(record_id)


def policy_rag_search_tool(query: str, caller_agent_role: str = "Retrieval Agent") -> Dict[str, Any]:
    """
    Retrieval Agent Tool: Queries the ChromaDB vector store for grounded Nykaa policy context.
    """
    return query_with_grounded_fallback(query_text=query, strategy="sentence")


if __name__ == "__main__":
    print("Testing tools & Least Autonomy enforcement:")
    # 1. Authorized call
    status = check_order_status_tool("NYK-1002", caller_agent_role="Lookup Agent")
    print(f"Authorized Lookup Agent call: Status={status['status']}, S_esc={status['escalation_score']}")

    # 2. Unauthorized call from Composer Agent
    try:
        check_order_status_tool("NYK-1002", caller_agent_role="Response Composer Agent")
        print("ERROR: Unauthorized call did not fail!")
    except LeastAutonomyViolation as e:
        print(f"PASS: Least Autonomy successfully blocked unauthorized invocation: {e}")
