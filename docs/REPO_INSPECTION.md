# Repo Inspection Report — Global Multi-Source Intelligence Engine V1

**Date:** 2026-08-26  
**Workspace:** `C:\Opencode`  
**Target:** `evidence-engine/` (existing subproject)  
**Inspector:** AgentsOrchestrator  
**Method:** `Get-ChildItem -Recurse`, read of `pyproject.toml`, `alembic/versions/initial_tables.py`, `src/*/models.py`, `src/research/orchestrator.py`, `src/llm/provider.py`, `src/core/{types,config}.py`, `src/documents/*`, `src/verification/engine.py`, plus `docs/superpowers/specs/2026-08-25-evidence-intelligence-engine-design.md`

---

## 1. Is This a New Project or Existing?

**Answer: EXISTING — substantial, reusable foundation (~45% of V1).**

Evidence:

- `pyproject.toml` at `evidence-engine/pyproject.toml` declares `name=evidence-engine version=0.1.0` with full prod deps (`fastapi`, `sqlalchemy[asyncio]`, `asyncpg`, `alembic`, `pydantic-settings`, `redis[hiredis]`, `litellm`, `httpx`, `arq`, `structlog`, `pgvector`) matching V1 stack exactly.
- `src/` contains 13 packages: `core`, `api`, `connectors`, `documents`, `claims`, `graph`, `provenance`, `verification`, `confidence`, `research`, `reporting`, `llm` — typed, async, with repos + models + engines.
- `alembic/versions/001 initial_tables.py` creates 9 tables with indexes, FKs, `VECTOR(1536)`, JSON columns.
- `tests/` has ~22 unit tests + integration (`test_full_pipeline`, `test_orchestrator`) + security (`test_prompt_injection`), all pytest-asyncio.
- `docs/superpowers/specs/2026-08-25-evidence-intelligence-engine-design.md` (36,520 bytes) and `docs/superpowers/plans/2026-08-25-evidence-engine-implementation.md` (95,898 bytes) define a prior evidence-engine iteration that this code implements.
- `C:\Opencode` itself is a workspace root git repo (branch `master`, ~10 recent commits around `ai-workforce-platform` auth/JWT + pipeline), containing parallel prototypes (`ai-startup-analyst`, `clipping-agent`, `smart-clock`, `ai-workforce-platform`, `evidence-engine`). `evidence-engine` is a **nested git repo** (`.git` inside) — independent history.

**Conclusion:** Not empty/template. Treat as **seed to evolve**, not greenfield.

---

## 2. Top-Level Inventory

```
C:\Opencode
  .git/                          # workspace root git (master)
  .opencode/agents/              # 200+ agent definitions
  .superpowers/sdd/              # task reports for ai-workforce-platform
  docs/architecture/{01-overview,02-schema-org,03-schema-agents}.md
  docs/superpowers/plans|specs/  # including 2026-08-25 evidence-engine docs
  docs/workflows/{REGISTRY,WORKFLOW-*.md}
  ai-startup-analyst/           # Next.js project (unrelated)
  ai-workforce-platform/        # Python FastAPI + Postgres (unrelated, mature)
  clipping-agent/
  smart-clock/                  # ESP32 + webapp (unrelated)
  simplefeedback/
  evidence-engine/             # ⭐ THIS PROJECT
    .git/                      # nested repo
    src/                       # 13 packages, 30+ models/engines
    tests/{unit,integration,security}/
    alembic/{env.py, versions/initial_tables.py}
    alembic.ini
    pyproject.toml
    (no docker-compose.yml, no .env.example, no configs/, no apps/web, no benchmarks/)
  agent.zip (1.3 MB)
```

---

## 3. What Exists — Detailed Map

