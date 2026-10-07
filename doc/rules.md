# System Operating Rules & AI Governance Directives

**Project:** Nykaa Domain Support Agent (Retail Operations)  
**Track:** E-Commerce & Retail (Nykaa)  
**System:** Enterprise Multi-Agent Retail Operations Support Platform  
**Document Version:** 1.0.0  
**Status:** Mandatory Operational Directives  
**Reference:** [architecture.md](file:///c:/Users/kastu/Desktop/capstone%20-%20ecommerce/doc/architecture.md) | [implementation_plan.md](file:///c:/Users/kastu/Desktop/capstone%20-%20ecommerce/doc/implementation_plan.md)

---

## 1. Governance & Risk Classification

### Rule 1.1: Enterprise AI Risk Tiering

* **Classification:** The Nykaa Domain Support Agent is classified as a **Medium Risk AI System (Customer Support & E-Commerce Operations)** under enterprise AI governance guidelines.
* **Operational Mandate:** The system must maintain complete auditability, continuous logistics risk scoring, verifiable human-in-the-loop escalation paths, and zero-hallucination factual grounding.

### Rule 1.2: Factual Policy Grounding Mandate

* All customer-facing policy representations (return windows, COD refund timelines, delivery SLAs, Privé points values, and warranty durations) must derive verbatim from the authoritative policy knowledge base.
* Fabricating non-existent return windows (e.g. claiming 60 days) or doorstep cash refunds is strictly prohibited and must be intercepted by secondary AutoGen review.

---

## 2. Statistical Invariants & Dataset Integrity Rules

### Rule 2.1: Deterministic Dataset Generation (`dataset.py`)

* The dataset generator must utilize a fixed random seed (`seed=42`).
* Total record volume must satisfy $N_{\text{total}} \ge 40$ (system implements $N = 45$).
* **Category Diversity:** Every category (`Apparel`, `Electronics`, `Home`, `Footwear`, `Beauty`) must contain at least 3 records.
* **Status Coverage:** Every lifecycle status (`Placed`, `Shipped`, `Delivered`, `Returned`, `Refunded`) must contain at least 1 record.
* **Statistical Delay Invariant:** The fraction of records flagged as delayed must strictly satisfy:
  $$0.10 \le \frac{\sum_{i=1}^{N} \mathbb{I}(\text{delayed\_shipment}_i)}{N} \le 0.30$$
  *(Measured: $6 / 45 = 13.33\%$. Violation invalidates the dataset.)*

---

## 3. Retrieval & Fallback Policy Rules

### Rule 3.1: Empirical Cosine Similarity Threshold ($\tau$)

* Vector retrieval executes against the calibrated threshold $\tau = 0.2021$.
* **Authoritative Fallback Rule:** If the top-1 cosine similarity between a user query and indexed policy chunks is strictly less than $\tau$ ($\text{Sim}_{\max} < 0.2021$), the system must abort generative inference and emit the verbatim fallback response:
  > *"I do not have sufficient information in the Nykaa policy to answer this question."*
* Under no circumstances may the system generate speculative answers on topics outside retail policies (e.g., mortgages, cryptocurrency, equity trading).

### Rule 3.2: Mandatory Parent Document Citations

* Any policy inquiry yielding similarity $\ge \tau$ must include parent document identifiers in the `citations` list of the response schema (e.g., `["01_return_window", "07_loyalty_prive"]`).

---

## 4. Multi-Agent Least-Privilege & RBAC Rules

```text
┌────────────────────────────────────────────────────────────────────────┐
│                        LEAST PRIVILEGE RBAC MATRIX                     │
├───────────────────────┬───────────────────┬────────────────────────────┤
│ Agent Role            │ Allowed Tool(s)   │ Strictly Prohibited Tool(s)│
├───────────────────────┼───────────────────┼────────────────────────────┤
│ Retrieval Agent       │ policy_rag_search │ check_order_status         │
│ Lookup Agent          │ check_order_status│ policy_rag_search          │
│ Response Composer     │ None (Synthesis)  │ policy_rag_search, check_..│
└───────────────────────┴───────────────────┴────────────────────────────┘
```

### Rule 4.1: Role-Based Tool Isolation

* **Retrieval Agent:** Permitted access to `policy_rag_search` only. Zero capability to inspect transactional customer order records.
* **Lookup Agent:** Permitted access to `check_order_status` only. Raises `LeastAutonomyViolation` if invoked by any other agent.
* **Response Composer Agent:** Least privilege: zero tool execution privileges. Operates strictly as a response synthesizer.

### Rule 4.2: Deterministic Mock LLM Mitigations

* **Mitigation 1 (ReAct Template Collision):** In `MOCK_LLM.call()`, the model must slice incoming prompt strings at the conversational turn boundary and inspect only model-generated tokens, preventing false parser matching against CrewAI's system prompt `"Observation:"`.
* **Mitigation 2 (Tool Routing Collision):** Tool dispatch evaluates exact string equality and regex schema validation (`\bNYK-\d{4}\b`). Substring matching on tool names is prohibited.

---

## 5. Continuous Escalation Scoring Rules

### Rule 5.1: Mathematical Formulation

* Every order status lookup must compute an objective logistics risk metric $S_{\text{esc}} \in [0.0, 1.0]$:
  $$S_{\text{esc}} = 0.60 \cdot \mathbb{I}(\text{delayed\_shipment}) + 0.40 \cdot \left(\frac{\text{days\_since\_created}}{30}\right)$$
* Invariant: $w_{\text{delay}} + w_{\text{aging}} = 0.60 + 0.40 = 1.00$.

### Rule 5.2: Escalation Threshold

* If $S_{\text{esc}} \ge 0.65$, the tool must set `escalation_triggered = True`.
* The final synthesized customer response must append:
  > *"Order logistics issue escalated to Level 2 Priority Logistics Support."*

---

## 6. Privacy & Security Guardrail Rules

### Rule 6.1: Inbound PII Redaction

* Inbound queries must pass through regex masking before processing:
  * Indian Mobile Numbers: `(?:\+91[\s-]?)?[6-9]\d{4}[\s-]?\d{5}\b` $\longrightarrow$ `[PHONE_REDACTED]`
  * Payment Card Digits: `(?i)(?:card\s*)?([0-9]{4})\b` $\longrightarrow$ `[CARD_REDACTED]`

### Rule 6.2: Adversarial Injection Defense

* Queries containing jailbreak patterns (`"ignore previous instructions"`, `"reveal system prompt"`, `"system reboot"`) must be rejected with HTTP 400.

### Rule 6.3: Runtime Token Budget Guard

* Pre-flight guard enforces an upper ceiling of 500 estimated tokens per request. Requests breaching the ceiling must be rejected with HTTP 429 (`BudgetExceeded`).

### Rule 6.4: In-Memory Cache Invalidation

* Dynamic policy ingestion via `POST /add-document` must immediately purge the normalized query cache to prevent serving stale policies.
