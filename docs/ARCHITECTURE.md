# Global Multi-Source Intelligence Engine V1 — Architecture Freeze

**Version:** V1.0 Freeze — Phase 0  
**Date:** 2026-08-26  
**Status:** FROZEN — No code changes beyond docs until human review  
**Workspace Root:** `C:\Opencode`  
**Target Subproject:** `evidence-engine/` (existing) → evolves into `global-intelligence-engine/` for V1  
**Stack Freeze:** Python 3.12+, FastAPI, PostgreSQL 16+pgvector, Redis (arq), httpx, Playwright, BeautifulSoup/trafilatura, Next.js/React, Docker Compose, pytest, pydantic-settings, structlog, litellm  
**Principles (priority order):** `CORRECTNESS → EVIDENCE → COVERAGE → COST → PERFORMANCE → UX`  
**Philosophy:** `DISCOVER BROADLY → VERIFY AGGRESSIVELY → SYNTHESIZE INTELLIGENTLY`

---

## 0. Executive Summary & Freeze Decision

### What V1 is
Evidence-first, multi-agent deep research engine that answers not *what can be found* but *what is supported, by whom, how independently, and how confidently*. V1 must deliver the 33-item MVP explicitly listed in the spec (prompt parsing through basic API+UI) without scope creep into crawlers, bypass, private social extraction, trading, custom model training, Neo4j, Kafka/K8s, billing, RBAC, multi-tenant, or fancy graph viz.

### Freeze scope
This document + 6 sibling docs + phased plan freeze the module boundaries, contracts, data model, state machine, and evaluation harness. No implementation beyond `docs/` until review sign-off.

### Where we are today (Repo Inspection Summary — full report in `docs/REPO_INSPECTION.md`)
`C:\Opencode` is a **shared workspace root** containing multiple historical prototypes. It is **NOT empty**. The relevant subproject `evidence-engine/` is **already ~45% toward V1** with typed Python, FastAPI, SQLAlchemy-async, pgvector, arq/redis intent, LiteLLM abstraction, and a two-pass orchestrator. **Recommendation: EVOLVE, not rewrite** — preserve reusable core, extend missing V1 subsystems, and align the repo structure to the V1 `global-intelligence-engine/` layout via incremental moves.

---

## 1. Logical Architecture