### 3.1 `src/core`
- `types.py`: `Result` monad (`Ok`/`Err`), enums `JobStatus` (12 states incl. PARTIAL), `PassType`, `ClaimStatus` (8 states), `ConnectorStatus`, `LineageRelationship`, `GraphNodeType`, `GraphEdgeType`, `LLMRole` (5 roles), `ResearchDepth` (quick/standard/deep). Typed, frozen dataclasses.
- `config.py`: `Settings(BaseSettings)` with `database_url`, `redis_url`, `llm_api_key/model/embedding_model`, retry knobs, connector timeout/max_results, security limits. Loads `.env`.
- `errors.py`, `retry.py`, `circuit_breaker.py`, `security.py`: circuit breaker, exponential retry, prompt-injection defenses (referenced by tests).
- **Reuse: 95%** — add budget fields, move connector consts to registry.

### 3.2 `src/research`
- `models.py`: `ResearchJob` (SQLAlchemy, mapped to `research_jobs`) with `query`, `normalized_query`, `status`, `current_pass`, time_range, languages, depth, source_strategy, timestamps, retry, result counters, `connector_statuses` JSON, `report` text.
- `lifecycle.py`: `JobLifecycle` + `VALID_TRANSITIONS` dict (strict state machine), `can_partial_complete`, `InvalidTransition`.
- `orchestrator.py`: `ResearchOrchestrator(connectors, llm)` with `execute(job_id, query)` performing 8 phases: PLANNING→DISCOVERING (fan-out connectors)→RETRIEVING (normalize)→NORMALIZING (dedup)→EXTRACTING (LLM claim extract)→VERIFYING (graph evidence)→RED_TEAM (adversarial)→REPORTING (partial vs completed). Uses `SearchQuery`, `DocumentNormalizer`, `Deduplicator`, `ClaimExtractor`, `EvidenceGraphStore`, `VerificationEngine`, `ContradictionEngine`, `AdversarialPass`, `ConfidenceScorer`.
- **Reuse: 70%** — keep lifecycle engine + orchestrator skeleton, split planner/discovery into dedicated packages, add QUALIFY/DEEP_RESEARCH/GAP/RECURSIVE/SCORE states per V1.

### 3.3 `src/connectors`
- `base.py`: `SearchQuery`, `RawResult`, `ConnectorStatusInfo`, `SourceConnector` Protocol (`search`, `fetch`, `health_check`, `name`).
- `web_search.py`: concrete web connector (httpx-based).
- `models.py`/`repository.py`: `RetrievalRun` table tracking per-connector runs.
- **Reuse: 60%** — keep protocol, split into `packages/search` (+news) and `packages/sources` registry, add region/lang fields.

### 3.4 `src/documents`
- `models.py`: `Document` with `job_id`, `source_id`, `url`, `canonical_url`, `title`, `author`, `publisher`, `published_at`, `retrieved_at`, `language`, `content`, `content_hash` (auto SHA-256), `mime_type`, `is_duplicate_of`, `dedup_reason`, `metadata` JSON, `embedding VECTOR(1536)`.
- `normalizer.py`, `dedup.py`: exact URL, canonical URL, content-hash dedup.
- `repository.py`: CRUD with async session.
- **Reuse: 85%** — add language detection, citation spans, chunking, canonicalization rules.

### 3.5 `src/claims`
- `models.py`: `Claim` with `job_id`, `document_id`, `normalized_text`, `subject/predicate/object` (triple), `event_time`, `extraction_confidence`, `verification_status` (string, default `unverified`), `verification_reasoning`, `embedding VECTOR(1536)`.
- `extractor.py`: `ClaimExtractor(llm)` using LLM to extract claims.
- **Reuse: 80%** — align status enum to V1 (5-state), add `claim_sources`/`evidence` join.

### 3.6 `src/provenance` & `src/graph`
- `models.py`: `SourceLineage` (document_a→document_b, relationship, confidence, evidence), `GraphNode`/`GraphEdge` with type, metadata, indexes.
- `independence.py`, `lineage.py`, `store.py`: independence analysis, lineage building, graph store query (`get_supporting_evidence`, `get_contradicting_evidence`).
- **Reuse: 75%** — keep, add copy-graph via embeddings + tier-aware independence scoring.

