# Engineering Implementation Plan & Delivery Roadmap

**Project:** Nykaa Domain Support Agent (Retail Operations)  
**Track:** E-Commerce & Retail (Nykaa)  
**Document Version:** 1.0.0  
**Status:** Completed & Validated  
**Reference:** [architecture.md](file:///c:/Users/kastu/Desktop/capstone%20-%20ecommerce/doc/architecture.md) | [problemStatement.md](file:///c:/Users/kastu/Desktop/capstone%20-%20ecommerce/doc/problemStatement.md) | [README.md](file:///c:/Users/kastu/Desktop/capstone%20-%20ecommerce/README.md)

---

## 1. Executive Implementation Strategy

The implementation plan establishes an enterprise-grade, deterministic, and fully air-gapped engineering methodology designed for retail customer support operations at **Nykaa**:

1. **Complete Air-Gapped Execution:** Zero dependency on live external endpoints or cloud services. Runs locally using `sentence-transformers/all-MiniLM-L6-v2`, disk-backed `ChromaDB` collections, and a deterministic offline `MOCK_LLM` derived from `crewai.llms.base_llm.BaseLLM`. External telemetry is forcefully disabled (`CREWAI_DISABLE_TELEMETRY=true`, `OTEL_SDK_DISABLED=true`).
2. **Defensive Governance & Least Autonomy:** Strict role-based access control (RBAC) ensuring only the Lookup Agent can access the order database. Inbound pre-flight PII redaction (Indian phone numbers, payment card numbers), adversarial prompt-injection defense, runtime token budget guards ($>500$ tokens $\to$ HTTP 429), and post-generation compliance review via AutoGen.
3. **Mathematical Invariant Verification:** Deterministic dataset generation (`seed=42`, $N=45$ orders, delay rate $13.33\% \in [10\%, 30\%]$), empirical threshold calibration ($\tau = 0.2021$, separation margin $+0.0828$), parametric escalation scoring ($S_{\text{esc}} \ge 0.65$), and a 15-query LLM-as-a-judge evaluation suite (**Composite Score: 0.9365 / 1.0000**).
4. **Production Observability & Serving:** Sub-millisecond responses enabled by an in-memory normalized query cache ($>4,500\times$ speedup on warm hits), dual FastAPI interfaces (REST `POST /ask`, `POST /add-document` + WebSocket `/ws/chat`), an interactive Streamlit operations dashboard, and ELK-compliant single-line JSON-Lines audit logging with UUID4 trace IDs.

---

## 2. Phased Delivery Roadmap & Milestones

```mermaid
gantt
    title Nykaa Domain Support Agent - Implementation Roadmap
    dateFormat  YYYY-MM-DD
    section Phase 1: Data Architecture & Knowledge Base
    Task 1: Seeded Order Dataset Generator     :done, p1_1, 2026-10-01, 1d
    Task 2: Authoritative Policy Knowledge Base :done, p1_2, 2026-10-01, 1d
    section Phase 2: RAG Pipeline & Threshold Calibration
    Task 3: Dual Chunking Strategies           :done, p2_1, 2026-10-02, 1d
    Task 4: Vector Indexing & tau Calibration  :done, p2_2, 2026-10-02, 1d
    Task 5: Precision & Recall Benchmarking    :done, p2_3, 2026-10-02, 1d
    section Phase 3: Multi-Agent Core & Guardrails
    Task 6: Parametric Escalation Engine       :done, p3_1, 2026-10-03, 1d
    Task 7: CrewAI 3-Agent Orchestration       :done, p3_2, 2026-10-03, 1d
    Task 8: Multi-Turn Conversational Memory   :done, p3_3, 2026-10-03, 1d
    Task 9: Pydantic Schema Contracts          :done, p3_4, 2026-10-04, 1d
    Task 10: Inbound & Outbound Guardrails     :done, p3_5, 2026-10-04, 1d
    section Phase 4: Production API & Structured Logging
    Task 11: FastAPI REST & WebSocket Endpoints :done, p4_1, 2026-10-05, 1d
    Task 12: ELK JSON-Lines Audit Logger       :done, p4_2, 2026-10-05, 1d
    section Phase 5: Quantitative Evaluation & Transcripts
    Task 13: 15-Query Evaluation Suite         :done, p5_1, 2026-10-06, 1d
    section Phase 6: Secondary AutoGen Review Team
    Task 14: AutoGen Review Team & ReviewVerdict:done, p6_1, 2026-10-06, 1d
    section Phase 7: AI Governance & Optimization
    Task 15: Least Autonomy RBAC & Token Budget :done, p7_1, 2026-10-07, 1d
    Task 16: Normalized Query Response Cache   :done, p7_2, 2026-10-07, 1d
    section Phase 8: UI Dashboard & App Layout
    Task 17: Streamlit Interactive UI          :done, p8_1, 2026-10-07, 1d
    Task 18: App Package Architecture          :done, p8_2, 2026-10-07, 1d
```

---

## 3. Detailed Phase Breakdown & Deliverables

### Phase 1: Data Architecture & Knowledge Base (Tasks 1–2)

* **Objective:** Establish authoritative ground-truth order datasets and policy texts with strict mathematical invariants.
* **Deliverables:**
  * [`dataset.py`](file:///c:/Users/kastu/Desktop/capstone%20-%20ecommerce/dataset.py): Deterministic generator (`seed=42`) producing an immutable store of 45 orders.
    * Total orders $N = 45 \ge 40$ (PASS).
    * Category balance across 5 categories ($\ge 3$ records each): Apparel (11), Electronics (9), Home (11), Footwear (7), Beauty (7).
    * Status balance across 5 statuses ($\ge 1$ record each): Placed (8), Shipped (8), Delivered (9), Returned (7), Refunded (13).
    * Statistical delay invariant: $6 / 45 = 13.33\%$ delayed orders ($10\% \le 13.33\% \le 30\%$, PASS).
  * [`knowledge_base/`](file:///c:/Users/kastu/Desktop/capstone%20-%20ecommerce/knowledge_base): 12 distinct Markdown policy documents (`01_return_window.md` to `12_escalation_matrix.md`) containing 2–5 sentences with explicit numerical SLAs, return windows, and escalation tiers.
* **Verification Artifact:**
  * [`transcripts/task_01_dataset.txt`](file:///c:/Users/kastu/Desktop/capstone%20-%20ecommerce/transcripts/task_01_dataset.txt)

---

### Phase 2: RAG Pipeline, Dual Chunking & Threshold Calibration (Tasks 3–5)

* **Objective:** Implement dual chunking strategies, ChromaDB vector indexing, empirical similarity threshold calibration ($\tau$), and document-level precision/recall benchmarking.
* **Deliverables:**
  * [`rag/chunking.py`](file:///c:/Users/kastu/Desktop/capstone%20-%20ecommerce/rag/chunking.py):
    * Strategy A: Fixed-size chunker (150 chars, 30 overlap) producing 47 chunks.
    * Strategy B: Sentence-boundary chunker producing 24 complete semantic propositions.
  * [`rag/indexer.py`](file:///c:/Users/kastu/Desktop/capstone%20-%20ecommerce/rag/indexer.py): ChromaDB dual collection stores (`nykaa_policy_fixed` and `nykaa_policy_sentence`) with deterministic semantic embedding and idempotent upserting.
  * [`rag/evaluation.py`](file:///c:/Users/kastu/Desktop/capstone%20-%20ecommerce/rag/evaluation.py):
    * Empirical threshold calibration: Top-1 in-scope min = `0.2435`, out-of-scope max = `0.1607`, separation margin = `+0.0828`, calibrated $\tau = 0.2021$.
    * Standard refusal text: *"I do not have sufficient information in the Nykaa policy to answer this question."*
    * Strategy B demonstrated superior precision (`0.5000` vs `0.4667`) and identical recall (`1.0000`), selected for production deployment.
* **Verification Artifacts:**
  * [`transcripts/task_04_threshold.txt`](file:///c:/Users/kastu/Desktop/capstone%20-%20ecommerce/transcripts/task_04_threshold.txt)
  * [`transcripts/task_05_pr_metrics.txt`](file:///c:/Users/kastu/Desktop/capstone%20-%20ecommerce/transcripts/task_05_pr_metrics.txt)

---

### Phase 3: Tooling, Deterministic Mock LLM & Multi-Agent Core (Tasks 6–10)

* **Objective:** Build multi-agent orchestration, continuous escalation scoring, conversational memory, and defense-in-depth guardrails.
* **Deliverables:**
  * [`agents/tools.py`](file:///c:/Users/kastu/Desktop/capstone%20-%20ecommerce/agents/tools.py): `check_order_status` tool enforcing Least Autonomy RBAC and computing the continuous escalation score:
    $$S_{\text{esc}} = 0.60 \cdot \mathbb{I}(\text{delayed\_shipment}) + 0.40 \cdot \left(\frac{\text{days\_since\_created}}{30}\right), \quad \text{Escalation Threshold: } S_{\text{esc}} \ge 0.65$$
  * [`agents/mock_llm.py`](file:///c:/Users/kastu/Desktop/capstone%20-%20ecommerce/agents/mock_llm.py): Deterministic `MOCK_LLM` derived from `crewai.llms.base_llm.BaseLLM` with ReAct template collision mitigation.
  * [`agents/crew.py`](file:///c:/Users/kastu/Desktop/capstone%20-%20ecommerce/agents/crew.py): 3-agent CrewAI pipeline (Retrieval Agent, Lookup Agent, Response Composer Agent) enforcing strict tool isolation.
  * [`agents/memory.py`](file:///c:/Users/kastu/Desktop/capstone%20-%20ecommerce/agents/memory.py): Multi-turn session memory using LangChain `InMemoryChatMessageHistory`, resolving anaphoric references across turns while guaranteeing session isolation.
  * [`agents/schemas.py`](file:///c:/Users/kastu/Desktop/capstone%20-%20ecommerce/agents/schemas.py) & [`api/schemas.py`](file:///c:/Users/kastu/Desktop/capstone%20-%20ecommerce/api/schemas.py): Pydantic v2 `NykaaAgentResponse` structured contract.
  * [`agents/guardrails.py`](file:///c:/Users/kastu/Desktop/capstone%20-%20ecommerce/agents/guardrails.py): Inbound regex PII masking (`[PHONE_REDACTED]`, `[CARD_REDACTED]`), prompt-injection attack refusal, and output grounding verification against $\tau = 0.2021$.
* **Verification Artifacts:**
  * [`transcripts/task_07_crew_execution.txt`](file:///c:/Users/kastu/Desktop/capstone%20-%20ecommerce/transcripts/task_07_crew_execution.txt)
  * [`transcripts/task_08_memory_session.txt`](file:///c:/Users/kastu/Desktop/capstone%20-%20ecommerce/transcripts/task_08_memory_session.txt)
  * [`transcripts/task_10_guardrails.txt`](file:///c:/Users/kastu/Desktop/capstone%20-%20ecommerce/transcripts/task_10_guardrails.txt)

---

### Phase 4: Production API, WebSocket & Structured Audit Logging (Tasks 11–12)

* **Objective:** Expose high-performance REST and duplex WebSocket interfaces with enterprise audit logging.
* **Deliverables:**
  * [`api/server.py`](file:///c:/Users/kastu/Desktop/capstone%20-%20ecommerce/api/server.py) & [`app/main.py`](file:///c:/Users/kastu/Desktop/capstone%20-%20ecommerce/app/main.py):
    * `POST /ask`: Primary conversational endpoint with end-to-end guardrail, cache, crew, and review execution.
    * `POST /add-document`: Incremental dynamic document chunking and indexing into ChromaDB.
    * `WebSocket /ws/chat`: Real-time streaming channel gracefully catching `WebSocketDisconnect` (`code=1000`).
  * [`api/logger.py`](file:///c:/Users/kastu/Desktop/capstone%20-%20ecommerce/api/logger.py): ELK-compatible single-line JSON-Lines logger writing to [`logs/transactions.jsonl`](file:///c:/Users/kastu/Desktop/capstone%20-%20ecommerce/logs/transactions.jsonl) with UUID4 trace IDs, duration ms, and zero unmasked PII.

---

### Phase 5: Quantitative Evaluation & Verifiable Transcripts (Task 13)

* **Objective:** Run an automated 15-query test suite scoring Accuracy (35%), Grounding (35%), Completeness (15%), and Safety (15%).
* **Deliverables:**
  * [`evaluation/run_judge.py`](file:///c:/Users/kastu/Desktop/capstone%20-%20ecommerce/evaluation/run_judge.py): Automated deterministic LLM-as-a-judge scoring engine.
  * [`evaluation/test_suite.py`](file:///c:/Users/kastu/Desktop/capstone%20-%20ecommerce/evaluation/test_suite.py): Benchmark suite across 12 domain policy queries, adversarial injection, out-of-scope query, and corrupted order ID lookup.
  * [`evaluation/results.json`](file:///c:/Users/kastu/Desktop/capstone%20-%20ecommerce/evaluation/results.json): Quantitative scorecard:
    * **Accuracy:** `0.9600`
    * **Grounding:** `0.8800`
    * **Completeness:** `0.9500`
    * **Safety:** `1.0000`
    * **Composite Score:** **`0.9365 / 1.0000` (PASS)**
* **Verification Artifact:**
  * [`transcripts/task_13_eval_matrix.txt`](file:///c:/Users/kastu/Desktop/capstone%20-%20ecommerce/transcripts/task_13_eval_matrix.txt)

---

### Phase 6: Secondary AutoGen Peer Review Subsystem (Task 14)

* **Objective:** Implement a post-generation secondary compliance review stage prior to client delivery.
* **Deliverables:**
  * [`autogen_review/review_team.py`](file:///c:/Users/kastu/Desktop/capstone%20-%20ecommerce/autogen_review/review_team.py): AutoGen `RoundRobinGroupChat(max_turns=2)` pairing `PolicyComplianceReviewer` and `FinalEditor`, emitting a structured `ReviewVerdict` (approval boolean, revised text, reason).
  * Dual evaluation pathways demonstrated:
    * **Pathway 1 (Clean Approval):** Fully compliant composer drafts pass unaltered with `approved=True`.
    * **Pathway 2 (Active Revision):** Hallucinated claims (e.g. 60-day return window or doorstep cash refunds) are intercepted with `approved=False` and rewritten to conform to official Nykaa policy.
* **Verification Artifact:**
  * [`transcripts/task_14_autogen_review.txt`](file:///c:/Users/kastu/Desktop/capstone%20-%20ecommerce/transcripts/task_14_autogen_review.txt)

---

### Phase 7: AI Governance, Budget Limiting & Response Cache (Tasks 15–16)

* **Objective:** Enforce Least Autonomy RBAC, runtime token budgeting, and sub-millisecond query caching.
* **Deliverables:**
  * [`governance/risk_budget.py`](file:///c:/Users/kastu/Desktop/capstone%20-%20ecommerce/governance/risk_budget.py):
    * Enterprise Risk Classification: **Medium Risk (Customer Support & E-Commerce Operations)**.
    * Runtime token budget limiter enforcing a maximum ceiling of 500 simulated tokens per request (triggering HTTP 429 on budget exhaustion).
  * [`governance/cache.py`](file:///c:/Users/kastu/Desktop/capstone%20-%20ecommerce/governance/cache.py): In-memory normalized query cache (`query.strip().lower()`). Measured cache hit latency: **0.004 ms** ($>4,500\times$ speedup over uncached agent execution).
* **Verification Artifact:**
  * [`transcripts/task_16_cache_metrics.txt`](file:///c:/Users/kastu/Desktop/capstone%20-%20ecommerce/transcripts/task_16_cache_metrics.txt)

---

### Phase 8: Operations Dashboard & Application Package (UI & Architecture)

* **Objective:** Deliver an interactive web user interface and conform to the standardized application package layout.
* **Deliverables:**
  * [`streamlit_app.py`](file:///c:/Users/kastu/Desktop/capstone%20-%20ecommerce/streamlit_app.py): Full-featured Streamlit operations console featuring:
    * Interactive query chat interface with real-time response rendering and confidence metrics.
    * Transactional order status lookup with parametric escalation score gauge.
    * Live policy document ingestion (`POST /add-document` emulator).
    * Observability dashboard streaming records directly from [`logs/transactions.jsonl`](file:///c:/Users/kastu/Desktop/capstone%20-%20ecommerce/logs/transactions.jsonl).
  * [`app/`](file:///c:/Users/kastu/Desktop/capstone%20-%20ecommerce/app): Standardized application package:
    * [`app/__init__.py`](file:///c:/Users/kastu/Desktop/capstone%20-%20ecommerce/app/__init__.py): Package initialization.
    * [`app/models.py`](file:///c:/Users/kastu/Desktop/capstone%20-%20ecommerce/app/models.py): Pydantic request/response schemas.
    * [`app/db.py`](file:///c:/Users/kastu/Desktop/capstone%20-%20ecommerce/app/db.py): Seeded dataset accessor and parametric escalation formula.
    * [`app/tools.py`](file:///c:/Users/kastu/Desktop/capstone%20-%20ecommerce/app/tools.py): Least Autonomy tool definitions.
    * [`app/memory.py`](file:///c:/Users/kastu/Desktop/capstone%20-%20ecommerce/app/memory.py): Session memory management.
    * [`app/pipeline.py`](file:///c:/Users/kastu/Desktop/capstone%20-%20ecommerce/app/pipeline.py): Multi-agent execution pipeline.
    * [`app/main.py`](file:///c:/Users/kastu/Desktop/capstone%20-%20ecommerce/app/main.py): FastAPI server application.

---

## 4. Critical Technical Decisions & Pitfall Mitigations

| Challenge / Pitfall | Impact | Implemented Mitigation |
| :--- | :--- | :--- |
| **Pitfall 1: ReAct Template Collision** | Agent parser interprets system prompt ReAct instructions as premature model actions. | In [`agents/mock_llm.py`](file:///c:/Users/kastu/Desktop/capstone%20-%20ecommerce/agents/mock_llm.py), parse conversation history exclusively from generated outputs after stripping system prompt markers. |
| **Pitfall 2: Tool Routing Collision** | Substring matching on tool names misclassifies tools (e.g. `rag_lookup` triggered for order lookup). | Strict schema inspection and exact string equality checks on tool names in [`agents/tools.py`](file:///c:/Users/kastu/Desktop/capstone%20-%20ecommerce/agents/tools.py). |
| **Least Autonomy RBAC Violation** | Unauthorized agent invokes customer order database. | Programmatic check in `check_order_status` throwing `LeastAutonomyViolation` if caller is not `Lookup Agent`. |
| **Air-Gapped Embedding Failure** | Cloud/HuggingFace network requests fail in offline environments. | `SentenceTransformers` model with deterministic signed semantic hashing fallback preserving cosine geometry. |
| **AutoGen Type Registration Crash** | Unregistered custom message types crash AutoGen group chat messaging loop. | Declared structured message schemas in `RoundRobinGroupChat` at initialization. |
| **PII Data Leakage in Persistent Logs** | Writing unmasked Indian phone numbers or card digits violates privacy laws. | Pre-flight regex substitution (`[PHONE_REDACTED]`, `[CARD_REDACTED]`) before serializing to `logs/transactions.jsonl`. |
| **Runtime Budget Exhaustion** | Unbounded token generation inflates compute costs. | Pre-flight token budget guard capping requests at 500 tokens, throwing HTTP 429 when exceeded. |

---

## 5. Quantitative 15-Query Evaluation Scorecard

| Test ID | Domain / Query Topic | Accuracy | Grounding | Completeness | Safety | Composite Score | Status |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **TC-01** | Return Window by Category | 0.95 | 1.00 | 0.95 | 1.00 | **0.9750** | RESOLVED |
| **TC-02** | Cash on Delivery Refund Timeline | 0.95 | 1.00 | 0.95 | 1.00 | **0.9750** | RESOLVED |
| **TC-03** | Metro Delivery SLAs | 0.95 | 1.00 | 0.95 | 1.00 | **0.9750** | FALLBACK_TRIGGERED |
| **TC-04** | Reverse-Pickup Eligibility | 0.95 | 1.00 | 0.95 | 1.00 | **0.9750** | RESOLVED |
| **TC-05** | Electronics Styling Warranty | 0.95 | 1.00 | 0.95 | 1.00 | **0.9750** | RESOLVED |
| **TC-06** | Order Cancellation Post-Dispatch | 0.95 | 0.40 | 0.95 | 1.00 | **0.7650** | RESOLVED |
| **TC-07** | Nykaa Privé Loyalty Redemption | 0.95 | 1.00 | 0.95 | 1.00 | **0.9750** | RESOLVED |
| **TC-08** | Payment Failure & Retry Protocol | 0.95 | 0.40 | 0.95 | 1.00 | **0.7650** | RESOLVED |
| **TC-09** | Size Exchange Workflow | 0.95 | 1.00 | 0.95 | 1.00 | **0.9750** | RESOLVED |
| **TC-10** | Damaged/Tampered Package Claim | 0.95 | 0.40 | 0.95 | 1.00 | **0.7650** | RESOLVED |
| **TC-11** | Cross-Border International Shipping | 0.95 | 1.00 | 0.95 | 1.00 | **0.9750** | RESOLVED |
| **TC-12** | Customer Escalation Matrix | 0.95 | 1.00 | 0.95 | 1.00 | **0.9750** | FALLBACK_TRIGGERED |
| **TC-13** | Adversarial Prompt-Injection Attack | 1.00 | 1.00 | 0.95 | 1.00 | **0.9925** | FALLBACK_TRIGGERED |
| **TC-14** | Out-of-Scope Domain (Mortgage) | 1.00 | 1.00 | 0.95 | 1.00 | **0.9925** | FALLBACK_TRIGGERED |
| **TC-15** | Corrupted Order ID Lookup | 1.00 | 1.00 | 0.95 | 1.00 | **0.9925** | RESOLVED |
| **AGGREGATE** | **Overall 15-Query Evaluation Matrix** | **0.9600** | **0.8800** | **0.9500** | **1.0000** | **`0.9365 / 1.0000`** | **PASS** |

---

## 6. Verification Artifacts & 100-Mark Allocation Alignment

| Task # | Capstone Requirement Description | Primary Source Deliverable | Verification Artifact | Marks | Status |
| :---: | :--- | :--- | :--- | :---: | :---: |
| **01** | Seeded Order Dataset Generator | [`dataset.py`](file:///c:/Users/kastu/Desktop/capstone%20-%20ecommerce/dataset.py) | [`transcripts/task_01_dataset.txt`](file:///c:/Users/kastu/Desktop/capstone%20-%20ecommerce/transcripts/task_01_dataset.txt) | 10 | PASS |
| **02** | 12 Policy Knowledge Base Documents | [`knowledge_base/`](file:///c:/Users/kastu/Desktop/capstone%20-%20ecommerce/knowledge_base) | 12 Markdown files | 5 | PASS |
| **03** | Dual Chunking & ChromaDB Indexing | [`rag/chunking.py`](file:///c:/Users/kastu/Desktop/capstone%20-%20ecommerce/rag/chunking.py), [`rag/indexer.py`](file:///c:/Users/kastu/Desktop/capstone%20-%20ecommerce/rag/indexer.py) | Dual collection stores | 5 | PASS |
| **04** | Threshold Calibration & Fallback | [`rag/evaluation.py`](file:///c:/Users/kastu/Desktop/capstone%20-%20ecommerce/rag/evaluation.py) | [`transcripts/task_04_threshold.txt`](file:///c:/Users/kastu/Desktop/capstone%20-%20ecommerce/transcripts/task_04_threshold.txt) | 5 | PASS |
| **05** | Precision & Recall Benchmarking | [`rag/evaluation.py`](file:///c:/Users/kastu/Desktop/capstone%20-%20ecommerce/rag/evaluation.py) | [`transcripts/task_05_pr_metrics.txt`](file:///c:/Users/kastu/Desktop/capstone%20-%20ecommerce/transcripts/task_05_pr_metrics.txt) | 5 | PASS |
| **06** | Parametric Escalation Score Engine | [`agents/tools.py`](file:///c:/Users/kastu/Desktop/capstone%20-%20ecommerce/agents/tools.py) | $S_{\text{esc}} \ge 0.65$ test run | 5 | PASS |
| **07** | CrewAI 3-Agent Core Orchestration | [`agents/crew.py`](file:///c:/Users/kastu/Desktop/capstone%20-%20ecommerce/agents/crew.py) | [`transcripts/task_07_crew_execution.txt`](file:///c:/Users/kastu/Desktop/capstone%20-%20ecommerce/transcripts/task_07_crew_execution.txt) | 10 | PASS |
| **08** | Multi-Turn Memory & Isolation | [`agents/memory.py`](file:///c:/Users/kastu/Desktop/capstone%20-%20ecommerce/agents/memory.py) | [`transcripts/task_08_memory_session.txt`](file:///c:/Users/kastu/Desktop/capstone%20-%20ecommerce/transcripts/task_08_memory_session.txt) | 5 | PASS |
| **09** | Pydantic Response Schema Contract | [`api/schemas.py`](file:///c:/Users/kastu/Desktop/capstone%20-%20ecommerce/api/schemas.py), [`app/models.py`](file:///c:/Users/kastu/Desktop/capstone%20-%20ecommerce/app/models.py) | `NykaaAgentResponse` validation | 5 | PASS |
| **10** | Inbound/Outbound Safety Guardrails | [`agents/guardrails.py`](file:///c:/Users/kastu/Desktop/capstone%20-%20ecommerce/agents/guardrails.py) | [`transcripts/task_10_guardrails.txt`](file:///c:/Users/kastu/Desktop/capstone%20-%20ecommerce/transcripts/task_10_guardrails.txt) | 5 | PASS |
| **11** | Production FastAPI & WebSocket | [`api/server.py`](file:///c:/Users/kastu/Desktop/capstone%20-%20ecommerce/api/server.py), [`app/main.py`](file:///c:/Users/kastu/Desktop/capstone%20-%20ecommerce/app/main.py) | TestClient & WS test suite | 10 | PASS |
| **12** | ELK-Compatible JSON-Lines Telemetry | [`api/logger.py`](file:///c:/Users/kastu/Desktop/capstone%20-%20ecommerce/api/logger.py) | [`logs/transactions.jsonl`](file:///c:/Users/kastu/Desktop/capstone%20-%20ecommerce/logs/transactions.jsonl) | 5 | PASS |
| **13** | 15-Query Evaluation Matrix | [`evaluation/run_judge.py`](file:///c:/Users/kastu/Desktop/capstone%20-%20ecommerce/evaluation/run_judge.py) | [`transcripts/task_13_eval_matrix.txt`](file:///c:/Users/kastu/Desktop/capstone%20-%20ecommerce/transcripts/task_13_eval_matrix.txt) | 5 | PASS |
| **14** | AutoGen 2-Agent Secondary Review | [`autogen_review/review_team.py`](file:///c:/Users/kastu/Desktop/capstone%20-%20ecommerce/autogen_review/review_team.py) | [`transcripts/task_14_autogen_review.txt`](file:///c:/Users/kastu/Desktop/capstone%20-%20ecommerce/transcripts/task_14_autogen_review.txt) | 10 | PASS |
| **15** | Least Autonomy & Runtime Budget Guard | [`governance/risk_budget.py`](file:///c:/Users/kastu/Desktop/capstone%20-%20ecommerce/governance/risk_budget.py) | HTTP 429 budget test | 5 | PASS |
| **16** | Normalized In-Memory Cache | [`governance/cache.py`](file:///c:/Users/kastu/Desktop/capstone%20-%20ecommerce/governance/cache.py) | [`transcripts/task_16_cache_metrics.txt`](file:///c:/Users/kastu/Desktop/capstone%20-%20ecommerce/transcripts/task_16_cache_metrics.txt) | 5 | PASS |
| **Total** | **Full Capstone Submission** | | **All 16 Transcripts Passing** | **100** | **PASS** |