```
                            ┌──────────────────────────────────────────────┐
                            │              USER (API / Minimal UI)         │
                            └──────────┬───────────────────┬───────────────┘
                                       │                   │
                              ┌────────▼──────┐   ┌────────▼──────┐
                              │  Next.js Web  │   │  FastAPI /api │
                              │  (apps/web)   │   │  (apps/api)   │
                              └────────┬──────┘   └────────┬──────┘
                                       │                   │
                                       └─────────┬─────────┘
                                                 │
                                    ┌────────────▼─────────────┐
                                    │   RESEARCH API GATEWAY    │
                                    │  /research  /jobs  /eval  │
                                    │  typed schemas + auth stub│
                                    └────────────┬─────────────┘
                                                 │
                                    ┌────────────▼─────────────┐
                                    │    RESEARCH PLANNER       │
                                    │  (packages/planner)       │
                                    │  prompt→intent→plan→      │
                                    │  queries × regions × langs│
                                    └────────────┬─────────────┘
                                                 │
                                    ┌────────────▼─────────────┐
                                    │  DISCOVERY ORCHESTRATOR   │
                                    │  (packages/discovery)     │
                                    │  fan-out → parallel       │
                                    │  WEB / NEWS / SOCIAL /    │
                                    │  SPECIALIZED workers      │
                                    └────────────┬─────────────┘
                                                 │
                    ┌──────────────┬─────────────┼─────────────┬──────────────┐
                    │              │             │             │              │
             ┌──────▼──────┐ ┌────▼─────┐ ┌─────▼─────┐ ┌─────▼──────┐ ┌─────▼──────┐
             │ WEB SEARCH  │ │NEWS/ RSS │ │ SOCIAL    │ │ SPECIALIZED│ │ CRAWL/     │
             │ (search)    │ │ (search) │ │ (social)  │ │ (search)   │ │ EXTRACT    │
             │ Tavily/Serp │ │ GDELT/News│ │ Reddit/X  │ │ Regulatory │ │ (crawling) │
             │ Brave/SearX │ │ API/feeds │ │ public   │ │ DBs, Patents│ │ Playwright │
             └──────┬──────┘ └────┬─────┘ └─────┬─────┘ └─────┬──────┘ └─────┬──────┘
                    │             │             │             │              │
                    └─────────────┴──────┬──────┴─────────────┴──────────────┘
                                         │
                              ┌──────────▼──────────┐
                              │   DOCUMENT STORE    │
                              │  (packages/extraction│
                              │   + documents)      │
                              │  normalize→dedup→   │
                              │  pgvector embeddings│
                              └──────────┬──────────┘
                                         │
                              ┌──────────▼──────────┐
                              │  ENTITY RESOLUTION  │
                              │  (packages/entities)│
                              │  aliases, dedup,    │
                              │  candidate set      │
                              └──────────┬──────────┘
                                         │
                              ┌──────────▼──────────┐
                              │   CANDIDATE SET →   │
                              │   QUALIFICATION     │
                              │  deterministic rules│
                              └──────────┬──────────┘
                                         │
                              ┌──────────▼──────────┐
                              │   DEEP RESEARCH     │
                              │  (packages/research)│
                              │  per-entity deep    │
                              │  fetch, extraction  │
                              └──────────┬──────────┘
                                         │
                              ┌──────────▼──────────┐
                              │   GAP DETECTION →   │
                              │   RECURSIVE RESEARCH│
                              │  coverage matrix    │
                              │  budget-aware loop  │
                              └──────────┬──────────┘
                                         │
                              ┌──────────▼──────────┐
                              │  EVIDENCE ENGINE    │
                              │  (packages/evidence)│
                              │  CLAIM→EVIDENCE→    │
                              │  SOURCE→DOCUMENT    │
                              └──────────┬──────────┘
                                         │
                              ┌──────────▼──────────┐
                              │ VERIFICATION ENGINE │
                              │ (verify + contrad.) │
                              │ VERIFIED/SUPPORTED/ │
                              │ CONTESTED/UNVERIF/R │
                              └──────────┬──────────┘
                                         │
                              ┌──────────▼──────────┐
                              │   SCORING ENGINE    │
                              │  (packages/scoring) │
                              │  deterministic +    │
                              │  explainable conf.  │
                              └──────────┬──────────┘
                                         │
                              ┌──────────▼──────────┐
                              │  REPORT GENERATOR   │
                              │  citation-backed    │
                              │  markdown + JSON    │
                              └──────────┬──────────┘
                                         │
                                    ┌────▼────┐
                                    │  USER   │
                                    └─────────┘

        Cross-cutting:  LLMProvider (packages/llm)  •  SourceRegistry (packages/sources)
                        Configs (configs/regions/languages/sources/scoring)  •  Redis arq  •  Postgres+pgvector
                        Observability (structlog, OTEL, Prometheus)  •  BudgetController
```

### Layering and Dependency Direction (Enforced)

```
 configs/ (regions/languages/sources/scoring)  — pure data, no code deps
        ▲
 packages/core  (types, errors, Result, config, retry, circuit_breaker)  — depends on nothing
        ▲
 packages/llm  +  packages/sources  (registries, abstractions)
        ▲
 packages/extraction, documents, entities, evidence, claims  — depend only on core + llm + sources
        ▲
 packages/search, social, crawling  — depend on core + documents
        ▲
 packages/verification, confidence/scoring
        ▲
 packages/research, planner, discovery  — orchestration layer (depends on everything above)
        ▲
 apps/api, apps/worker, apps/web  — delivery layer
```

This is the **actual dependency graph currently approximated** in `evidence-engine/src` (see §3). V1 hardens it with import-lint / `import` rules in CI.

---

## 2. Module Boundaries & Package Map

### Proposed V1 Repo Structure (justification in §8)

