"""
app/models.py - Standardized Pydantic Schemas and Contracts
Track: E-Commerce & Retail (Nykaa)
"""

from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field


class AskRequest(BaseModel):
    """Input payload for POST /ask."""
    query: str = Field(..., min_length=1, description="Customer inquiry or order tracking prompt")
    session_id: Optional[str] = Field("default", description="Conversational session identifier")


class AddDocumentRequest(BaseModel):
    """Input payload for POST /add-document."""
    doc_id: str = Field(..., description="Unique policy document identifier")
    text: str = Field(..., description="Authoritative policy markdown content")


class OrderModel(BaseModel):
    """Represents a Nykaa order in transactional database."""
    record_id: str
    category: str
    status: str
    order_value_inr: float
    days_since_created: int
    delayed_shipment: bool


class NykaaAgentResponse(BaseModel):
    """Task 9: Canonical Pydantic output schema for all Nykaa agent interactions."""
    query: str
    resolution_status: Literal["RESOLVED", "ESCALATED", "FALLBACK_TRIGGERED"]
    answer: str
    retrieved_sources: List[str] = Field(default_factory=list)
    order_details: Optional[Dict[str, Any]] = None
    escalation_triggered: bool = False


class ReviewVerdict(BaseModel):
    """Task 14: AutoGen review team structured messaging schema."""
    approved: bool
    final_answer: str
    reason: str


class TelemetryEntry(BaseModel):
    """ELK-compatible structured log entry."""
    timestamp: str
    trace_id: str
    endpoint: str
    duration_ms: float
    sanitized_query: str
    status_code: int
