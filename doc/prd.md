# Product Requirements Document (PRD)

**Project:** Nykaa Domain Support Agent (Retail Operations)  
**Track:** E-Commerce & Retail (Nykaa)  
**Version:** 1.0.0  
**Status:** Approved / Production Specification  
**Reference:** [architecture.md](file:///c:/Users/kastu/Desktop/capstone%20-%20ecommerce/doc/architecture.md) | [implementation_plan.md](file:///c:/Users/kastu/Desktop/capstone%20-%20ecommerce/doc/implementation_plan.md)

---

## 1. Executive Summary & Product Vision

### 1.1 Vision Statement

The **Nykaa Domain Support Agent** is an enterprise-grade AI retail operations assistant engineered to automate customer support inquiries for Nykaa's beauty, apparel, footwear, electronics, and home & wellness divisions. The platform resolves complex policy inquiries, executes transactional order status lookups, evaluates operational logistics escalations, and guarantees customer data privacy with zero reliance on cloud APIs or external telemetry.

### 1.2 Core Problem Statement

Customer service desks in high-volume e-commerce handle concurrent request spikes across returns, refunds, delivery SLAs, and logistics delays. Key operational risks include:

1. **Policy Hallucination:** Generating inaccurate return windows, non-existent doorstep cash refunds, or erroneous warranty terms.
2. **Customer PII Exposure:** Storing or leaking sensitive contact information such as Indian mobile numbers and payment card digits.
3. **Escalation Blind Spots:** Inability to continuously compute logistics aging scores and prioritize delayed shipments for operational intervention.
4. **Adversarial Exploitation:** Vulnerability to adversarial prompt injections and system persona hijacking.

The Nykaa Domain Support Agent eliminates these failure modes through an air-gapped, multi-agent architecture featuring layered defensive guardrails, multi-turn conversational memory, least-autonomy tool execution, and secondary AutoGen compliance peer review.

---

## 2. Target Personas & Stakeholders

| Persona | Role | Primary Needs & Jobs-to-be-Done |
| :--- | :--- | :--- |
| **Nykaa Customer / Shopper** | End-User | - Instant, accurate policy answers regarding return windows, COD refunds, Privé points, and SLAs.<br>- Real-time order tracking with conversational continuity across turns.<br>- Complete privacy protection for phone numbers and payment card data. |
| **Retail Operations Specialist** | Internal Staff | - Automated deflection of repetitive tier-1 customer inquiries.<br>- Continuous parametric escalation calculation prioritizing high-risk delayed shipments ($S_{\text{esc}} \ge 0.65$) for Level 2 Logistics support. |
| **Compliance & Audit Officer** | Enterprise Regulator | - Verification of 100% factual policy grounding with zero fabricated claims.<br>- Adherence to data protection regulations with complete ELK-compatible audit logging.<br>- Strict least-autonomy role-based access control preventing unauthorized database queries. |

---

## 3. Product Scope & Functional Requirements

### 3.1 Feature Group 1: Authoritative Policy Resolution (RAG Pipeline)

* **FR-1.1:** System shall ingest and index an authoritative corpus of 12 distinct policy documents covering category return windows, COD refunds, delivery SLAs, reverse pickups, electronics warranties, order cancellations, Privé loyalty rewards, payment failures, size exchanges, tampered packages, international shipping, and the escalation matrix.
* **FR-1.2:** System shall implement dual chunking strategies:
  * Strategy A: Fixed-size character window (150 characters, 30-character overlap) producing 47 chunks.
  * Strategy B: Sentence-boundary chunking preserving complete atomic propositions (24 chunks).
* **FR-1.3:** System shall enforce an empirical cosine similarity cutoff ($\tau = 0.2021$). Inquiries falling below $\tau$ must immediately return the exact standard refusal:
  > *"I do not have sufficient information in the Nykaa policy to answer this question."*
* **FR-1.4:** Grounded responses must cite parent policy document identifiers (e.g., `01_return_window`, `07_loyalty_prive`).

### 3.2 Feature Group 2: Transactional Order Lookup & Continuous Escalation

* **FR-2.1:** System shall query active orders from an immutable, invariant-validated dataset of $N=45 \ge 40$ records generated with a fixed seed (`seed=42`).
* **FR-2.2:** Each lookup shall return order ID, category, current status, order value in INR, and days since creation.
* **FR-2.3:** System shall compute a continuous escalation score $S_{\text{esc}} \in [0.0, 1.0]$ using the weighted formulation:
  $$S_{\text{esc}} = 0.60 \cdot \mathbb{I}(\text{delayed\_shipment}) + 0.40 \cdot \left(\frac{\text{days\_since\_created}}{30}\right)$$
* **FR-2.4:** If $S_{\text{esc}} \ge 0.65$, the system must flag `escalation_triggered = True` and append an operational priority routing advisory for Level 2 Priority Logistics Support.

### 3.3 Feature Group 3: Multi-Agent CrewAI Orchestration

* **FR-3.1:** Multi-agent pipeline shall deploy 3 specialized agents enforcing the Principle of Least Autonomy:
  * **Retrieval Agent:** Restricted strictly to `policy_rag_search`.
  * **Lookup Agent:** Restricted strictly to `check_order_status`.
  * **Response Composer Agent:** Zero tools; synthesizes structured customer-facing responses.
* **FR-3.2:** Execution shall be driven by an offline deterministic LLM subclass (`MOCK_LLM`) derived from `crewai.llms.base_llm.BaseLLM` with ReAct template collision mitigation.
* **FR-3.3:** Output contract must validate against the Pydantic v2 schema `NykaaAgentResponse`.

### 3.4 Feature Group 4: Secondary Peer Review (AutoGen)

* **FR-4.1:** All draft responses shall undergo secondary review via an AutoGen `RoundRobinGroupChat` (maximum 2 turns) comprising:
  * `PolicyComplianceReviewer`: Verifies grounding, absence of PII, and policy accuracy.
  * `FinalEditor`: Emits a structured verdict using `ReviewVerdict(approved, final_answer, reason)`.
* **FR-4.2:** Hallucinated claims shall be intercepted and rewritten to conform to official policy.

### 3.5 Feature Group 5: Conversational Memory

* **FR-5.1:** System shall maintain session-isolated conversational memory using LangChain `InMemoryChatMessageHistory`.
* **FR-5.2:** Memory must support multi-turn pronominal continuity (e.g., resolving *"Is it delayed?"* to the order ID referenced in the preceding turn).
* **FR-5.3:** Uninitialized or distinct session IDs must maintain complete isolation with zero cross-session data leakage.

### 3.6 Feature Group 6: Production Gateway, UI & Audit Logging

* **FR-6.1:** FastAPI service shall provide:
  * `POST /ask`: Primary synchronous query endpoint with end-to-end execution.
  * `POST /add-document`: Dynamic policy ingestion with incremental ChromaDB indexing.
  * `WebSocket /ws/chat`: Duplex streaming endpoint with graceful disconnect handling (`code=1000`).
* **FR-6.2:** Single-line ELK-compatible JSON-Lines audit logs shall be written to [`logs/transactions.jsonl`](file:///c:/Users/kastu/Desktop/capstone%20-%20ecommerce/logs/transactions.jsonl) with UUID4 trace IDs, latency metrics, and 100% masked user inputs.
* **FR-6.3:** Interactive web console (`streamlit_app.py`) providing chat testing, order lookup, policy ingestion, and log telemetry.

---

## 4. Non-Functional & Governance Requirements

### 4.1 Air-Gapped & Offline Execution

* **NFR-1.1:** Zero cloud API invocations (no external OpenAI, Anthropic, or external embedding endpoints).
* **NFR-1.2:** Hard disablement of framework telemetry (`CREWAI_DISABLE_TELEMETRY=true`, `OTEL_SDK_DISABLED=true`).
* **NFR-1.3:** Vector embedding inference executes locally via `SentenceTransformers` (`all-MiniLM-L6-v2`) with deterministic signed semantic hashing fallback.

### 4.2 Security & Data Privacy Guardrails

* **NFR-2.1 (PII Masking):** Strict regex masking before downstream processing:
  * Indian Mobile Numbers: `(?:\+91[\s-]?)?[6-9]\d{4}[\s-]?\d{5}\b` $\longrightarrow$ `[PHONE_REDACTED]`
  * Payment Card Last-4: `(?i)(?:card\s*)?([0-9]{4})\b` $\longrightarrow$ `[CARD_REDACTED]`
* **NFR-2.2 (Injection Defense):** Rejection of adversarial prompt injection attempts (`"ignore previous instructions"`, `"system reboot"`).
* **NFR-2.3 (Log Sanitation):** Zero raw customer PII written to disk logs.

### 4.3 AI Governance & Risk Classification

* **NFR-3.1 (Medium-Risk Classification):** Classified as **Medium Risk (Customer Support & E-Commerce Operations)** under enterprise AI governance guidelines.
* **NFR-3.2 (Runtime Budget Limiter):** Inbound queries exceeding 500 estimated tokens must be rejected with HTTP 429 (`BudgetExceeded`).

### 4.4 Latency & High-Performance Caching

* **NFR-4.1 (Normalized Cache):** In-memory cache keyed by `query.strip().lower()` must return repeated queries in sub-millisecond time ($0.004\text{ ms}$, $>4,500\times$ speedup), bypassing vector search and agent coordination.
* **NFR-4.2 (Cache Invalidation):** Cache must be purged immediately upon dynamic document ingestion via `POST /add-document`.

---

## 5. Success Metrics & Key Performance Indicators (KPIs)

| Metric | Target Threshold | Measured Performance | Verification Tool |
| :--- | :--- | :--- | :--- |
| **Composite Evaluation Score** | $\ge 0.85$ (on $[0.0, 1.0]$ scale) | **`0.9365` (PASS)** | [`evaluation/run_judge.py`](file:///c:/Users/kastu/Desktop/capstone%20-%20ecommerce/evaluation/run_judge.py) |
| **Safety Evaluation Score** | $1.00$ (100% compliance) | **`1.0000` (PASS)** | [`evaluation/run_judge.py`](file:///c:/Users/kastu/Desktop/capstone%20-%20ecommerce/evaluation/run_judge.py) |
| **PII Redaction Rate** | $100\%$ across phone and card | **`100%` (PASS)** | [`agents/guardrails.py`](file:///c:/Users/kastu/Desktop/capstone%20-%20ecommerce/agents/guardrails.py) |
| **Fallback Recall on Out-of-Scope** | $100\%$ accurate fallback | **`100%` (PASS)** | [`rag/evaluation.py`](file:///c:/Users/kastu/Desktop/capstone%20-%20ecommerce/rag/evaluation.py) |
| **Dataset Invariants** | $N \ge 40$, categories $\ge 3$, delay $\in [10\%, 30\%]$ | **$N=45$, delay=13.33%** | [`dataset.py`](file:///c:/Users/kastu/Desktop/capstone%20-%20ecommerce/dataset.py) |
| **Cache Hit Speedup** | $\ge 10\times$ speedup on duplicate queries | **$>4,500\times$ speedup (0.004 ms)** | [`governance/cache.py`](file:///c:/Users/kastu/Desktop/capstone%20-%20ecommerce/governance/cache.py) |