```
global-intelligence-engine/               # ← evolution of evidence-engine/ (rename or keep alias)
  apps/
    api/          # FastAPI: /research, /jobs, /documents, /claims, /evidence, /eval, /sources
    worker/       # arq workers: discovery, deep_research, verification workers (same image, different entrypoint)
    web/          # Next.js minimal UI: submit job, view progress, view report, eval dashboard
  packages/
    core/         # types, enums, Result, config (pydantic-settings), retry, circuit_breaker, logging
    planner/      # PromptParser, QueryExpander, PlanningService (region/lang aware)
    discovery/    # DiscoveryOrchestrator (fan-out, budget, aggregation)
    search/       # Web/News search connectors (UnifiedSearchConnector interface)
    social/       # Social discovery (Reddit/X public only — V1 scoped)
    crawling/     # Fetch + extract (httpx + Playwright + trafilatura/BS4), robots.txt respect
    extraction/   # Content extraction, citation anchoring, chunking, embedding
    entities/     # Entity resolution, alias graph, candidate dedup
    evidence/     # Claim/Evidence/Source/Document ORM + repos, provenance, lineage
    research/     # Deep research, gap detection, recursive loop, state machine
    scoring/      # Deterministic ranking, confidence, explainability
    llm/          # LLMProvider (generate/structured_generate/stream/estimate_cost)
    sources/      # SourceRegistry, tier classification, authority/coverage
  configs/
    regions/      # e.g., us.json, eu.json, vn.json, ru.json, cn.json — searchable domains, languages
    languages/    # language-specific query templates, transliteration
    sources/      # source registry YAML/JSON (see SOURCE_MODEL.md)
    scoring/      # scoring weights YAML (deterministic, versioned)
  migrations/     # Alembic (single lineage from 001)
  tests/
    unit/         # pure logic, no IO
    integration/  # DB + Redis + httpx mock + LLM stub
    evals/        # benchmark harness (see EVALUATION.md)
  benchmarks/     # benchmark datasets (fixtures)
  docs/           # this freeze (7 docs + phased plan)
  docker-compose.yml
  pyproject.toml
  .env.example
```

### Current `evidence-engine/src` Mapping → V1

| Current (`evidence-engine/src`) | V1 `packages/` | Reuse Verdict | Notes |
|---|---|---|---|
| `core/` | `core/` | **KEEP** | Expand config with budget/stopping criteria; add typed `LLMProvider` contract |
| `llm/provider.py` | `llm/` | **KEEP + EXTEND** | Current has `complete/json`; add `generate/structured_generate/stream/estimate_cost`, role-to-model map, cost tracking |
| `connectors/base.py, web_search.py` | `search/` + `sources/` | **KEEP + SPLIT** | Split generic connector iface → `search`; move registry/tier logic → `sources` |
| `documents/` | `documents/` + `extraction/` | **KEEP + SPLIT** | Keep model/repo/dedup; move extraction to `extraction/`; add citation anchoring |
| `claims/` | `evidence/` (or `claims` stays) | **KEEP + RENAME** | Align to CLAIM→EVIDENCE→SOURCE→DOCUMENT; add `claim_sources` join |
| `provenance/` | `evidence/provenance` | **KEEP** | Add independence scoring, copy-graph via embeddings |
| `graph/` | `evidence/graph` or separate | **KEEP** | Current GraphNode/Edge is generic; keep for evidence graph overlay |
| `verification/` | `verification/` | **KEEP + EXTEND** | Add primary-source bias, temporal consistency, contradiction severity |
| `confidence/` | `scoring/` | **REFACTOR** | Merge deterministic scoring here; keep explainable breakdown |
| `research/` | `research/` + `planner/` + `discovery/` | **KEEP + SPLIT** | Current orchestrator is 2-pass; needs planner, discovery orchestrator, gap/recursive extraction |
| `reporting/` | `reporting/` (or `packages/reporting`) | **KEEP + EXTEND** | Add citation-backed report with claim-level anchors |
| `api/v1/` | `apps/api` | **KEEP + EXTEND** | Add `/research`, `/jobs/{id}/report`, `/eval` endpoints |
| — | `entities/` | **NEW** | Entity resolution + aliases (missing today — highest V1 gap) |
| — | `social/` | **NEW** | Public Reddit/X connectors (scoped, no private scrape) |
| — | `crawling/` | **NEW (partial)** | Fetch layer exists implicitly; extract to dedicated package with Playwright fallback |
| — | `tests/evals, benchmarks/` | **NEW** | Eval harness per EVALUATION.md |
| — | `configs/` | **NEW** | Region/lang/source/scoring configs (today hardcoded) |

