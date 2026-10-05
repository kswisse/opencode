# Agent Contracts — The 6 V1 Roles

**Version:** V1 Freeze 2026-08-26  
**Queue:** `arq` on Redis (not Kafka)  
**Coordination:** `ResearchOrchestrator` (state machine) + `DiscoveryOrchestrator` (fan-out) + `BudgetController`  
**Idempotency:** `sha256(job_id + phase + input_hash)` per task  
**Budget-aware:** every agent checks `BudgetController` before LLM/fetch  
**LLM-agnostic:** all agents depend on `LLMProvider` protocol, not a concrete model

---

## 1. Role Inventory (V1 Only 6)

| # | Role | Primary Package | Triggered By | Parallelizable | LLM Role | Source Tier Access |
|---|------|-----------------|--------------|----------------|----------|---------------------|
| 1 | **PLANNER** | `packages/planner` | `research_runs.status=pending→planning` | No (single per run) | `REASONING_MODEL` | None (no fetch) |
| 2 | **DISCOVERY WORKER** | `packages/search` + `packages/discovery` | `plan.research_queries[]` | Yes — 8–16 shards in parallel | `FAST_MODEL` (expand), `EXTRACTION_MODEL` (snippets) | All tiers, but tier 1-2 prioritized |
| 3 | **SOCIAL DISCOVERY WORKER** | `packages/social` | `plan.research_queries[]` where `purpose=social` | Yes — 2–4 shards | `FAST_MODEL` | Tier 3–5 (social) |
| 4 | **ENTITY RESOLVER** | `packages/entities` | After document dedup, before qualification | Yes — per-document-entity extraction | `EXTRACTION_MODEL` | None (operates on docs) |
| 5 | **DEEP RESEARCH WORKER** | `packages/research` + `packages/crawling` | GAP DETECTION output (`gap_queries[]`) | Yes — 4–8 per recursive iteration | `EXTRACTION_MODEL` + `REASONING_MODEL` | Tier 1-2 for gap_fill/verification |
| 6 | **VERIFICATION/SYNTHESIS WORKER** | `packages/verification` + `packages/scoring` + `packages/reporting` | After each evidence batch + final | Yes per claim (verify) → single reduce (score+report) | `VERIFICATION_MODEL` (verify), `REASONING_MODEL` (report) | Reads `claim_sources` tier |

**Out of scope for V1 (postponed):** dedicated Crawler agent (merged into Discovery/Deep Research via `crawling` package), Ranking-only agent (merged into Scoring), UI agent (minimal UI is not agentic).

---

## 2. Contract Shape (Shared)

Every agent exposes:

```python
@dataclass
class AgentInput:
    job_id: UUID
    run_id: UUID
    budget: BudgetSnapshot        # remaining_tokens, remaining_usd, fetch_remaining, soft_hit?
    config_hash: str
    trace_id: str                 # OTEL / structlog correlation

@dataclass
class AgentOutput:
    job_id: UUID
    run_id: UUID
    status: Literal["success","partial","failed"]
    artefacts: list[ArtefactRef]  # DB IDs produced (document_ids, claim_ids, etc.)
    cost: CostRecord              # prompt_tokens, completion_tokens, cost_usd, fetch_count
    next_phase: JobStatus | None  # hint to orchestrator (or None if orchestrator decides)
    error: str | None
    partial_reason: str | None

class Agent(Protocol):
    name: str
    async def run(self, inp: AgentInput) -> AgentOutput: ...
    async def health_check(self) -> bool: ...
```

- **Retry:** `arq` retries on transient (`httpx.Timeout`, `LLMError.rate_limited`, `RedisError`). Max 3 per task, backoff `2s, 8s, 32s` + jitter. Idempotency key prevents double-write on retry.
- **Budget awareness:** First line of every `run` is `if budget.is_hard_exceeded(): return partial`. Soft exceeded → skip optional expansions (e.g., planner emits fewer queries, discovery caps at `max_results/2`).
- **Observability:** Every agent logs `agent={name} job={job_id} run={run_id} phase={current_pass} cost={cost}` and emits OTEL span.

---

## 3. Per-Role Contracts

### 3.1 PLANNER

**Purpose:** Convert raw user prompt into a planner plan: normalized query, intent, entities heuristically seeded, expanded queries × regions × languages, source strategy.

**Input:**

