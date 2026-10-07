"""
api/server.py - Production FastAPI Gateway
Track: E-Commerce & Retail (Nykaa)
Task 11: Production Serving with REST (/ask, /add-document) and WebSocket (/ws/chat).
"""

from typing import Dict, Any, Optional
import time
import uuid
import sys
from pathlib import Path
from contextlib import asynccontextmanager

# Add project root directory to sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse

from api.schemas import AskRequest, AddDocumentRequest, NykaaAgentResponse
from api.logger import get_logger
from agents.crew import NykaaSupportCrew
from agents.guardrails import apply_input_guardrails, validate_groundedness
from autogen_review.review_team import get_review_team
from governance.risk_budget import enforce_runtime_budget
from governance.cache import get_query_cache
from rag.indexer import get_vector_store


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure vector store is initialized on startup
    store = get_vector_store()
    store.index_all()
    yield


app = FastAPI(
    title="Nykaa Domain Support Agent API",
    description="Enterprise Multi-Agent Domain Support Service for Nykaa E-Commerce",
    version="1.0.0",
    lifespan=lifespan,
)

# Global service singletons
crew_service = NykaaSupportCrew()
reviewer_service = get_review_team()
logger_service = get_logger()
cache_service = get_query_cache()


@app.post("/ask", response_model=NykaaAgentResponse)
async def ask_endpoint(payload: AskRequest):
    """
    POST /ask: Primary customer-facing support query endpoint.
    Orchestration: Runtime Budget -> Input Guardrail -> Cache -> CrewAI -> AutoGen Review -> Audit Log.
    """
    t0 = time.perf_counter()
    trace_id = str(uuid.uuid4())
    raw_query = payload.query
    session_id = payload.session_id or "default"

    # Step 1: Runtime Token Budget Guard (Task 15)
    in_budget, token_count, budget_msg = enforce_runtime_budget(raw_query)
    if not in_budget:
        duration_ms = (time.perf_counter() - t0) * 1000
        logger_service.log_transaction(
            endpoint="/ask",
            query=raw_query,
            status_code=429,
            duration_ms=duration_ms,
            trace_id=trace_id,
        )
        raise HTTPException(status_code=429, detail=budget_msg)

    # Step 2: Inbound Defensive Guardrails (Task 10)
    guard = apply_input_guardrails(raw_query)
    if not guard["allowed"]:
        duration_ms = (time.perf_counter() - t0) * 1000
        logger_service.log_transaction(
            endpoint="/ask",
            query=raw_query,
            status_code=400,
            duration_ms=duration_ms,
            trace_id=trace_id,
        )
        raise HTTPException(status_code=400, detail=guard["error"])

    sanitized_q = guard["sanitized_query"]

    # Step 3: Normalized Query Response Cache (Task 16)
    cached = cache_service.get(sanitized_q)
    if cached is not None:
        duration_ms = (time.perf_counter() - t0) * 1000
        logger_service.log_transaction(
            endpoint="/ask",
            query=sanitized_q,
            status_code=200,
            duration_ms=duration_ms,
            trace_id=trace_id,
            extra_fields={"cache_hit": True},
        )
        return cached

    # Step 4: CrewAI Multi-Agent Execution (Task 7)
    crew_draft = crew_service.run_pipeline(sanitized_q, session_id=session_id)

    # Step 5: AutoGen Secondary Multi-Agent Review (Task 14)
    verdict = reviewer_service.review_draft(crew_draft)
    final_answer = verdict.final_answer

    final_response = NykaaAgentResponse(
        query=raw_query,
        resolution_status=crew_draft.resolution_status,
        answer=final_answer,
        retrieved_sources=crew_draft.retrieved_sources,
        order_details=crew_draft.order_details,
        escalation_triggered=crew_draft.escalation_triggered,
    )

    # Cache successful response
    cache_service.set(sanitized_q, final_response)

    # Step 6: ELK Structured Logging (Task 12)
    duration_ms = (time.perf_counter() - t0) * 1000
    logger_service.log_transaction(
        endpoint="/ask",
        query=sanitized_q,
        status_code=200,
        duration_ms=duration_ms,
        trace_id=trace_id,
        extra_fields={"cache_hit": False, "approved": verdict.approved},
    )

    return final_response


@app.post("/add-document")
async def add_document_endpoint(payload: AddDocumentRequest):
    """
    POST /add-document: Incremental knowledge-base ingestion endpoint.
    Indexes incoming text into both fixed and sentence ChromaDB collections.
    """
    store = get_vector_store()
    counts = store.add_document(doc_id=payload.doc_id, text=payload.text)

    return {
        "status": "INGESTED",
        "doc_id": payload.doc_id,
        "fixed_chunks_added": counts["fixed_chunks_added"],
        "sentence_chunks_added": counts["sentence_chunks_added"],
        "message": f"Policy document '{payload.doc_id}' successfully indexed.",
    }


@app.websocket("/ws/chat")
async def websocket_chat_endpoint(websocket: WebSocket):
    """
    WebSocket /ws/chat: Real-time bidirectional chat interface.
    Handles multi-turn memory and catches WebSocketDisconnect gracefully.
    """
    await websocket.accept()
    ws_session_id = f"ws_{uuid.uuid4().hex[:8]}"

    try:
        while True:
            text_data = await websocket.receive_text()
            t0 = time.perf_counter()

            # Budget check
            in_budget, _, budget_msg = enforce_runtime_budget(text_data)
            if not in_budget:
                await websocket.send_json({"error": budget_msg, "status_code": 429})
                continue

            # Inbound Guardrails
            guard = apply_input_guardrails(text_data)
            if not guard["allowed"]:
                await websocket.send_json({"error": guard["error"], "status_code": 400})
                continue

            sanitized_q = guard["sanitized_query"]

            # Pipeline execution
            response = crew_service.run_pipeline(sanitized_q, session_id=ws_session_id)
            duration_ms = (time.perf_counter() - t0) * 1000

            logger_service.log_transaction(
                endpoint="/ws/chat",
                query=sanitized_q,
                status_code=200,
                duration_ms=duration_ms,
            )

            await websocket.send_json(response.model_dump())

    except WebSocketDisconnect:
        # Graceful disconnection handling per Task 11 specification
        logger_service.log_transaction(
            endpoint="/ws/chat",
            query=f"Session {ws_session_id} disconnected gracefully.",
            status_code=1000,
            duration_ms=0.0,
        )
    except Exception as e:
        await websocket.close()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api.server:app", host="127.0.0.1", port=8000, reload=False)