**No Neo4j, Kafka, K8s, or microservice explosion in V1** — single Postgres+Redis+FastAPI+Worker image, Docker Compose.

---

## 3. Current Architecture: What Exists Today (Evidence Snapshot)

> Full inspection in `docs/REPO_INSPECTION.md`. Summary:

- **Language/runtime:** Python 3.12+, `pyproject.toml` with `fastapi>=0.115`, `sqlalchemy[asyncio]>=2.0`, `asyncpg`, `alembic`, `pydantic-settings`, `redis[hiredis]`, `litellm`, `httpx`, `arq`, `structlog`, `pgvector` — **matches V1 stack exactly**.
- **DB:** One Alembic revision `001 initial_tables` — tables `research_jobs`, `documents`, `claims`, `graph_nodes`, `graph_edges`, `source_lineages`, `contradictions`, `retrieval_runs`, `verification_runs`. Uses `pgvector VECTOR(1536)`. **Solid foundation but incomplete vs. Data Model (§V1)** — missing entities/aliases, funding/market tables, claim_sources, evidence, scores, benchmarks, research_queries/runs.
- **Research orchestration:** `ResearchOrchestrator` implements `PENDING→PLANNING→DISCOVERING→RETRIEVING→NORMALIZING→EXTRACTING→VERIFYING→RED_TEAM→REPORTING→COMPLETED/PARTIAL/FAILED` via `JobLifecycle` + `VALID_TRANSITIONS`. Two-pass model (discovery + adversarial). **Reuse: keep lifecycle engine, extend to V1 state machine (adds QUALIFY, DEEP RESEARCH, GAP, RECURSIVE, SCORE).**
- **LLM abstraction:** `LLMProvider` via `litellm.acompletion` with `LLMRole` → model map and `complete`/`json` methods. **Extend to V1 contract** (`generate`/`structured_generate`/`stream`/`estimate_cost` + cost accumulator).
- **Connectors:** `SourceConnector` Protocol with `search/fetch/health_check`; `web_search` concrete. **Extend to multi-region, multi-language, social/news/specialized.**
- **Documents:** SHA-256 dedup, URL+content-hash dedup, normalizer. **Extend with canonical URL, language detection, citation spans, chunking.**
- **Claims/Verification/Confidence:** Claim model with `verification_status`, `VerificationEngine` with 8-state statuses, `ContradictionEngine`, `AdversarialPass`, `ConfidenceScorer` with factor breakdown. **This is the most mature part — preserve scoring philosophy, add primary-source ratio and source-tier weighting.**
- **Tests:** 20+ unit tests + integration tests for pipeline/orchestrator + security prompt-injection suite. **Keep and grow; add eval benchmarks.**
- **Infra gaps vs V1:** No `configs/` for regions/langs/sources/scoring; no entity resolution; no budget controller; no deterministic ranking; no citation-backed report generator (stub); no social connectors; no eval harness; no minimal UI.

**Verdict:** **EVOLVE** — `evidence-engine/` is not a throwaway prototype; it is the correct seed. V1 adds ~55% new subsystems on top, refactors ~20% for boundary hardening, keeps ~25% as-is.

Conflicts to resolve before Phase 1:
- `research_jobs` table mixes job + run + coverage; V1 splits `research_jobs` / `research_runs` / `research_queries` (see DATA_MODEL.md).
- `claims.verification_status` string vs. typed `ClaimStatus` enum drift (8 states vs V1 5-state `VERIFIED/SUPPORTED/CONTESTED/UNVERIFIED/REFUTED` + mapping).
- `graph_nodes` generic vs. `companies/people/funding_rounds/investors/markets` domain tables — V1 adds domain tables and treats graph as projection, not primary store.
- Hard-coded `connector_timeout_seconds=30, max_results=20` must move to source registry + budget controller.

---

## 4. Dependency Inversion & Interfaces