### 3.7 `src/verification` & `src/confidence`
- `engine.py`: `VerificationEngine.verify_claim` with deterministic matrix (VERIFIED if sup≥2 no con; PROBABLY_TRUE if sup=1; PARTIALLY_SUPPORTED, CONTESTED, PROBABLY_FALSE, FALSE, UNVERIFIED), `ConfidenceFactors`, `iterative_verify`.
- `contradiction.py`, `adversarial.py`: contradiction detection, adversarial pass.
- `confidence/scorer.py`: `ConfidenceScorer.score` producing `ExplainableConfidence` (final_score 0-1, supporting/weakening factors, factor breakdown 8 dims).
- **Reuse: 90%** — most mature; add primary-source ratio, tier weighting, temporal consistency from provenance.

### 3.8 `src/llm`
- `provider.py`: `LLMProvider(api_key, model)` with `_model_for_role`, `complete(prompt, system_prompt, role, temperature)` via `litellm.acompletion`, `json(prompt,...)` with code-fence stripping + JSON parse. Role map FAST/REASONING/EXTRACTION/VERIFICATION/VISION → `gpt-4o-mini`/`gpt-4o`.
- **Reuse: 65%** — keep litellm core, extend to V1 contract (`generate/structured_generate/stream/estimate_cost`), add cost tracking + stub/recording providers.

### 3.9 `src/api` & `src/database`
- `api/v1/{router,health,jobs}.py`: minimal jobs/health endpoints, `deps.py` for DB session.
- `database.py`: `engine = create_async_engine(settings.database_url)`, `async_session`, `Base(DeclarativeBase)`, `get_db()` yield with commit/rollback.
- `alembic/env.py`: async migrations, imports all models for autogenerate.
- **Reuse: 80%** — expand API surface per §5 of ARCHITECTURE.md; keep DB layer.

### 3.10 Tests
- `tests/unit`: 20+ files (circuit_breaker, claims, confidence, config, connectors, documents, graph, llm_provider, provenance, reporting, research_models, verification, etc.) — all passing previously per task reports.
- `tests/integration`: `test_full_pipeline`, `test_orchestrator`.
- `tests/security`: `test_prompt_injection`.
- **Reuse: 100%** — keep, add eval harness + region/lang + budget tests.

---

## 4. Current Schema Snapshot

**One migration `001`** (see `alembic/versions/initial_tables.py`):

| Table | Columns (key) | Indexes | FKs | PG Types |
|-------|---------------|---------|-----|----------|
| `research_jobs` | id UUID PK, query Text, normalized_query Text, status String(50), current_pass String(50), time_range_start/end DateTime tz, languages JSON, depth String(50), source_strategy String(50), created_at/started_at/completed_at DateTime tz, retry_count/max_retries Int, last_error Text, total/retrieved docs, claims_extracted, contradictions_found, connector_statuses JSON, report Text | status, created_at | — | — |
| `documents` | id UUID PK, job_id UUID FK, source_id String(255), url Text, canonical_url Text, title Text, author/publisher String(500), published_at/retrieved_at DateTime tz, language String(10), content Text, content_hash String(64), mime_type String(100), is_duplicate_of UUID self-FK, dedup_reason String(100), metadata JSON, embedding VECTOR(1536) | job_id, content_hash, canonical_url, source_id | research_jobs.id, documents.id | pgvector |
| `claims` | id UUID PK, job_id FK, document_id FK, normalized_text Text, subject/predicate/object String(500), event_time DateTime tz, extraction_confidence Float, verification_status String(50), verification_reasoning Text, embedding VECTOR(1536) | job_id, document_id, verification_status | research_jobs, documents | pgvector |
| `graph_nodes` | id UUID PK, node_type String(50), node_id UUID, metadata JSON, created_at DateTime tz | node_type, node_id, (type,id) | — | — |
| `graph_edges` | id UUID PK, source_node_id FK graph_nodes, target_node_id FK, edge_type String(50), metadata JSON, created_at | source, target, type, (source,target) | graph_nodes | — |
| `source_lineages` | id UUID PK, document_a_id FK docs, document_b_id FK docs, relationship String(50), confidence Float, evidence Text, metadata JSON, created_at | doc_a, doc_b | documents | — |
| `contradictions` | id UUID PK, job_id FK, claim_a_id FK claims, claim_b_id FK claims, contradiction_type String(100), severity String(20), description Text, metadata JSON, created_at | job_id, claim_a, claim_b | research_jobs, claims | — |
| `retrieval_runs` | id UUID PK, job_id FK, connector_name String(100), status String(50), documents_retrieved Int, error Text, started_at/completed_at DateTime tz, metadata JSON, created_at | job_id | research_jobs | — |
| `verification_runs` | id UUID PK, job_id FK, round_number Int, claims_verified/contradictions_detected Int, duration_ms Int, metadata JSON, created_at | job_id | research_jobs | — |

