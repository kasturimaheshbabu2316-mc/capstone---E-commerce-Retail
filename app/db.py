"""
app/db.py - Data Access Layer & Vector Store Integration
Track: E-Commerce & Retail (Nykaa)
"""

from typing import List, Dict, Any, Optional
import os
import sys
from pathlib import Path

# Add project root directory to sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from dataset import (
    ORDERS,
    ORDERS_BY_ID,
    compute_escalation_score,
    check_order_status,
    CATEGORIES,
    ORDER_STATUSES,
)
from rag.indexer import get_vector_store, ChromaPolicyStore
from rag.chunking import load_knowledge_base_documents


def get_all_orders() -> List[Dict[str, Any]]:
    """Returns the full collection of seeded orders."""
    return ORDERS


def get_order_by_id(record_id: str) -> Optional[Dict[str, Any]]:
    """O(1) transactional lookup for order records."""
    return ORDERS_BY_ID.get(record_id.strip().upper())


def query_vector_policies(query_text: str, top_k: int = 3, strategy: str = "sentence") -> List[Dict[str, Any]]:
    """Queries indexed ChromaDB collections for grounded policy context."""
    store = get_vector_store()
    return store.query(query_text=query_text, collection_type=strategy, top_k=top_k)


def ingest_policy_document(doc_id: str, content: str) -> Dict[str, int]:
    """Ingests a new policy document into dual vector indices."""
    store = get_vector_store()
    return store.add_document(doc_id=doc_id, text=content)


if __name__ == "__main__":
    print(f"app.db: Loaded {len(ORDERS)} seeded orders.")
    sample = check_order_status("NYK-1002")
    print(f"Sample order NYK-1002: Status={sample['status']}, S_esc={sample['escalation_score']}")