### 4.1 LLM Abstraction (LLM-agnostic, testable)

**V1 Interface (`packages/llm/provider.py`):**

```python
class LLMProvider(Protocol):
    # Core (required for all 6 agents)
    async def generate(self, prompt: str, *, system: str = "", role: LLMRole,
                       temperature: float = 0.7, max_tokens: int | None = None) -> str: ...
    async def structured_generate(self, prompt: str, *, system: str = "",
                                  role: LLMRole, schema: type[BaseModel]) -> BaseModel: ...
    async def stream(self, prompt: str, *, system: str = "", role: LLMRole) -> AsyncIterator[str]: ...
    def estimate_cost(self, prompt_tokens: int, completion_tokens: int, role: LLMRole) -> float: ...

    # Helpers
    def model_for_role(self, role: LLMRole) -> str: ...
    async def health_check(self) -> bool: ...
```

- **Implementations:** `OpenAIProvider`, `AnthropicProvider`, `GeminiProvider`, `StubProvider` (for tests/evals), `RecordingProvider` (for eval harness).
- **Backed by `litellm`** in Phase 1 for speed; swappable in Phase 8. Config selects provider per role (e.g., reasoning→Anthropic, fast→OpenAI).
- **Cost accounting:** Every call emits `llm_call{role, model, prompt_tokens, completion_tokens, cost_usd}` to `research_runs` + Prometheus; `BudgetController` enforces hard/soft limits.
- **Determinism:** Verification/scoring never branch on raw LLM free-text; only on `structured_generate` with JSON schema + fallbacks to deterministic rules. Temperature 0.0–0.3 for extraction/verification; 0.7 only for query expansion.

### 4.2 Source Abstraction

```python
class SearchConnector(Protocol):
    name: str                          # registry key
    tier: SourceTier                   # 1-5
    regions: list[str]                 # e.g., ["us","eu","vn"]
    languages: list[str]
    access_method: Literal["api","rss","scrape","playwright"]
    async def search(self, q: SearchQuery) -> list[RawResult]: ...
    async def fetch(self, url: str) -> RawResult: ...
    async def health_check(self) -> bool: ...

@dataclass
class SearchQuery:
    query: str
    expanded_queries: list[str] = []     # from planner
    time_range: tuple[datetime|None, datetime|None] | None = None
    languages: list[str] = field(default_factory=lambda: ["en"])
    regions: list[str] = field(default_factory=lambda: ["us"])
    max_results: int = 20
    result_type: str = "all"             # all|news|social|academic
    budget_tokens: int | None = None     # passed to BudgetController

@dataclass
class RawResult:
    url: str; title: str; snippet: str; content: str | None = None
    published_at: datetime|None = None; author: str|None = None
    source_name: str = ""; tier: int = 5; language: str = "en"; region: str = "us"
    metadata: dict = field(default_factory=dict)  # authority hints, retrieval trace
```

- **Registry-driven:** Connectors self-register from `configs/sources/*.yaml` at startup. Adding a source = add a YAML, not code.
- **Source tiers 1-5** (see SOURCE_MODEL.md): Tier 1 primary/official (SEC filings, company registry, official domains), Tier 2 major reputable press, Tier 3 trade/regional, Tier 4 blogs/UGC, Tier 5 unverified/aggregation. Tier affects verification weighting, not censorship.

### 4.3 Worker & Queue Design (arq + Redis)

**No Kafka/K8s in V1.** Single `arq` queue on Redis, durable jobs in Postgres.

- **Queues:** `discovery`, `deep_research`, `verification`, `scoring` (logically separated by `job_id` correlation, physically one Redis).
- **Workers:** Same Docker image, different `arq` worker entrypoints. Horizontal scale by running more worker containers; no microservices.
- **Idempotency:** Every task key = `sha256(job_id + phase + input_hash)`. DB upsert with idempotency key; retries safe. `research_runs` records attempt count.
- **Retry:** `arq` retry with exponential backoff + jitter; circuit breaker (`core/circuit_breaker.py` exists) per connector/tier.
- **Observability:** `structlog` with `job_id/run_id/phase/connector/claim_id` baggage; Prometheus counters (`discovery_docs_total`, `verification_claims_total`, `llm_cost_usd`); OTEL traces across planner→discovery→verification→report.
- **Budget-aware scheduling:** `BudgetController` checks before each fan-out; if soft limit hit → still finish in-flight but no new recursive passes; if hard limit → mark `PARTIAL` with coverage report.