```python
@dataclass
class PlannerInput(AgentInput):
    raw_query: str                # user input e.g., "AI startup founded 2023 in Berlin, seed round?"
    depth: Literal["quick","standard","deep"]
    regions: list[str] | None     # None → planner infers from query + config default
    languages: list[str] | None
    time_range: tuple[datetime|None, datetime|None] | None
    source_strategy: Literal["broad","focused","official_first"]
```

**Output:**

```python
@dataclass
class PlannerPlan:
    normalized_query: str         # cleaned, canonical form
    intent: Literal["company_research","person_research","market_research","general"]  # V1 supports company+general
    seeded_entities: list[SeededEntity]  # {name, type hint, confidence}
    research_queries: list[ResearchQueryShard]  # expanded queries — see below
    coverage_targets: list[str]   # e.g., ["identity","founders","product","funding","growth","market","competition","tech","customers","risks"]
    budget_estimate: CostEstimate # tokens + fetch estimate for discovery

@dataclass
class ResearchQueryShard:
    expanded_query: str
    region: str
    language: str
    purpose: Literal["discovery","verification","context"]  # social queries have purpose="discovery" + source filter
    rank: int                     # planner ranking (discovery priority)

@dataclass
class PlannerOutput(AgentOutput):
    plan: PlannerPlan
```

**State transition:**

```
research_runs.status: pending ──PLANNER.run()──▶ planning
    on success: write research_queries rows (one per shard), write planner_plan JSON to research_runs.metadata, transition to discovering
    on failure: research_runs.status=failed, research_jobs.last_error set
```

**Logic (deterministic + LLM-assisted):**

1. Deterministic: trim, language detect, region infer (keywords, TLD hints from `configs/regions/*.json`).
2. LLM `structured_generate` with schema `PlannerPlan` (temperature 0.3, `REASONING_MODEL`) to expand queries (2–5 for quick, 5–10 for standard, 10–16 for deep) with region/language sharding. Cost counted.
3. Budget estimate: `tokens≈ len(queries)*200 + N_docs*500`, `fetch≈ len(queries)*max_results*0.6`. If `estimate > budget_soft` → prune lowest-rank shards deterministically (no LLM needed).

**Idempotency:** `sha256(job_id + normalized_query + depth + regions + languages)`. Re-running planner with same input returns same plan without new LLM call (cached in `research_runs.metadata`).

**Failure modes:**

| Failure | Handling |
|---------|----------|
| LLM timeout / rate_limit | Retry 3×, then fallback to heuristic expansion (no LLM) — mark `partial_reason="planner_llm_fallback"` |
| Budget hard exceeded before planning | Return `failed` with `partial_reason="budget_hard"` — no queries emitted |

---

### 3.2 DISCOVERY WORKER (Web/News/Specialized)

**Purpose:** Execute a shard of `research_queries` against web/news/specialized connectors, fetch documents, normalize, and write `documents` + `retrieval_runs`.

**Input:**

```python
@dataclass
class DiscoveryInput(AgentInput):
    shards: list[ResearchQueryShard]  # 1–4 shards per worker (batch)
    connectors: list[str] | None      # None → all active connectors for shard's region/lang
```

**Output:**

```python
@dataclass
class DiscoveryOutput(AgentOutput):
    documents: list[DocumentRef]      # {document_id, url, canonical_url, content_hash, is_duplicate_of}
    retrieval_runs: list[RetrievalRunRef]
    dedup_stats: DedupStats           # {exact_url: n, canonical: n, content_hash: n, near_duplicate: n}
```

**Parallel execution model:**

```
Planner emits 12 shards
    │
    ├─ DiscoveryOrchestrator shards into 3 workers × 4 shards each
    │   each worker fans out per-shard per-connector searches in parallel (asyncio.gather, semaphore=8)
    │   each search → list[RawResult] → DocumentNormalizer → documents (bulk upsert with uq_documents_job_url)
    │
    └─ Aggregation: Deduplicator runs once after all workers join (not per-worker) to avoid cross-worker duplicates
```

- **Per-shard concurrency:** `asyncio.gather` with `asyncio.Semaphore(8)` global + per-connector rate limiter (token bucket from `sources.rate_limit_per_min`).
- **Retry/idempotency:** Per-shard idempotency key `sha256(run_id + shard.expanded_query + shard.region + shard.language + connector.name)`. A retry reuses `retrieval_runs` row (upsert).
- **Timeout:** Per-connector `timeout_ms` from registry; overall worker timeout = `max(connector timeouts) + 5s`. Single connector failure → `retrieval_runs.status=failed` but worker output is `partial` (not `failed`) if ≥1 connector succeeded.
- **Budget:** Before each `search`/`fetch`, check `BudgetController.can_fetch(budget)`. If hard exceeded → skip fetch, count as `skipped_due_to_budget`.

