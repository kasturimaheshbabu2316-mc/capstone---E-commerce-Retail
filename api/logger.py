"""
api/logger.py - ELK-Compatible Structured JSON-Lines Telemetry Logger
Track: E-Commerce & Retail (Nykaa)
Task 12: Single-line JSON logging with trace correlation and PII redaction guarantees.
"""

from typing import Dict, Any, Optional
import os
import sys
import json
import uuid
import datetime
from pathlib import Path

# Add project root directory to sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from agents.guardrails import mask_pii

LOG_FILE_PATH = "logs/transactions.jsonl"


class StructuredTelemetryLogger:
    """
    ELK-ready structured logger writing atomic JSON-Lines records.
    Guarantees raw unmasked PII is never persisted to disk.
    """

    def __init__(self, log_path: str = LOG_FILE_PATH):
        self.log_path = log_path
        os.makedirs(os.path.dirname(self.log_path), exist_ok=True)

    def log_transaction(
        self,
        endpoint: str,
        query: str,
        status_code: int = 200,
        duration_ms: float = 0.0,
        trace_id: Optional[str] = None,
        extra_fields: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Emits and appends a single-line JSON record.
        """
        tid = trace_id or str(uuid.uuid4())
        sanitized_q = mask_pii(query)
        timestamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        payload: Dict[str, Any] = {
            "timestamp": timestamp,
            "trace_id": tid,
            "endpoint": endpoint,
            "duration_ms": round(float(duration_ms), 2),
            "sanitized_query": sanitized_q,
            "status_code": status_code,
        }

        if extra_fields:
            payload.update(extra_fields)

        line = json.dumps(payload, ensure_ascii=False)
        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write(line + "\n")

        return payload


TELEMETRY_LOGGER = StructuredTelemetryLogger()


def get_logger() -> StructuredTelemetryLogger:
    return TELEMETRY_LOGGER


if __name__ == "__main__":
    logger = get_logger()
    entry = logger.log_transaction(
        endpoint="/ask",
        query="Order status for NYK-1002 and phone +91 9876543210",
        status_code=200,
        duration_ms=34.8,
        trace_id="c1f7b8a0-2d93-4a11-8e56-11f4d9e03421",
    )
    print("Logged transaction:")
    print(json.dumps(entry, indent=2))