**Missing vs V1 DATA_MODEL.md (see that doc for full DDL):**
- `research_runs`, `research_queries`, `entities`, `entity_aliases`, `companies`, `people`, `funding_rounds`, `investors`, `markets`, `evidence`, `claim_sources`, `claim_evidence`, `scores`, `social_posts`, `social_authors`, `benchmarks`, `eval_runs` + join tables.
- `sources` registry table or YAML+loader (currently `source_id` string only, no tier/authority/config).
- `documents` missing `region`, `citation_spans`, chunking linkage.

---

## 5. Reusable Components to Preserve (Do-Not-Rewrite)

1. **Core type system + Result monad + enums + valid-transitions map** — already typed and tested.
2. **LLMProvider litellm core** — extend, not replace.
3. **Document dedup (URL + content-hash)** — keep logic, parameterize via registry.
4. **VerificationEngine deterministic matrix + ConfidenceScorer factor breakdown** — the auditability core.
5. **SourceLineage / EvidenceGraphStore query layer** — independence + graph traversal.
6. **Alembic setup + async SQLAlchemy + pgvector** — migration lineage from 001 is correct.
7. **Test harness** — pytest-asyncio + conftest + security suite.

---

## 6. Conflicts Between Existing Code and V1 Spec

| # | Conflict | Existing | V1 Requirement | Resolution (Freeze) |
|---|----------|----------|----------------|----------------------|
| 1 | **Job vs Run vs Query** | Single `research_jobs` with `connector_statuses` JSON | Spec requires `research_jobs` (user intent) + `research_runs` (execution attempt) + `research_queries` (expanded queries × regions × langs) | Split: keep `research_jobs` for intent/history, add `research_runs` (per-execution with status, started/completed, cost, partial reason) and `research_queries` (one row per expanded query + region + lang). Migrate `connector_statuses` → `retrieval_runs` stays, link to `research_runs`. |
| 2 | **ClaimStatus drift** | 8-state enum (`verified`, `probably_true`, `partially_supported`, `contested`, `unverified`, `probably_false`, `false`, `outdated`) + string column | V1 freeze: `VERIFIED / SUPPORTED / CONTESTED / UNVERIFIED / REFUTED` + explainable confidence 0-1 | Map: `verified→VERIFIED`, `probably_true/partially_supported→SUPPORTED`, `contested→CONTESTED`, `probably_false/false/outdated→REFUTED`, `unverified→UNVERIFIED`. Keep `confidence` float separate. Add migration to new enum check; keep legacy string for 1 release with view. |
| 3 | **Graph as primary vs projection** | `graph_nodes/edges` generic, used as evidence graph | V1 requires domain tables (`companies`, `people`, etc.) plus evidence graph as projection | Add domain tables; keep graph tables as evidence-graph overlay indexed by `node_type`. Do not replace with Neo4j. |
| 4 | **Hard-coded connector knobs** | `settings.connector_timeout_seconds=30`, `connector_max_results=20` | V1 requires per-source `timeout`, `max_results`, `rate_limit`, `tiers`, `regions`, `languages` in registry | Move defaults to `configs/sources/*.yaml`; `settings` becomes fallback only. |
| 5 | **LLM contract** | `complete`/`json` only | V1 requires `generate/structured_generate/stream/estimate_cost` | Extend class; keep backwards compat aliases (`complete→generate`). |
| 6 | **State machine** | 2-pass linear (`DISCOVERING→RETRIEVING→NORMALIZING→EXTRACTING→VERIFYING→RED_TEAM→REPORTING`) | V1 requires `PLAN→DISCOVER→NORMALIZE→DEDUP→QUALIFY→DEEP RESEARCH→GAP DETECTION→RECURSIVE→VERIFY→SCORE→FINALIZE` with coverage dims | Extend `VALID_TRANSITIONS` + add `QUALIFY`, `DEEP_RESEARCH`, `GAP_DETECTION`, `RECURSIVE`, `SCORE` states; keep existing as subset. |
| 7 | **No entity resolution** | None | V1 33 items includes entity resolution + aliases | Add `packages/entities` + `entities`/`entity_aliases` tables; no breaking change to existing docs/claims. |
| 8 | **No region/lang/config extensibility** | Hard-coded `["en"]` | Multi-region, multi-language | Add `configs/regions`, `configs/languages`, `configs/sources`, `configs/scoring`; planner reads them. |
| 9 | **No budget/stopping criteria** | None | Budget controls + stopping criteria required | Add `BudgetController` + `research_runs.cost_*` + `configs/scoring/budget.yaml`. |
| 10 | **No deterministic ranking** | `ConfidenceScorer` only | Deterministic ranking tier-aware | Add `packages/scoring/ranker.py` using source tiers + recency + coverage. |
| 11 | **Report stub** | `reporting/generator.py` minimal, `research_jobs.report` text only | Citation-backed reports with anchors | Extend generator to produce claim-anchored markdown + JSON; store in `reports` table or keep text column + sidecar. |
| 12 | **No source registry/tier** | `source_id` free string | Source registry + tier 1-5 configurable | Add `sources` table or YAML registry (freeze: YAML + DB cache). |
| 13 | **No eval benchmarks** | None | Eval benchmarks A-H + harness | Add `benchmarks/` + `eval_runs` + `tests/evals`. |