**State transition:**

```
research_runs.status: planning ─▶ discovering
    after all discovery workers join + dedup: transition to normalizing (normalize was already done inline; dedup finalizes)
    if all connectors failed + no documents: status=failed or partial (depends on retry budget)
```

**No LLM in hot path** except optional snippet ranking (fast model, capped). Discovery is I/O-bound, not LLM-bound — cost control.

---

### 3.3 SOCIAL DISCOVERY WORKER

**Purpose:** Public social fetch (Reddit, X public, YouTube metadata) — **scoped to authorized public APIs only**. No login/CAPTCHA/private extraction.

**Input/Output:** Same shape as Discovery Worker but:

- `connectors` restricted to social registry entries (`reddit_public`, `x_public_search`, `youtube_search`).
- Output includes `social_posts` rows linked to `documents` plus `document` rows with `metadata.platform`.

**Guardrails (hard):**

- Worker checks `sources.access_method` — if a source expands to require login/CAPTCHA in runtime, worker aborts that shard with `error="access_method_not_allowed"` and logs anomaly.
- Content is stored as `documents` (with `social_posts` sidecar) — same evidence pipeline.

**Parallelism:** 2–4 shards per worker, semaphore=4 (social APIs are rate-limited tighter).

**State:** Runs **concurrently with Discovery Worker** (same `discovering` phase) — orchestrator fans out both worker types together.

---

### 3.4 ENTITY RESOLVER

**Purpose:** Resolve canonical entities and aliases from normalized documents; produce `entities` + `entity_aliases` + domain projections (`companies`, `people`, etc.) and the deduplicated **candidate set**.

**Input:**

```python
@dataclass
class EntityResolverInput(AgentInput):
    document_ids: list[UUID]          # deduped, non-duplicate documents
```

**Output:**

```python
@dataclass
class EntityResolverOutput(AgentOutput):
    entities: list[EntityRef]         # {entity_id, canonical_name, type, confidence}
    aliases: list[AliasRef]
    candidate_set: list[CandidateRef] # deduped candidate companies/people (post alias collapse)
    qualification_hints: list[QualificationHint]  # e.g., "two docs conflate Acme AI vs Acme Corp"
```

**Logic:**

1. Per-document entity extraction via `EXTRACTION_MODEL` `structured_generate` with schema `ExtractedEntities` (company/person/product). Batched (4 docs per call to save cost), temperature 0.2.
2. Deterministic alias normalization (`alias_normalized = lower + strip_punct + transliterate`) + trigram dedup (`pg_trgm` similarity > 0.88 → alias collapse).
3. Candidate set = entities with `confidence >= 0.5` and `evidence_count >= 2` OR `tier 1 source` mention. Near-duplicate entities merged (cosine on canonical name embedding > 0.88 + shared domain/alias → merge).
4. Domain projection: if `entity_type=company`, upsert `companies` row; `person` → `people`, etc. Missing fields stay null — filled by Deep Research.

**Parallelism:** Parallel per **document batch** (workers over document slices), final alias-collapse is a single reduce (needs global view).

**Idempotency:** `sha256(run_id + sorted(document_ids) + model)` — re-running with same docs reuses rows.

**Budget:** Resolution is LLM-bound — checks budget before each batch call. If soft exceeded → skip low-confidence docs (tail).

**State transition:**

```
research_runs.status: normalizing ─▶ qualifying   (entity resolution is part of qualifying)
    after resolver + qualification (deterministic rules) → transition to deep_researching if gaps found, else verifying
```

---

### 3.5 DEEP RESEARCH WORKER

**Purpose:** Gap-filling: fetch additional documents for missing/uncertain coverage dimensions per candidate (identity/founders/product/funding/growth/market/competition/tech/customers/risks).

**Input:**

```python
@dataclass
class DeepResearchInput(AgentInput):
    gap_queries: list[GapQuery]      # from Gap Detection

@dataclass
class GapQuery:
    candidate_entity_id: UUID
    coverage_dimension: str           # e.g., "funding"
    query: str                        # e.g., "Acme AI seed round investors 2023"
    region: str
    language: str
    preferred_tiers: list[int]        # [1,2] for funding
    purpose: Literal["gap_fill","verification"]
```

