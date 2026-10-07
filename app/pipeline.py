"""
app/pipeline.py - Multi-Agent Orchestration & Execution Pipeline
Track: E-Commerce & Retail (Nykaa)
"""

from typing import Dict, Any, Optional, Tuple
import os
import sys
import time
import uuid
from pathlib import Path

# Add project root directory to sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.models import NykaaAgentResponse, ReviewVerdict
from app.tools import apply_input_guardrails
from agents.crew import NykaaSupportCrew
from agents.mock_llm import MockLLM
from autogen_review.review_team import get_review_team, AutoGenReviewTeam
from governance.risk_budget import enforce_runtime_budget, BudgetExceededError
from governance.cache import get_query_cache, NormalizedQueryCache


class NykaaSupportPipeline:
    """
    Unified end-to-end multi-agent support execution pipeline:
    1. Runtime Token Budget Guard (<= 500 simulated tokens)
    2. Inbound Defensive Guardrails (PII masking & prompt injection defense)
    3. Normalized In-Memory Query Response Cache (idempotent sub-millisecond return)
    4. CrewAI 3-Agent Core with Least Autonomy (Retrieval, Lookup, Composer)
    5. AutoGen 2-Agent Secondary Compliance & Editorial Review
    6. Cache Storage & Latency Instrumentation
    """

    def __init__(self):
        self.crew = NykaaSupportCrew()
        self.reviewer = get_review_team()
        self.cache = get_query_cache()

    def execute(
        self, query: str, session_id: str = "default"
    ) -> Tuple[NykaaAgentResponse, float, bool, str]:
        """
        Executes query through all enterprise governance and orchestration stages.
        Returns: (response, duration_ms, is_cache_hit, trace_id)
        """
        t0 = time.perf_counter()
        trace_id = str(uuid.uuid4())

        # Stage 1: Runtime Token Budget Guard
        in_budget, _, budget_msg = enforce_runtime_budget(query)
        if not in_budget:
            duration_ms = (time.perf_counter() - t0) * 1000
            err_resp = NykaaAgentResponse(
                query=query,
                resolution_status="FALLBACK_TRIGGERED",
                answer=budget_msg,
                retrieved_sources=[],
                order_details=None,
                escalation_triggered=False,
            )
            return err_resp, duration_ms, False, trace_id

        # Stage 2: Inbound Defensive Guardrails
        guard = apply_input_guardrails(query)
        if not guard["allowed"]:
            duration_ms = (time.perf_counter() - t0) * 1000
            err_resp = NykaaAgentResponse(
                query=query,
                resolution_status="FALLBACK_TRIGGERED",
                answer=f"Request blocked by guardrails: {guard['error']}",
                retrieved_sources=[],
                order_details=None,
                escalation_triggered=False,
            )
            return err_resp, duration_ms, False, trace_id

        sanitized_query = guard["sanitized_query"]

        # Stage 3: Normalized Query Response Cache
        cached_val = self.cache.get(sanitized_query)
        if cached_val is not None:
            duration_ms = (time.perf_counter() - t0) * 1000
            return cached_val, duration_ms, True, trace_id

        # Stage 4: CrewAI Primary Multi-Agent Orchestration
        crew_draft = self.crew.run_pipeline(sanitized_query, session_id=session_id)

        # Stage 5: AutoGen Secondary Peer Review
        verdict = self.reviewer.review_draft(crew_draft)
        final_answer = verdict.final_answer

        final_response = NykaaAgentResponse(
            query=query,
            resolution_status=crew_draft.resolution_status,
            answer=final_answer,
            retrieved_sources=crew_draft.retrieved_sources,
            order_details=crew_draft.order_details,
            escalation_triggered=crew_draft.escalation_triggered,
        )

        # Stage 6: Update cache on miss
        self.cache.set(sanitized_query, final_response)
        duration_ms = (time.perf_counter() - t0) * 1000

        return final_response, duration_ms, False, trace_id


_GLOBAL_PIPELINE: Optional[NykaaSupportPipeline] = None


def get_support_pipeline() -> NykaaSupportPipeline:
    global _GLOBAL_PIPELINE
    if _GLOBAL_PIPELINE is None:
        _GLOBAL_PIPELINE = NykaaSupportPipeline()
    return _GLOBAL_PIPELINE


if __name__ == "__main__":
    pipeline = get_support_pipeline()
    resp, latency, hit, tid = pipeline.execute("What is the return window for cosmetics?")
    print(f"Pipeline executed in {latency:.2f}ms | CacheHit={hit} | Status={resp.resolution_status}")
    print(f"Answer: {resp.answer[:80]}...")
