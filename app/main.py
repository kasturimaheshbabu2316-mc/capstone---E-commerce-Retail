"""
app/main.py - Production FastAPI Application Gateway
Track: E-Commerce & Retail (Nykaa)
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

from app.models import AskRequest, AddDocumentRequest, NykaaAgentResponse
from app.pipeline import get_support_pipeline
from app.db import ingest_policy_document, get_vector_store
from api.logger import get_logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure vector indices are warm on server startup
    store = get_vector_store()
    store.index_all()
    yield


app = FastAPI(
    title="Nykaa Domain Support Agent",
    description="Enterprise Multi-Agent Domain Support Platform for Nykaa E-Commerce",
    version="1.0.0",
    lifespan=lifespan,
)

pipeline_service = get_support_pipeline()
logger_service = get_logger()


@app.post("/ask", response_model=NykaaAgentResponse)
async def ask_endpoint(payload: AskRequest):
    """
    POST /ask: Primary customer-facing support query endpoint.
    Orchestration: Runtime Budget -> Input Guardrail -> Cache -> CrewAI -> AutoGen Review -> Audit Log.
    """
    raw_query = payload.query
    session_id = payload.session_id or "default"

    response, duration_ms, is_hit, trace_id = pipeline_service.execute(
        query=raw_query, session_id=session_id
    )

    # Check for budget breach or injection rejection error response
    if "HTTP 429" in response.answer:
        logger_service.log_transaction(
            endpoint="/ask",
            query=raw_query,
            status_code=429,
            duration_ms=duration_ms,
            trace_id=trace_id,
        )
        raise HTTPException(status_code=429, detail=response.answer)

    if "blocked by guardrails" in response.answer:
        logger_service.log_transaction(
            endpoint="/ask",
            query=raw_query,
            status_code=400,
            duration_ms=duration_ms,
            trace_id=trace_id,
        )
        raise HTTPException(status_code=400, detail=response.answer)

    # Emit ELK-compliant structured log
    logger_service.log_transaction(
        endpoint="/ask",
        query=raw_query,
        status_code=200,
        duration_ms=duration_ms,
        trace_id=trace_id,
        extra_fields={"cache_hit": is_hit},
    )

    return response


@app.post("/add-document")
async def add_document_endpoint(payload: AddDocumentRequest):
    """
    POST /add-document: Incremental knowledge-base ingestion endpoint.
    """
    counts = ingest_policy_document(doc_id=payload.doc_id, content=payload.text)
    return {
        "status": "INGESTED",
        "doc_id": payload.doc_id,
        "fixed_chunks_added": counts["fixed_chunks_added"],
        "sentence_chunks_added": counts["sentence_chunks_added"],
        "message": f"Policy document '{payload.doc_id}' successfully indexed into ChromaDB collections.",
    }


@app.websocket("/ws/chat")
async def websocket_chat_endpoint(websocket: WebSocket):
    """
    WebSocket /ws/chat: Real-time bidirectional streaming chat interface.
    Handles multi-turn memory and catches WebSocketDisconnect gracefully.
    """
    await websocket.accept()
    ws_session_id = f"ws_{uuid.uuid4().hex[:8]}"

    try:
        while True:
            text_data = await websocket.receive_text()
            response, duration_ms, is_hit, trace_id = pipeline_service.execute(
                query=text_data, session_id=ws_session_id
            )

            logger_service.log_transaction(
                endpoint="/ws/chat",
                query=text_data,
                status_code=200,
                duration_ms=duration_ms,
                trace_id=trace_id,
                extra_fields={"cache_hit": is_hit},
            )

            await websocket.send_json(response.model_dump())

    except WebSocketDisconnect:
        logger_service.log_transaction(
            endpoint="/ws/chat",
            query=f"Session {ws_session_id} disconnected cleanly.",
            status_code=1000,
            duration_ms=0.0,
        )
    except Exception as e:
        await websocket.close()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=False)