**Output:**

```python
@dataclass
class DeepResearchOutput(AgentOutput):
    documents: list[DocumentRef]
    claims: list[ClaimRef]            # claims extracted inline (same extractor as discovery)
    coverage_delta: dict[str, str]    # e.g., {"funding": "MISSING→FOUND"}
```

**Parallelism:** 4–8 `gap_queries` per worker per iteration; multiple workers per iteration. Bounded by `max_iterations` (default 2) and budget.

**State machine integration (recursive loop):**

```
qualifying/ deep_researching ─▶ gap_detecting (analyze coverage matrix)
    if gaps + budget + iteration < max → emit gap_queries → deep_researching (recursive)
    else → verifying
```

- **Stopping:** Same criteria as `RESEARCH_STATE_MACHINE.md` — coverage complete, diminishing gain (< 5% new claims per iteration), budget soft/hard, max iterations, confidence threshold (>0.85 avg for required dimensions).
- **Retry/idempotency:** Per `gap_query` key `sha256(run_id + candidate_id + dimension + query + tier)`. Duplicate gap queries (from parallel gap detectors) deduplicate via this key.

**Sources:** Tier-aware — `funding` prefers tier 1 (SEC, Crunchbase-like licensed snapshot if available or official), `product/tech` prefers tier 1 (company site, docs), `market/competition` tier 2-3.

---

### 3.6 VERIFICATION/SYNTHESIS WORKER

**Purpose:** Verify claims against evidence, detect contradictions, apply deterministic scoring, and synthesize citation-backed report. This is a **map-reduce**: per-claim verify (parallel) → contradiction detection → scoring → report (single reduce).

**Input:**

```python
@dataclass
class VerificationInput(AgentInput):
    claim_ids: list[UUID]            # claims to verify (batch per worker)
    mode: Literal["initial","adversarial","final"]  # final includes scoring/report

@dataclass
class SynthesisInput(AgentInput):     # only for the final reduce worker
    claim_ids: list[UUID]            # all claims in run
    scores: list[ScoreRef]
    contradictions: list[ContradictionRef]
```

**Output:**

```python
@dataclass
class VerificationOutput(AgentOutput):
    verifications: list[VerificationResult]  # per claim: status, confidence, reasoning, factors
    contradictions: list[ContradictionRef]  # newly found

@dataclass
class SynthesisOutput(AgentOutput):
    scores: list[ScoreRef]             # deterministic scores (or reused)
    report_markdown: str
    report_json: dict
```

**Verify (parallel map):**

- For each claim: collect `supporting_evidence = evidence WHERE role=supporting via claim_evidence`, `contradicting_evidence` similarly, `claim_sources` for tier/independence.
- Call `VerificationEngine.verify_claim` (deterministic matrix — **no LLM** for status, LLM only for `verification_reasoning` optional via `VERIFICATION_MODEL` if claim is contested and budget allows).
- `ProvenanceAnalyzer` computes `source_independence` (copy-graph + tier diversity + domain diversity).
- Write `claim.verification_status`, `verification_reasoning`, `evidence` linkage, `claim_sources` tier snapshot.

**Contradiction detection (after verify):**

- `ContradictionEngine` pairwise over claims of same candidate/dimension: embedding cosine > 0.92 + numeric/temporal conflict → emit `contradictions` row. Severity based on tier and numeric delta.

**Score (deterministic):**

- `ConfidenceScorer + Ranker` compute `scores` table rows per claim per run. Deterministic math (see SCORING). No LLM.

**Report (single reduce, `REASONING_MODEL`):**

- `ReportGenerator` takes `claims + scores + evidence + contradictions + coverage` and produces:
  - `markdown`: citation-backed sections per coverage dimension, evidence anchors `[1]`, contradictions callouts, confidence badges.
  - `json_payload`: machine-readable (claims with evidence_ids, scores, citations).
- Citations are **evidence spans** with `document_id + char_start/end + source tier`, not bare URLs.

**State transition:**

```
research_runs.status: verifying ─▶ scoring (scores computed)
    scoring ─▶ reporting (report generated, markdown+JSON written)
    reporting ─▶ completed | partial (depending on budget/coverage)
```

**Idempotency:** Verify per `claim_ids` batch `sha256(run_id + sorted(claim_ids) + mode)`. Report by `sha256(run_id + sorted(claim_ids) + scores.hash)`.

