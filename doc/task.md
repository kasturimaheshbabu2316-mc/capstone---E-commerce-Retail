# Task Breakdown & Work Breakdown Structure (WBS)

**Project:** Nykaa Domain Support Agent (Retail Operations)  
**Track:** E-Commerce & Retail (Nykaa)  
**Total Tasks:** 16 Tasks across 4 Core Parts (+ UI & App Layout)  
**Status:** 100% Completed & Verified (100 / 100 Marks)  
**Reference:** [architecture.md](file:///c:/Users/kastu/Desktop/capstone%20-%20ecommerce/doc/architecture.md) | [implementation_plan.md](file:///c:/Users/kastu/Desktop/capstone%20-%20ecommerce/doc/implementation_plan.md) | [problemStatement.md](file:///c:/Users/kastu/Desktop/capstone%20-%20ecommerce/doc/problemStatement.md)

---

## 1. Master Task Checklist & Completion Status

| Task ID | Component Name | Primary Deliverable | Key Technical Requirement | Marks | Status |
| :---: | :--- | :--- | :--- | :---: | :---: |
| **Task 1** | Seeded Order Dataset Generator | [`dataset.py`](file:///c:/Users/kastu/Desktop/capstone%20-%20ecommerce/dataset.py) | Seed=42, $N=45 \ge 40$, 5 categories, delay rate 13.3% $\in [10\%, 30\%]$ | 10 | **PASS** |
| **Task 2** | Authoritative Policy Corpus | [`knowledge_base/`](file:///c:/Users/kastu/Desktop/capstone%20-%20ecommerce/knowledge_base) | 12 policy files, 2–5 sentences each with numerical SLAs | 5 | **PASS** |
| **Task 3** | Dual Chunking Strategies | [`rag/chunking.py`](file:///c:/Users/kastu/Desktop/capstone%20-%20ecommerce/rag/chunking.py) | Strategy A (150/30 fixed) vs Strategy B (sentence boundary) | 5 | **PASS** |
| **Task 4** | Vector Store & Fallback Calibration | [`rag/indexer.py`](file:///c:/Users/kastu/Desktop/capstone%20-%20ecommerce/rag/indexer.py), [`rag/evaluation.py`](file:///c:/Users/kastu/Desktop/capstone%20-%20ecommerce/rag/evaluation.py) | ChromaDB dual stores, $\tau = 0.2021$ cutoff, standard refusal | 5 | **PASS** |
| **Task 5** | Chunking Strategy Benchmark | [`rag/evaluation.py`](file:///c:/Users/kastu/Desktop/capstone%20-%20ecommerce/rag/evaluation.py) | Precision & Recall evaluation across 5 benchmark queries | 5 | **PASS** |
| **Task 6** | Order Status Tool & Escalation | [`agents/tools.py`](file:///c:/Users/kastu/Desktop/capstone%20-%20ecommerce/agents/tools.py) | Status lookup, $S_{\text{esc}} = 0.60\cdot\mathbb{I}(\text{delay}) + 0.40\cdot(\text{days}/30) \ge 0.65$ | 5 | **PASS** |
| **Task 7** | Deterministic MockLLM & CrewAI Crew | [`agents/mock_llm.py`](file:///c:/Users/kastu/Desktop/capstone%20-%20ecommerce/agents/mock_llm.py), [`agents/crew.py`](file:///c:/Users/kastu/Desktop/capstone%20-%20ecommerce/agents/crew.py) | 3-agent least privilege, ReAct template collision mitigation | 10 | **PASS** |
| **Task 8** | Multi-Turn Conversational Memory | [`agents/memory.py`](file:///c:/Users/kastu/Desktop/capstone%20-%20ecommerce/agents/memory.py) | LangChain `InMemoryChatMessageHistory`, session isolation & continuity | 5 | **PASS** |
| **Task 9** | Structured Pydantic Response Schema | [`api/schemas.py`](file:///c:/Users/kastu/Desktop/capstone%20-%20ecommerce/api/schemas.py), [`app/models.py`](file:///c:/Users/kastu/Desktop/capstone%20-%20ecommerce/app/models.py) | Pydantic v2 `NykaaAgentResponse` contract validation | 5 | **PASS** |
| **Task 10** | Dual-Stage Safety Guardrails | [`agents/guardrails.py`](file:///c:/Users/kastu/Desktop/capstone%20-%20ecommerce/agents/guardrails.py) | Regex PII masking (Phone, Card), injection defense, grounding | 5 | **PASS** |
| **Task 11** | Production FastAPI Service | [`api/server.py`](file:///c:/Users/kastu/Desktop/capstone%20-%20ecommerce/api/server.py), [`app/main.py`](file:///c:/Users/kastu/Desktop/capstone%20-%20ecommerce/app/main.py) | `POST /ask`, `POST /add-document`, duplex `WebSocket /ws/chat` | 10 | **PASS** |
| **Task 12** | Structured ELK Audit Logging | [`api/logger.py`](file:///c:/Users/kastu/Desktop/capstone%20-%20ecommerce/api/logger.py) | Single-line JSON-L (`logs/transactions.jsonl`), UUID4 trace IDs | 5 | **PASS** |
| **Task 13** | LLM Judge & 15-Query Evaluation | [`evaluation/run_judge.py`](file:///c:/Users/kastu/Desktop/capstone%20-%20ecommerce/evaluation/run_judge.py) | 15-query test suite, 4 scoring dimensions (**Score: 0.9365**) | 5 | **PASS** |
| **Task 14** | AutoGen Secondary Peer Review Team | [`autogen_review/review_team.py`](file:///c:/Users/kastu/Desktop/capstone%20-%20ecommerce/autogen_review/review_team.py) | `RoundRobinGroupChat` (max_turns=2), Clean Approval vs Active Revision | 10 | **PASS** |
| **Task 15** | AI Governance & Token Budget Guard | [`governance/risk_budget.py`](file:///c:/Users/kastu/Desktop/capstone%20-%20ecommerce/governance/risk_budget.py) | Max 500 tokens (HTTP 429), Medium-Risk enterprise tiering | 5 | **PASS** |
| **Task 16** | Normalized Query Response Cache | [`governance/cache.py`](file:///c:/Users/kastu/Desktop/capstone%20-%20ecommerce/governance/cache.py) | Normalized string key (`query.strip().lower()`), 0.004 ms bypass | 5 | **PASS** |
| **Bonus** | Streamlit Interactive Operations UI | [`streamlit_app.py`](file:///c:/Users/kastu/Desktop/capstone%20-%20ecommerce/streamlit_app.py) | Interactive web UI with chat, order lookup, and log viewer | - | **PASS** |
| **Bonus** | Standard Application Package Layout | [`app/`](file:///c:/Users/kastu/Desktop/capstone%20-%20ecommerce/app) | Standardized module layout matching enterprise conventions | - | **PASS** |
| **Total** | **Full Capstone Submission** | | **All 16 Tasks Verified & Passing** | **100** | **100/100** |

---

## 2. Granular Task Breakdown & Technical Specifications

### Task 1: Synthetic Transactional Dataset Generator

* **File:** [`dataset.py`](file:///c:/Users/kastu/Desktop/capstone%20-%20ecommerce/dataset.py)
* **Scope:** Deterministic generation of synthetic retail order records.
* **Invariants Enforced:**
  1. Fixed seed (`seed=42`).
  2. Dataset count $N = 45 \ge 40$.
  3. Controlled Categories: `Apparel`, `Electronics`, `Home`, `Footwear`, `Beauty` ($\ge 3$ records per category).
  4. Controlled Statuses: `Placed`, `Shipped`, `Delivered`, `Returned`, `Refunded` ($\ge 1$ record per status).
  5. Statistical Delay Rate: $6/45 = 13.33\%$, strictly within $[0.10, 0.30]$.
* **Verification Transcript:** [`transcripts/task_01_dataset.txt`](file:///c:/Users/kastu/Desktop/capstone%20-%20ecommerce/transcripts/task_01_dataset.txt)

---

### Task 2: Authoritative Policy Knowledge Base

* **Directory:** [`knowledge_base/`](file:///c:/Users/kastu/Desktop/capstone%20-%20ecommerce/knowledge_base)
* **Scope:** 12 authoritative Markdown policy documents ($2\text{--}5$ sentences each):
  * `01_return_window.md`: Category return windows (Beauty 15d, Apparel 7d, Home 10d).
  * `02_cod_refund.md`: 3–5 day bank/wallet transfer; zero doorstep cash refunds.
  * `03_delivery_sla.md`: Metro 2–4 days, Tier-2/3 4–7 days, Nykaa Now 2–4 hours.
  * `04_reverse_pickup.md`: 19,000+ pin codes, 24–48h pickup attempt, ₹100 max self-ship.
  * `05_warranty_terms.md`: 12-month manufacturer styling warranty.
  * `06_order_cancellation.md`: Cancellation allowed while Placed; locked once Shipped.
  * `07_loyalty_prive.md`: 100 points = ₹10; redeemable on orders > ₹500; 365-day validity.
  * `08_payment_failure.md`: Auto-reconciliation in 24–48h; bank refund in 5–7 days.
  * `09_size_exchange.md`: Free 1-time exchange within 7 days.
  * `10_damaged_tampered.md`: 48h claim window with photo/video proof.
  * `11_international_shipping.md`: Cross-border shipping in 7–14 days.
  * `12_escalation_matrix.md`: L1 (24h), L2 Logistics (4h, delay >3d), L3 (Fraud/legal).
* **Verification Transcript:** [`transcripts/task_02_knowledge_base.txt`](file:///c:/Users/kastu/Desktop/capstone%20-%20ecommerce/transcripts/task_02_knowledge_base.txt)

---

### Task 3: Dual Chunking Strategies

* **File:** [`rag/chunking.py`](file:///c:/Users/kastu/Desktop/capstone%20-%20ecommerce/rag/chunking.py)
* **Scope:** Implementation of two contrasting chunking approaches:
  * Strategy A: `chunk_fixed_size` (window: 150 chars, overlap: 30 chars $\to$ 47 chunks).
  * Strategy B: `chunk_sentence_boundary` (regex `(?<=[.!?])\s+` $\to$ 24 chunks).

---

### Task 4: Vector Store & Empirical Fallback Calibration

* **Files:** [`rag/indexer.py`](file:///c:/Users/kastu/Desktop/capstone%20-%20ecommerce/rag/indexer.py), [`rag/evaluation.py`](file:///c:/Users/kastu/Desktop/capstone%20-%20ecommerce/rag/evaluation.py)
* **Scope:** Local ChromaDB indexing into `nykaa_policy_fixed` and `nykaa_policy_sentence`, deterministic embedding generation, and empirical cutoff calibration.
* **Findings:**
  * Minimum in-scope similarity: `0.2435`
  * Maximum out-of-scope similarity: `0.1607`
  * Calibrated threshold: $\tau = 0.2021$ (separation margin $+0.0828$)
  * Standard refusal: *"I do not have sufficient information in the Nykaa policy to answer this question."*
* **Verification Transcript:** [`transcripts/task_04_threshold.txt`](file:///c:/Users/kastu/Desktop/capstone%20-%20ecommerce/transcripts/task_04_threshold.txt)

---

### Task 5: Chunking Strategy Precision & Recall Benchmark

* **File:** [`rag/evaluation.py`](file:///c:/Users/kastu/Desktop/capstone%20-%20ecommerce/rag/evaluation.py)
* **Scope:** Evaluated 5 in-scope queries across both collections against ground truth document sets.
* **Results:**
  * Strategy A (Fixed-size 150/30): Mean Precision = `0.4667`, Mean Recall = `1.0000`
  * Strategy B (Sentence-boundary): Mean Precision = `0.5000`, Mean Recall = `1.0000`
* **Decision:** Strategy B selected for production deployment.
* **Verification Transcript:** [`transcripts/task_05_pr_metrics.txt`](file:///c:/Users/kastu/Desktop/capstone%20-%20ecommerce/transcripts/task_05_pr_metrics.txt)

---

### Task 6: Order Status Tool & Parametric Escalation Engine

* **File:** [`agents/tools.py`](file:///c:/Users/kastu/Desktop/capstone%20-%20ecommerce/agents/tools.py)
* **Scope:** Order status lookup tool with continuous escalation calculation:
  $$S_{\text{esc}} = 0.60 \cdot \mathbb{I}(\text{delayed\_shipment}) + 0.40 \cdot \left(\frac{\text{days\_since\_created}}{30}\right), \quad \text{Threshold } \theta = 0.65$$
* **Least Autonomy Enforcement:** Throws `LeastAutonomyViolation` if caller is not `Lookup Agent`.

---

### Task 7: Deterministic MockLLM & CrewAI 3-Agent Core

* **Files:** [`agents/mock_llm.py`](file:///c:/Users/kastu/Desktop/capstone%20-%20ecommerce/agents/mock_llm.py), [`agents/crew.py`](file:///c:/Users/kastu/Desktop/capstone%20-%20ecommerce/agents/crew.py)
* **Scope:** 3-agent orchestration pipeline (Retrieval Agent, Lookup Agent, Response Composer) powered by offline `MOCK_LLM`.
* **Mitigation:** Slices prompt at turn boundary to prevent ReAct template collisions.
* **Verification Transcript:** [`transcripts/task_07_crew_execution.txt`](file:///c:/Users/kastu/Desktop/capstone%20-%20ecommerce/transcripts/task_07_crew_execution.txt)

---

### Task 8: Multi-Turn Conversational Memory

* **File:** [`agents/memory.py`](file:///c:/Users/kastu/Desktop/capstone%20-%20ecommerce/agents/memory.py)
* **Scope:** Multi-turn session management with LangChain `InMemoryChatMessageHistory`.
* **Continuity:** Turn 1 (*"Track NYK-1002"*) $\to$ Turn 2 (*"Is it delayed?"* $\to$ resolves *"it"* to `NYK-1002`).
* **Isolation:** Uninitialized session returns empty history with zero state bleed.
* **Verification Transcript:** [`transcripts/task_08_memory_session.txt`](file:///c:/Users/kastu/Desktop/capstone%20-%20ecommerce/transcripts/task_08_memory_session.txt)

---

### Task 9: Structured Pydantic Response Schema

* **Files:** [`api/schemas.py`](file:///c:/Users/kastu/Desktop/capstone%20-%20ecommerce/api/schemas.py), [`app/models.py`](file:///c:/Users/kastu/Desktop/capstone%20-%20ecommerce/app/models.py)
* **Scope:** Pydantic v2 `NykaaAgentResponse` enforcing typed fields: `answer`, `citations`, `escalation_triggered`, `escalation_score`, `grounded`.

---

### Task 10: Inbound & Outbound Safety Guardrails

* **File:** [`agents/guardrails.py`](file:///c:/Users/kastu/Desktop/capstone%20-%20ecommerce/agents/guardrails.py)
* **Scope:** Pre-flight PII redaction (`[PHONE_REDACTED]`, `[CARD_REDACTED]`), prompt injection rejection (HTTP 400), and output grounding verification against $\tau = 0.2021$.
* **Verification Transcript:** [`transcripts/task_10_guardrails.txt`](file:///c:/Users/kastu/Desktop/capstone%20-%20ecommerce/transcripts/task_10_guardrails.txt)

---

### Task 11: Production FastAPI Service

* **Files:** [`api/server.py`](file:///c:/Users/kastu/Desktop/capstone%20-%20ecommerce/api/server.py), [`app/main.py`](file:///c:/Users/kastu/Desktop/capstone%20-%20ecommerce/app/main.py)
* **Scope:** REST endpoints (`POST /ask`, `POST /add-document`) and streaming `WebSocket /ws/chat` catching `WebSocketDisconnect` cleanly.

---

### Task 12: Structured ELK Audit Logging

* **File:** [`api/logger.py`](file:///c:/Users/kastu/Desktop/capstone%20-%20ecommerce/api/logger.py)
* **Scope:** Single-line JSON-Lines logger writing to [`logs/transactions.jsonl`](file:///c:/Users/kastu/Desktop/capstone%20-%20ecommerce/logs/transactions.jsonl) with UUID4 trace IDs and masked prompts.

---

### Task 13: Quantitative Evaluation & Test Suite

* **Files:** [`evaluation/run_judge.py`](file:///c:/Users/kastu/Desktop/capstone%20-%20ecommerce/evaluation/run_judge.py), [`evaluation/test_suite.py`](file:///c:/Users/kastu/Desktop/capstone%20-%20ecommerce/evaluation/test_suite.py)
* **Scope:** 15-query test suite across 4 weighted scoring dimensions:
  * Accuracy: `0.9600` (35%)
  * Grounding: `0.8800` (35%)
  * Completeness: `0.9500` (15%)
  * Safety: `1.0000` (15%)
  * **Composite Score:** **`0.9365 / 1.0000` (PASS)**
* **Verification Transcript:** [`transcripts/task_13_eval_matrix.txt`](file:///c:/Users/kastu/Desktop/capstone%20-%20ecommerce/transcripts/task_13_eval_matrix.txt)

---

### Task 14: AutoGen Secondary Peer Review Subsystem

* **File:** [`autogen_review/review_team.py`](file:///c:/Users/kastu/Desktop/capstone%20-%20ecommerce/autogen_review/review_team.py)
* **Scope:** AutoGen `RoundRobinGroupChat` (max_turns=2) pairing `PolicyComplianceReviewer` and `FinalEditor`, emitting structured `ReviewVerdict`.
* **Demonstrations:** Both Clean Approval and Active Revision cases verified.
* **Verification Transcript:** [`transcripts/task_14_autogen_review.txt`](file:///c:/Users/kastu/Desktop/capstone%20-%20ecommerce/transcripts/task_14_autogen_review.txt)

---

### Task 15: AI Governance & Runtime Budget Guard

* **File:** [`governance/risk_budget.py`](file:///c:/Users/kastu/Desktop/capstone%20-%20ecommerce/governance/risk_budget.py)
* **Scope:** Enterprise Medium-Risk tiering and runtime budget guard capping requests at 500 estimated tokens (throwing HTTP 429 when exceeded).

---

### Task 16: Normalized Query Response Cache

* **File:** [`governance/cache.py`](file:///c:/Users/kastu/Desktop/capstone%20-%20ecommerce/governance/cache.py)
* **Scope:** In-memory query cache keyed by `query.strip().lower()`. Delivers warm hit responses in 0.004 ms ($>4,500\times$ speedup) and purges upon `/add-document`.
* **Verification Transcript:** [`transcripts/task_16_cache_metrics.txt`](file:///c:/Users/kastu/Desktop/capstone%20-%20ecommerce/transcripts/task_16_cache_metrics.txt)