```
  FastAPI POST /research  → create research_jobs row (status=pending) → enqueue discovery
                                   │
          arq worker: DiscoveryOrchestrator fans out 8-16 search calls in parallel (asyncio.gather + semaphore)
                                   │  respects per-source rate limits, region/lang sharding
                                   ▼
                          documents + dedup → entity resolution → candidate set
                                   │
                          if gaps + budget remains → recursive deep_research tasks (bounded)
                                   │
                          verification (parallel per-claim) → scoring (deterministic) → report
                                   │
                          update research_jobs.report, status=completed/partial/failed
```

---

## 5. API Overview

### FastAPI — `apps/api` (typed, async, paginated)

```
POST   /api/v1/research              # create job: {query, depth, regions, languages, time_range, budget}
GET    /api/v1/research/{job_id}     # job status + coverage + budget consumed
GET    /api/v1/research/{job_id}/report           # citation-backed report (markdown + json)
GET    /api/v1/research/{job_id}/claims           # paginated claims with evidence
GET    /api/v1/research/{job_id}/evidence         # evidence spans
GET    /api/v1/research/{job_id}/documents        # documents with dedup info
GET    /api/v1/research                           # list history (paginated, filter by status/date)
POST   /api/v1/research/{job_id}/retry            # retry failed phase (idempotent)
GET    /api/v1/sources               # source registry (+ tiers, health)
GET    /api/v1/eval/benchmarks       # benchmark list
POST   /api/v1/eval/runs             # run eval (baseline_search | baseline_llm | engine)
GET    /api/v1/eval/runs/{run_id}    # eval results + comparison
GET    /api/v1/health                # liveness + dependency checks (DB, Redis, LLM)
```

All endpoints: `pydantic` request/response models, `structlog` request_id, `limit/offset` pagination, `ETag` for report, `429` with `Retry-After` on budget/rate limits.

### Minimal UI — `apps/web` (Next.js, no graph viz in V1)

- **Pages:** `/` (new research form: query, depth, region/language multi-select, time range, advanced: budget), `/jobs` (history table), `/jobs/[id]` (progress timeline + coverage bar + connector statuses + cost live), `/jobs/[id]/report` (citation-backed report, claim cards with evidence popover), `/eval` (benchmark runner + comparison table).
- **No fancy frontend:** Tailwind + shadcn-like primitives; no D3/graph viz until post-V1 (see FUTURE.md).
- **Realtime:** Polling `GET /research/{id}` every 2s during active phases; SSE/WebSocket deferred (not needed for V1).

---

## 6. Key Architectural Decisions (ADRs — Frozen)

| # | Decision | Alternatives Considered | Why This One | Trade-off |
|---|----------|------------------------|--------------|-----------|
| 1 | **Evolve `evidence-engine/`** not greenfield | Greenfield `global-intelligence-engine/` | 45% of V1 already exists typed+tested; migration is faster + preserves provenance | Rename confusion; mitigate with alias + docs |
| 2 | **PostgreSQL+pgvector as primary store** (no Neo4j) | Neo4j, separate vector DB | Spec says prefer PG unless insufficient; PG covers doc embeddings, graph projection is queryable via `graph_nodes/edges`; one fewer infra | Graph traversal less ergonomic; mitigate with indexed adjacency |
| 3 | **Single arq/Redis queue** (no Kafka) | Kafka, BullMQ, Celery+RabbitMQ | Anti-scope: Kafka is explicit out-of-scope; arq is async-native, typed, sufficient for V1 throughput | No multi-broker replay; acceptable for V1 |
| 4 | **LiteLLM-backed LLMProvider** with role map | Direct OpenAI/Anthropic SDKs, LangChain | V1 needs LLM-agnostic fast; LiteLLM unifies cost/model routing, keeps provider swap at config level | Extra dependency; mitigated by thin abstraction + stub provider |
| 5 | **Deterministic scoring, LLM only for extraction** | LLM judges confidence | Spec prioritizes evidence/deterministic components; LLMs hallucinate calibration; scoring is auditable math | Less "smart" scoring; mitigated by explainable factors |
| 6 | **Evidence-first schema: CLAIM→EVIDENCE→SOURCE→DOCUMENT** | Document-only or claim-only | Provenance requires join through evidence spans; supports citation-backed reports + contradiction at claim level | More joins; mitigated by indexes + materialized scores |
| 7 | **Source tiers 1-5 via registry YAML** | DB-only tiers, LLM-estimated authority | Config-driven tiers are versioned, reviewable, deterministically scored; LLM tier drift is risk | Manual curation; mitigated by quarterly registry review |
| 8 | **State machine with explicit QUALIFY + GAP + RECURSIVE** | Implicit loop in orchestrator | V1 phase names (PLAN→...→FINALIZE) + coverage dimensions require explicit states for budget/stopping criteria + observability | More states to maintain; mitigate with transition table + tests |
| 9 | **Minimal UI, API-first** | Full dashboard with graph viz | Spec caps fancy frontend as post-V1; minimal UI unblocks API consumers and evals | Less delight; acceptable for V1 |