**Budget:** Verify/score are cheap (deterministic); report generation is LLM-bound — check budget; if hard exceeded, generate minimal template report from scores without LLM reasoning and mark `partial_reason="budget_hard_report_template"`.

---

## 4. Parallel Execution Model (Orchestrated)

### 4.1 Execution DAG per Run

```
  PLANNER (single)
    │
    ▼
  DISCOVERY WORKERS (8–16 shards) ──┬── SOCIAL WORKERS (2–4)   [parallel, same phase]
    │                               │
    └─────────── join + dedup ───────┘
                │
                ▼
          ENTITY RESOLVER (parallel batches → single alias collapse)
                │
                ▼
          QUALIFICATION (deterministic, inline — not a separate agent)
                │
                ▼
          GAP DETECTION (deterministic coverage matrix)
                │
          ┌─────▼─────┐
          │ gaps?     │── no ──▶ VERIFICATION WORKERS (per-claim parallel)
          │ + budget? │
          └─────┬─────┘
                │ yes
                ▼
          DEEP RESEARCH WORKERS (parallel, iterative, bounded)
                │
                ▼  loop back to GAP DETECTION
         VERIFICATION WORKERS (per-claim)
                │
                ▼
          CONTRADICTION ENGINE (after verify join)
                │
                ▼
          SCORING (deterministic, parallel per claim → ranked)
                │
                ▼
          REPORT (single reduce, LLM)
                │
                ▼
          completed / partial / failed
```

### 4.2 Queuing & Concurrency Controls

- **Queue depth:** Discovery fan-out capped at 16 shards per run (config `discovery.max_shards_per_run`). Deep research capped at 8 `gap_queries` per iteration.
- **Semaphore:** Global `asyncio.Semaphore(32)` for outbound HTTP; per-source `rate_limit_per_min` token bucket.
- **Worker concurrency (arq):** `max_jobs=8` per container for I/O-bound workers, `max_jobs=4` for LLM-bound workers (entity/verification). Tuning via `WORKER_CONCURRENCY` env.
- **Backpressure:** If Redis pending > 100, API returns `429 Retry-After: 30` on `POST /research`.
- **Poison-pill guard:** Task timeout = `30s` (discovery/search), `60s` (deep fetch), `45s` (entity LLM), `20s` (verify per claim). Arq kills beyond `360s` per job.

### 4.3 Data Flow & Artefact Handoff

Artefacts are **never passed as queue payloads** (would exceed Redis limits). Only IDs are queued; artefacts live in Postgres:

```
PlannerOutput.plan → research_queries rows (+ research_runs.metadata)
DiscoveryOutput → documents rows (IDs returned, not content)
EntityResolverOutput → entities rows
DeepResearchOutput → documents + claims rows
VerificationOutput → claims.verification_status update + contradictions rows
SynthesisOutput → reports row + research_jobs.report
```

Queue payload:

```json
{"job_id": "uuid", "run_id": "uuid", "phase": "discovery", "shard_ids": ["uuid",...], "budget_snapshot": {...}}
```

---

## 5. Retry & Idempotency (Cross-Agent)

| Concern | Policy |
|---------|--------|
| **Transient LLM** (`rate_limited`, `timeout`, `503`) | Retry 3×, backoff + jitter, circuit breaker per provider/role |
| **Transient fetch** (`httpx.Timeout`, `429`, `5xx`) | Retry 3× per connector, then mark `retrieval_runs.status` accordingly, worker returns `partial` |
| **DB transient** (`asyncpg ConnectionError`) | Retry 2× at repo layer with new session |
| **Deterministic failure** (`4xx`, schema validation, CLAIM parse error) | No retry; mark artefact as failed with reason |
| **Idempotency** | Worker checks DB for existing artefacts by idempotency key before work; if found → return cached output (no LLM/fetch). Keys are `UNIQUE` where possible (`uq_documents_job_url`, `uq_entity_aliases`) |
| **Exactly-once semantics** | **Not claimed.** At-least-once with idempotent writes → effective exactly-once for artefacts, at-most-once cost accounting (cost row is insert-only, deduped by `run_id`+`agent`+`key`) |
| **Partial success** | Every output has `status=partial` mode; orchestrator decides whether to continue or short-circuit to `scoring/reporting` |

---

## 6. Budget Awareness (Cross-Agent, Hard + Soft)

