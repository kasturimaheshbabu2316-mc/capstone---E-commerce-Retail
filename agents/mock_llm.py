"""
agents/mock_llm.py - Deterministic Offline BaseLLM Implementation
Track: E-Commerce & Retail (Nykaa)
Task 7: CrewAI Custom BaseLLM Extension with Pitfall 1 and Pitfall 2 Mitigations.
"""

from typing import Any, List, Optional, Dict
import re
import json

# BaseLLM import fallback for air-gapped / offline environments
try:
    from crewai.llms.base_llm import BaseLLM  # type: ignore
except Exception:
    class BaseLLM:  # type: ignore
        """Lightweight stand-in if CrewAI BaseLLM cannot be directly loaded."""
        def __init__(self, *args, **kwargs):
            pass


class MockLLM(BaseLLM):
    """
    Deterministic offline LLM subclass.
    Zero external network calls, zero API keys.
    Addresses Pitfall 1 (ReAct Template Collision) and Pitfall 2 (Tool Routing Collision).
    """

    def __init__(self, model_name: str = "mock-deterministic-nykaa-llm", **kwargs):
        super().__init__(**kwargs)
        self.model_name = model_name

    def call(
        self,
        messages: Any,
        tools: Optional[List[Dict[str, Any]]] = None,
        callbacks: Optional[List[Any]] = None,
    ) -> str:
        """
        Main inference entrypoint called by CrewAI agents during ReAct reasoning loops.
        """
        prompt_str = ""
        if isinstance(messages, str):
            prompt_str = messages
        elif isinstance(messages, list):
            for m in messages:
                if isinstance(m, dict):
                    prompt_str += m.get("content", "") + "\n"
                elif hasattr(m, "content"):
                    prompt_str += str(m.content) + "\n"
                else:
                    prompt_str += str(m) + "\n"
        else:
            prompt_str = str(messages)

        return self.generate_response(prompt_str)

    def generate_response(self, prompt: str) -> str:
        """
        Generates deterministic ReAct outputs or final answers based on prompt content.
        Safeguards against Pitfall 1 (template collision) and Pitfall 2 (tool name collision).
        """
        # =========================================================================
        # Pitfall 1 Mitigation: ReAct Template Collision
        # Slices off system prompt so template text "Observation: the result of the action"
        # does not cause premature pattern matching in conversation history.
        # =========================================================================
        system_marker = "Observation: the result of the action"
        working_prompt = prompt
        if system_marker in prompt:
            parts = prompt.split(system_marker, 1)
            working_prompt = parts[1] if len(parts) > 1 else prompt

        # Check if an observation has already been provided in the dialogue turn
        has_recent_observation = "Observation:" in working_prompt

        # Order ID Pattern (e.g., NYK-1002)
        order_id_match = re.search(r'\b(NYK-\d{4})\b', prompt, re.IGNORECASE)

        # =========================================================================
        # Scenario A: Order Status Lookup (Handled by Lookup Agent)
        # =========================================================================
        if order_id_match:
            record_id = order_id_match.group(1).upper()

            if not has_recent_observation:
                # Pitfall 2 Mitigation: Explicit schema-based tool routing
                return (
                    f"Thought: The user is requesting order details for {record_id}. "
                    f"I must invoke the order status tool.\n"
                    f"Action: check_order_status\n"
                    f"Action Input: {{\"record_id\": \"{record_id}\"}}"
                )
            else:
                return (
                    f"Thought: I have received the order status observation from the system.\n"
                    f"Final Answer: Nykaa Order {record_id} has been retrieved successfully. "
                    f"All order lifecycle details and escalation parameters have been calculated."
                )

        # =========================================================================
        # Scenario B: Policy Query (Handled by Retrieval Agent)
        # =========================================================================
        if not has_recent_observation:
            # First turn: trigger policy RAG search
            cleaned_q = prompt.splitlines()[-1].strip()
            return (
                f"Thought: The customer is asking a policy question. I need to search the Nykaa policy base.\n"
                f"Action: policy_rag_search\n"
                f"Action Input: {{\"query\": \"{cleaned_q}\"}}"
            )
        else:
            return (
                f"Thought: I have the policy context from the knowledge base.\n"
                f"Final Answer: According to official Nykaa policy, all relevant terms and procedures have been verified."
            )