---

## 7. Cross-Cutting Concerns (Frozen)

- **Budget Controls (hard + soft):** `BudgetController` tracks per-job `llm_cost_usd`, `llm_tokens`, `fetch_count`, `elapsed_ms`. Config `configs/scoring/budget.yaml` defines soft limit (e.g., $2/standard, $5/deep) and hard limit (+20%). Soft → no new recursive passes, still finish; Hard → abort and return `PARTIAL` with `budget_exhausted` reason + coverage report.
- **Idempotency:** DB unique constraints (`uq_documents_job_url`, idempotency keys on `research_runs`), upsert in repos, arq retry-safe workers.
- **Observability:** `structlog` JSON lines, correlation via `job_id`+`run_id`, Prometheus metrics, OTEL spans (exporter stub-pluggable), `research_runs` audit trail.
- **Reproducability:** `research_jobs` stores `normalized_query`, `planner_plan` JSON, `source_strategy`, `model_versions`, `config_hash`; eval runs record them.
- **Provenance:** Every claim stores `evidence_ids[]` → each evidence stores `document_id` + char offsets + `source_id`; `source_lineages` captures copy/derive/cite graph.
- **Security (V1 scope):** No login/CAPTCHA bypass, no private social scrape, no unauthorized scraping beyond `robots.txt`; `max_document_size_bytes=1MB`, `max_content_length=500k`, prompt-injection tests exist and expand for planner.
- **Error handling:** Typed `Result` monad (`core/types.py`), `LLMError` etc., `connector_statuses` partial success → `PARTIAL` not `FAILED`.

---

## 8. Repo Structure Justification

Why not separate repos? V1 is a **single deployable** with 3 entrypoints (api, worker, web) sharing `packages/`. Monorepo `global-intelligence-engine/` (or evolved `evidence-engine/`) keeps import boundaries explicit, allows `import-lint` enforcement, shares typed contracts, and runs one `docker-compose.yml` for local/eval. Micro-repos would add versioning friction for no isolation benefit at V1 scale.

`configs/` outside `packages/` because regions/languages/sources/scoring are **data, not code**, editable without redeploy, versioned, and loadable by both API and workers.

`tests/evals + benchmarks/` sibling to `packages/` because evals are first-class (not an afterthought) and must compare BASELINE SEARCH vs BASELINE LLM vs ENGINE on same datasets.

---

## 9. What Is Explicitly Out of Scope (Hard Gates)

- Full crawler / login / CAPTCHA / anti-bot bypass
- Unauthorized scraping or private social extraction (FB/LI/TikTok/IG private)
- Proprietary DB access without license
- Trading execution
- Custom LLM/embedding training or fine-tuning
- Neo4j (unless PG insufficient — not expected)
- Kafka/K8s/microservice explosion
- Mobile app, RBAC, billing, multi-tenant
- Fancy frontend / graph viz (minimal UI only)