---

## 7. Conventions & Infra Already Configured

- **Python:** `>=3.12`, `hatchling` build, `pytest asyncio_mode=auto`.
- **DB:** `postgresql+asyncpg`, `Base(DeclarativeBase)`, async sessions, Alembic async env.
- **Redis:** `redis[hiredis]`, `arq` (worker lib) — no `docker-compose.yml` yet in `evidence-engine/` but `ai-workforce-platform/docker-compose.yml` shows pattern (PG+Redis+API). Reuse template.
- **Logging:** `structlog` + stub `observability/` in sibling project; ready to wire OTEL.
- **Env:** `pydantic-settings` with `.env` file.
- **Security:** `max_document_size_bytes`, `max_content_length`, prompt-injection suite — good V1 base.
- **Git:** Nested repo per subproject; workspace root git tracks cross-cutting docs. Recommend keeping `evidence-engine` as canonical for V1 (single migration lineage), workspace root `docs/` as freeze source of truth.

---

## 8. Decision: New vs Existing Path

**Path: EVOLVE `evidence-engine/` into `global-intelligence-engine` V1.**

- Rename is logical, not physical in Phase 1 (keep folder name, document logical name).
- Migrate incrementally: add entities, source registry, budget controller, region/lang configs, scoring ranker, eval harness on top of existing tables.
- Hard gates: no overwrite of `001` migration; all new changes append as `002_v1_entities_and_registry`, `003_v1_budget_and_runs`, etc.
- Test gate: existing 30+ tests must stay green throughout V1.

---

## 9. Immediate Blockers/Risks from Inspection

- No `docker-compose.yml` in `evidence-engine/` → Phase 1 must add Compose (PG+pgvector+Redis+API+Worker) or eval/repro impossible.
- No `.env.example` → add before onboarding.
- `Claim.verification_status` string column risks drift → freeze enum mapping this doc.
- `Document.embedding` + `Claim.embedding` both `VECTOR(1536)` but no index strategy (IVFFLAT/HNSW) → define in DATA_MODEL.md (HNSW, `m=16`, `ef_construction=64`).
- `graph_nodes.node_id` is polymorphic → needs check constraint or app-level guard.

---

**Sign-off:** This inspection is evidence for ARCHITECTURE.md §3 and DATA_MODEL.md migration strategy. No code change implied; next is phased plan.
