# Enterprise Domain Support Agent for E-Commerce (Nykaa Track)

An enterprise-grade, deterministic Domain Support Agent tailored to high-volume e-commerce and retail operations (Nykaa). The platform is engineered to resolve policy and transactional customer inquiries with low latency, zero external network egress, strict Least-Autonomy role segregation, and an automated LLM-as-a-judge evaluation suite.

---

## 1. System Architecture

```text
[ Incoming Customer Request ]
                               │
                               ▼
   ┌────────────────────────────────────────────────────────┐
   │          Layer 1: Edge Guardrails & Caching            │
   │  - Inbound PII Masking (Phone: +91, Card Last-4)       │
   │  - Heuristic Prompt-Injection Detection                │
   │  - Runtime Token/Cost Budget Enforcement (<= 500 tok)  │
   │  - Normalized In-Memory Idempotent Response Cache      │
   └───────────────────────────┬────────────────────────────┘
                               │ (Cache Miss)
                               ▼
   ┌────────────────────────────────────────────────────────┐
   │           Layer 2: CrewAI Multi-Agent Core             │
   │  ┌──────────────────────────────────────────────────┐  │
   │  │ Retrieval Agent                                  │  │
   │  │ - Embeddings: SentenceTransformers / Local Hash  │  │
   │  │ - Vector Store: ChromaDB Dual Collections        │  │
   │  │ - Tool: policy_rag_search                        │  │
   │  └──────────────────────────┬───────────────────────┘  │
   │                             │                          │
   │  ┌──────────────────────────┴───────────────────────┐  │
   │  │ Lookup Agent (Principle of Least Autonomy)       │  │
   │  │ - Tool: check_order_status (Exclusively Wired)   │  │
   │  │ - Parametric Escalation Score Engine (S_esc)     │  │
   │  └──────────────────────────┬───────────────────────┘  │
   │                             │                          │
   │  ┌──────────────────────────┴───────────────────────┐  │
   │  │ Response Composer Agent                          │  │
   │  │ - Multi-Turn Session Memory (LangChain Memory)   │  │
   │  │ - Structured Output Schema: NykaaAgentResponse   │  │
   │  └──────────────────────────┬───────────────────────┘  │
   └─────────────────────────────┼──────────────────────────┘
                                 │ [Draft Answer + Context]
                                 ▼
   ┌────────────────────────────────────────────────────────┐
   │      Layer 3: AutoGen Multi-Agent Review Stage         │
   │  - Policy-Compliance-Reviewer Agent                    │
   │  - Final-Editor Agent (Structured ReviewVerdict)       │
   │  - Dual Evaluation: Clean Approval vs Active Revision  │
   └─────────────────────────────┬──────────────────────────┘
                                 │
                                 ▼
   ┌────────────────────────────────────────────────────────┐
   │        Layer 4: Serving & Observability Layer          │
   │  - Output Groundedness Fallback Gatekeeper             │
   │  - FastAPI Endpoints (POST /ask, POST /add-doc, WS)    │
   │  - Redacted ELK JSON-Lines Telemetry (Trace ID)        │
   └────────────────────────────────────────────────────────┘
```

---

## 2. 100-Mark Deliverables & Tasks Overview

| Component | Marks | Key Modules | Deliverables & Verification Criteria |
| :--- | :---: | :--- | :--- |
| **Part 1: Dataset & RAG Core** | **30** | `dataset.py`<br>`knowledge_base/`<br>`rag/chunking.py`<br>`rag/indexer.py`<br>`rag/evaluation.py` | Seeded 45 orders (`seed=42`); 13.33% delay proportion (strictly within $10\%\text{--}30\%$); 12 Nykaa policy markdown docs; dual ChromaDB collections (Fixed 150/30 vs Sentence-boundary); calibrated threshold $\tau = 0.2021$; parent-doc Precision & Recall metrics. |
| **Part 2: CrewAI Orchestration** | **30** | `agents/mock_llm.py`<br>`agents/tools.py`<br>`agents/crew.py`<br>`agents/memory.py`<br>`agents/guardrails.py`<br>`api/schemas.py` | Continuous escalation index $S_{\text{esc}} \ge 0.65$; 3 specialized CrewAI agents with Least Autonomy role checks; multi-turn memory continuity and uninitialized session isolation; Pydantic validation; Indian phone (+91) & card last-4 masking; prompt injection defense. |
| **Part 3: Evaluation & Serving** | **20** | `api/server.py`<br>`api/logger.py`<br>`evaluation/test_suite.py`<br>`evaluation/run_judge.py` | FastAPI production server with `POST /ask`, `POST /add-document`, and duplex `WebSocket /ws/chat`; ELK-compliant masked `.jsonl` logging; 15-query LLM-as-a-judge scoring across Accuracy, Grounding, Completeness, Safety (Mean Composite: 0.9365). |
| **Part 4: Resilience & Governance** | **20** | `autogen_review/review_team.py`<br>`governance/risk_budget.py`<br>`governance/cache.py` | AutoGen 2-turn `RoundRobinGroupChat` with Clean Approval and Active Revision cases; Least Autonomy programmatic block; Medium Risk governance documentation; token cap ($>500$ tokens $\to$ 429); normalized query cache with $>4500\times$ speedup. |

---

## 3. Directory Layout