```python
@dataclass
class BudgetSnapshot:
    soft_usd: float
    hard_usd: float
    spent_usd: float
    spent_tokens: int
    fetch_count: int
    soft_hit: bool
    hard_hit: bool

class BudgetController:
    def can_llm(self, est_cost: float, budget: BudgetSnapshot) -> bool: ...
    def can_fetch(self, budget: BudgetSnapshot) -> bool: ...
    def record_llm(self, cost: CostRecord, run_id: UUID) -> None: ...
    def record_fetch(self, run_id: UUID) -> None: ...
    def remaining(self, run_id: UUID) -> BudgetSnapshot: ...
```

- **Estimates:** `LLMProvider.estimate_cost` + heuristic `50 tokens per snippet` for discovery.
- **Enforcement:** Soft → degrade gracefully (planner emits fewer shards, discovery halves `max_results`, entity resolver skips tail docs, report falls back to template). Hard → stop new fan-out, drain in-flight, mark `partial_reason="budget_hard"`.
- **Per-agent pre-check:** Every agent's first await is `budget = controller.remaining(run_id); if budget.hard_hit: return partial`.
- **Config:** `configs/scoring/budget.yaml`:

```yaml
depth_budgets:
  quick:    { soft_usd: 1.0, hard_usd: 1.2, max_shards: 6,  max_iterations: 1 }
  standard: { soft_usd: 2.0, hard_usd: 2.4, max_shards: 12, max_iterations: 2 }
  deep:     { soft_usd: 5.0, hard_usd: 6.0, max_shards: 16, max_iterations: 3 }
per_claim_llm_cap_usd: 0.02
```

---

## 7. Observability Per Agent

- **Logs:** `structlog` with `agent`, `job_id`, `run_id`, `shard`, `connector`, `claim_id` in context. Log at `info` for phase transitions, `warning` for degraded/partial, `error` for failed (with `last_error` persisted).
- **Metrics (Prometheus):**

  - `planner_duration_ms`, `planner_shards_emitted`, `planner_llm_cost_usd`
  - `discovery_docs_total{connector, region}`, `discovery_duration_ms`, `discovery_dedup_stats`
  - `entity_resolution_entities_total`, `entity_alias_collapse_count`
  - `deep_research_iterations`, `gap_dimensions{dimension}`, `deep_docs_total`
  - `verification_claims_total{status}`, `contradictions_total{severity}`
  - `scoringDuration`, `report_duration_ms`, `report_citations_total`
  - `budget_spent_usd{run_id}`, `llm_cost_usd{role, model}`

- **Traces:** OTEL span per agent `run`, nested spans per connector search / LLM call / DB batch.
- **Health:** `/health` aggregates `LLMProvider.health_check` + `Redis ping` + `DB SELECT 1` + per-connector `health_check` (sample tier 1–2).

---

## 8. Error Handling & Escalation

- **Agent failure does not kill run** unless phase is `planning` or `reporting`. Discovery/Deep Research failures degrade to `partial`.
- **Max retries per phase:** 3 at task level + 3 at connector level. After retries, worker emits `partial` with `error` summary; orchestrator logs and continues to next phase if `can_partial_complete(current_status)` (see `lifecycle.py`).
- **Escalation:** After 3 task failures on same idempotency key, orchestrator marks `research_runs.error`, sets `research_jobs.last_error`, and moves run to `failed` (no silent loop).
- **Human-visible:** Every `partial`/`failed` carries `partial_reason` + `connector_statuses` so UI can show coverage report (see `docs/ARCHITECTURE.md` coverage example).

---

## 9. Testing Contracts

- Each agent has a `Stub`/`Recording` double:
  - `StubLLMProvider` (deterministic responses for unit tests),
  - `StubConnector` (in-memory RawResults),
  - `FakeBudgetController` (never hits limits unless test wants it).
- Unit tests: agent logic with stub deps, no IO.
- Integration tests: Postgres+Redis real, httpx mocked, `StubLLMProvider` (for vertical slice) or live `litellm` with `gpt-4o-mini` stub key for eval harness replay.
- Security tests: prompt-injection payloads through PLANNER and VERIFICATION (already in `tests/security/test_prompt_injection.py` — expand for planner).

---

## 10. Open Questions for Review

1. **Social worker scope:** V1 hard-limits to Reddit/X public. Confirm X API tier (free vs basic) and whether to stub X in Phase 1 if no key.
2. **Entity resolver deterministic merge threshold:** `cosine > 0.88` + domain match — confirm or make config-driven per `configs/scoring/entity.yaml`.
3. **Report fallback:** Template report without LLM if budget hard — confirm acceptable or require at least one LLM call for report polish.