Any PR introducing these in V1 must be rejected per review checklist. Deferred items recorded in `docs/FUTURE.md` with rationale + dependency.

---

## 10. Smallest Viable Vertical Slice (Proof of End-to-End)

> Full vertical slice spec in `docs/PHASED_PLAN.md` § Vertical Slice. Summary:

**Slice:** Single fixed query → planner with one expanded query → 2 web connectors (mocked in tests, Tavily+Brave in prod behind stub) → fetch top 5 docs → normalize+dedup → extract 3-5 claims via `StubProvider` → graph store → verify (one supporting, one missing → UNVERIFIED) → deterministic score → citation-backed markdown report → API `GET /research/{id}/report` + UI job page. Uses real Postgres+Redis, mock LLM, no entity resolution yet.

**Why this slice:** Proves HTTP→Planner→Discovery→Document→Claim→Verification→Scoring→Report loop, infrastructure, budget wiring, and evidence provenance with minimal external deps. Entity resolution, social, recursive, regional, and full tier logic layer on top without re-architecting slice.

**Infra for slice:** `docker-compose.yml` with `postgres:16+pgvector`, `redis:7`, `api` (FastAPI), `worker` (arq), `web` (Next.js dev). One `alembic upgrade head`. No Playwright in slice (httpx only).

---

## 11. Decisions Requiring Human Sign-Off (Open Questions)

1. **Naming:** Keep `evidence-engine/` or rename to `global-intelligence-engine/`? Recommendation: **Keep `evidence-engine/` alias, add `global-intelligence-engine/` as logical name in docs** to avoid git churn in Phase 1. Alias in `pyproject.toml` name or keep `evidence-engine` and document mapping.
2. **V1 ClaimStatus enum:** Map existing 8-state (`verified/probably_true/.../outdated`) to V1 freeze `VERIFIED/SUPPORTED/CONTESTED/UNVERIFIED/REFUTED` (see EVIDENCE_MODEL.md). Confirm mapping; no behavior change without sign-off.
3. **Embedding dimension:** Current `VECTOR(1536)` (OpenAI `text-embedding-3-small`). Freeze at 1536 for V1? Alternatives: 768/1024 for cheaper embeddings. Recommendation: **Freeze at 1536** (matches LiteLLM default, migration cost high).
4. **Source tier authority source of truth:** Registry YAML curated manually vs. LLM-assisted suggestion with human review. Recommendation: **YAML + CI check + quarterly review**; LLM can suggest but not auto-promote.
5. **API auth for V1:** Spec says minimal; `evidence-engine` has no auth. Recommendation: **API key header (`X-API-Key`) with stub + rate limits** in V1, defer OAuth/RBAC.
6. **Budget defaults:** Proposed `quick: $1 / standard: $2 / deep: $5` with hard=+20% — confirm cost targets for eval comparison.

**Freeze holds until these are resolved or explicitly deferred.**

---

## 12. References

- `docs/REPO_INSPECTION.md` — evidence for reuse/conflict table above
- `docs/DATA_MODEL.md` — PostgreSQL schema + pgvector + migrations
- `docs/AGENT_CONTRACTS.md` — 6 agent roles + parallel/retry/budget
- `docs/SOURCE_MODEL.md` — tier definitions + registry
- `docs/EVIDENCE_MODEL.md` — CLAIM→EVIDENCE→SOURCE→DOCUMENT + verification states
- `docs/RESEARCH_STATE_MACHINE.md` — full state machine + coverage + stopping criteria
- `docs/EVALUATION.md` — benchmarks A-H + harness + baselines
- `docs/FUTURE.md` — deferred items + rationale
- `docs/PHASED_PLAN.md` — Phases 0-9, DoD, risks, dependencies, vertical slice
- Spec doc: `docs/superpowers/specs/2026-08-25-evidence-intelligence-engine-design.md` (prior design)
- Orchestration plan: `docs/superpowers/plans/2026-08-25-evidence-engine-implementation.md`

---

**Prepared by:** AgentsOrchestrator (Lead Architect) — Phase 0 Freeze  
**Next:** Human review → Freeze sign-off → Phase 1 (Planner + LLMProvider V1 contract + vertical slice)