```text
nykaa-support-agent/
├── README.md                      # Comprehensive project documentation (this document)
├── doc/
│   └── problemStatement.md        # Formatted project specification & checklist
├── requirements.txt               # Pinned dependencies (ChromaDB, CrewAI, AutoGen, FastAPI)
├── dataset.py                     # Seeded synthetic order generator with escalation scoring
├── knowledge_base/                # 12 authoritative Nykaa policy Markdown files
│   ├── 01_return_window.md
│   ├── 02_cod_refund.md
│   ├── 03_delivery_sla.md
│   ├── 04_reverse_pickup.md
│   ├── 05_warranty_terms.md
│   ├── 06_order_cancellation.md
│   ├── 07_loyalty_prive.md
│   ├── 08_payment_failure.md
│   ├── 09_size_exchange.md
│   ├── 10_damaged_tampered.md
│   ├── 11_international_shipping.md
│   └── 12_escalation_matrix.md
├── rag/
│   ├── chunking.py                # Fixed-size (150/30) vs sentence-boundary splitters
│   ├── indexer.py                 # Dual ChromaDB indexing & deterministic local embeddings
│   └── evaluation.py              # Empirical threshold calibration & PR benchmarking
├── agents/
│   ├── mock_llm.py                # Offline BaseLLM implementation with pitfall mitigations
│   ├── tools.py                   # Order status & policy RAG tools with Least Autonomy checks
│   ├── crew.py                    # CrewAI 3-agent orchestration pipeline
│   ├── memory.py                  # LangChain in-memory multi-turn session manager
│   ├── guardrails.py              # PII regex masking & prompt injection interceptor
│   └── schemas.py                 # Re-exported Pydantic request and response models
├── autogen_review/
│   └── review_team.py             # AutoGen round-robin review team (Approval & Revision)
├── api/
│   ├── server.py                  # FastAPI REST and WebSocket application
│   ├── schemas.py                 # Pydantic input and output contracts (NykaaAgentResponse)
│   └── logger.py                  # ELK-formatted redacted JSON-Lines telemetry
├── app/                           # Unified Application Package
│   ├── __init__.py                # Package root exports
│   ├── db.py                      # Data access layer & ChromaDB bridge
│   ├── main.py                    # FastAPI server entrypoint
│   ├── memory.py                  # Conversational session memory
│   ├── models.py                  # Pydantic data schemas
│   ├── pipeline.py                # Multi-agent execution pipeline
│   └── tools.py                   # Domain tools and defensive guardrails
├── governance/
│   ├── risk_budget.py             # Runtime token budget & Least Autonomy validator
│   └── cache.py                   # Normalized query in-memory response cache
├── evaluation/
│   ├── test_suite.py              # 15 structured evaluation test cases (12 policy + 3 edge)
│   ├── run_judge.py               # Deterministic LLM-as-a-judge scoring script
│   └── results.json               # Full itemized evaluation results
├── logs/
│   └── transactions.jsonl         # Redacted structured transaction logs
└── transcripts/                   # Validation run logs for all tasks
    ├── task_01_dataset.txt
    ├── task_04_threshold.txt
    ├── task_05_pr_metrics.txt
    ├── task_07_crew_execution.txt
    ├── task_08_memory_session.txt
    ├── task_10_guardrails.txt
    ├── task_13_eval_matrix.txt
    ├── task_14_autogen_review.txt
    └── task_16_cache_metrics.txt
```

---

## 4. Quickstart & Verification Commands

Activate the virtual environment:
```powershell
.\.e-commerce\Scripts\activate.ps1
```

Run all task verification scripts to regenerate verification transcripts:

```powershell
# Part 1: Dataset & RAG Core
python dataset.py
python rag/evaluation.py

# Part 2: CrewAI Orchestration, Guardrails & Memory
python agents/guardrails.py
python agents/memory.py
python agents/crew.py

# Part 4: AutoGen Review & Governance Caching
python autogen_review/review_team.py
python governance/cache.py

# Part 3: LLM-as-a-Judge Evaluation Suite
python evaluation/run_judge.py
```

---

## 5. Running the FastAPI Server

Start the server locally:
```powershell
python -m uvicorn api.server:app --host 127.0.0.1 --port 8000
```

### Endpoints
1. **`POST /ask`**
   ```bash
   curl -X POST http://127.0.0.1:8000/ask \
     -H "Content-Type: application/json" \
     -d '{"query": "What is the return window for sealed beauty cosmetics?"}'
   ```
2. **`POST /add-document`**
   ```bash
   curl -X POST http://127.0.0.1:8000/add-document \
     -H "Content-Type: application/json" \
     -d '{"doc_id": "13_vip_club", "text": "Nykaa VIP members receive complimentary priority shipping."}'
   ```
3. **`WebSocket /ws/chat`**
   Connect using any standard WebSocket client to `ws://127.0.0.1:8000/ws/chat`. Graceful disconnections (`1000`) are captured without server crashes.

---

## 6. Implementation Guardrails & Known Pitfalls Addressed

1. **System Prompt Template Collision**: CrewAI's default ReAct prompt contains `"Observation: the result of the action"`. In `agents/mock_llm.py`, conversation history is parsed exclusively from generated model outputs to prevent premature stops.
2. **Schema-Driven Tool Dispatch**: Tool executions evaluate strict parameter schemas rather than matching substring patterns in tool names.
3. **Structured AutoGen Registration**: Handled via `StructuredMessage[ReviewVerdict]` contracts to prevent message registration crashes.
4. **Zero Outbound Network Egress**: Runs 100% offline using local deterministic embeddings, ChromaDB, and `MOCK_LLM`.
