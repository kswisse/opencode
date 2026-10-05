# PHASE 1 Implementation Audit — Repository Inspection

**Date:** 2026-08-27
**Workspace:** `C:\Opencode\evidence-engine`
**Baseline:** 124/124 tests passing (verified)
**Frozen Architecture Docs:** `docs/ARCHITECTURE.md`, `DATA_MODEL.md`, `AGENT_CONTRACTS.md`, `SOURCE_MODEL.md`, `EVIDENCE_MODEL.md`, `RESEARCH_STATE_MACHINE.md`, `EVALUATION.md`, `PHASED_PLAN.md`, `FUTURE.md`, `REPO_INSPECTION.md`
**Stack:** Python 3.12+, FastAPI, SQLAlchemy async + asyncpg, Alembic, pgvector VECTOR(1536), LiteLLM, Redis/arq intent, structlog, httpx, pytest

---

## 1. Audit Method

- `Get-ChildItem -Recurse` over `evidence-engine/`
- Read `pyproject.toml`, `alembic.ini`, `alembic/env.py`, `alembic/versions/initial_tables.py` (rev 001)
- Read `src/core/{config,types,errors,retry,circuit_breaker,security}.py`
- Read `src/llm/provider.py`, `src/connectors/{base,web_search,models,repository}.py`
- Read `src/documents/{models,normalizer,dedup,repository}.py`
- Read `src/claims/{models,extractor,repository}.py`, `src/verification/*`, `src/confidence/scorer.py`
- Read `src/research/{models,lifecycle,orchestrator,repository}.py`, `src/graph/*`, `src/provenance/*`, `src/reporting/*`
- Read `src/api/v1/{router,health,jobs}.py`, `src/api/deps.py`, `src/database.py`, `src/main.py`
- Ran `pytest -q` → 124 passed (collections: unit/integration/security)
- Compared existing schema (001) vs `docs/DATA_MODEL.md` DDL (002-005 target)

---

## 2. Existing vs Missing vs Conflict — Component Table

| Existing Component | Status | Reuse / Refactor / New | Files | Compatibility with Frozen Arch | Required Changes for Phase 1 |
|---|---|---|---|---|---|
| **Core types & enums** (`JobStatus`, `ClaimStatus`, `LLMRole`, `ResearchDepth`, `Result`) | ✅ Exists, typed, tested | **REUSE + EXTEND** | `src/core/types.py` | Partial — JobStatus missing DEDUP/QUALIFYING/GAP_DETECTING/DEEP_RESEARCHING/RECURSIVE/SCORING; ClaimStatus is 8-state not V1 5-state; LLMRole is legacy (FAST_MODEL etc) not V1 7-role map | Extend JobStatus with 6 new states + keep old; add V1 `VerificationStatus` enum mapping (8→5); introduce new `AgentLLMRole` (PLANNER/DISCOVERY/CLASSIFICATION/ENTITY_RESOLUTION/DEEP_RESEARCH/VERIFICATION/SYNTHESIS) alongside legacy for backward compat; keep Result monad as-is |
| **Core config** (`Settings` via pydantic-settings) | ✅ Exists, .env loading | **REFACTOR + EXTEND** | `src/core/config.py` (32 lines) | Low — only app/db/redis/LLM basic keys; missing typed layers for embeddings/research/budgets/sources/regions/scoring; connector knobs hard-coded; no YAML loading | Expand to layered config: add `EmbeddingSettings`, `BudgetSettings`, `ResearchSettings`, `ScoringSettings`, `ObservabilitySettings`; keep env for secrets/infra; add YAML loaders under `configs/` (models.yaml, budgets.yaml, scoring/, sources/, regions/, languages/); add `validate_at_startup()` that fails fast; no secrets in YAML |
| **Core errors & retry & circuit breaker** | ✅ Exists, typed | **REUSE** | `src/core/errors.py`, `retry.py`, `circuit_breaker.py` | Compatible — no conflict | Keep as-is; add `BudgetExceededError` for budget hard limit; ensure `LLMError` mapped to ModelRouter fallback |
| **Database & Alembic** | ✅ Exists, async SQLAlchemy + pgvector, single rev 001 | **REUSE + APPEND** | `src/database.py`, `alembic/env.py`, `alembic/versions/initial_tables.py`, `alembic.ini` | 001 matches DATA_MODEL §2.1 partially (9 tables); missing 14 V1 tables + column extensions | Keep 001 untouched; add 002 migration for `research_runs`, `research_queries`, `sources`, `entities`, `entity_aliases`, budget columns, region/run_id columns etc; add 003 for `scores` if needed but Phase 1 scopes 002 only for vertical slice; ensure `alembic upgrade head` from clean + existing; downgrade where practical; import new models in `env.py` |
| **Research jobs & lifecycle** | ✅ Exists (single table `research_jobs`) + state machine | **REFACTOR + SPLIT** | `src/research/models.py`, `lifecycle.py`, `repository.py`, `orchestrator.py` | Conflict — `research_jobs` mixes job+run+coverage; VALID_TRANSITIONS is 2-pass linear not V1 13-state; missing `research_runs`/`research_queries`, budget fields, config_hash, planner_plan | Preserve `ResearchJob` table via additive columns (not rewrite); create new `ResearchRun` + `ResearchQuery` models; extend `JobStatus` and `VALID_TRANSITIONS` to V1 13-state while keeping subset valid; add deterministic hash for job spec idempotency (`sha256(job+phase+hash)`); keep orchestrator skeleton but Phase 1 only implements job creation + discovery stub + state update, not full engine |
| **LLM provider** (LiteLLM `complete`/`json`) | ✅ Exists, litellm.acompletion, role→model stub | **KEEP + EXTEND** | `src/llm/provider.py` (68 lines) | Partial — only `complete`/`json`, no `generate`/`structured_generate`/`stream`/`estimate_cost`/`health_check`; role map hard-coded to gpt-4o | Extend to V1 contract: add `generate()` (alias complete), `structured_generate()` (pydantic schema), `stream()` (AsyncIterator), `estimate_cost()` (token→USD via LiteLLM pricing + role metadata), `model_for_role()`, `health_check()`; introduce `ModelRouter` layer above provider with YAML-driven role→model (Nemotron 3.5 Lightning/Ultra); preserve LiteLLM abstraction; keep `api_key` per-call; add `StubProvider`/`RecordingProvider` for tests |
| **Connectors** (`SourceConnector` protocol + web_search) | ✅ Exists, Protocol with search/fetch/health_check | **KEEP + SPLIT** | `src/connectors/base.py`, `web_search.py`, `models.py`, `repository.py` | Partial — only web_search concrete; missing region/lang fields, source registry, tier/authority, purpose; SearchQuery lacks regions/time_range/expanded_queries/budget_tokens | Keep protocol; split generic iface → `src/sources/` registry; add `SearchQuery` extensions (regions/languages/purpose/budget_tokens); keep `RetrievalRun` but add `run_id`; implement `SourceRegistry` loading YAML + DB cache `sources` table; preserve `web_search` as example |
| **Documents** (model/repo/dedup/normalizer) | ✅ Exists, SHA-256 dedup, URL+content-hash, pgvector | **KEEP + EXTEND** | `src/documents/models.py`, `normalizer.py`, `dedup.py`, `repository.py` | Compatible — dedup is exact URL + content_hash only, missing canonical_url logic, deterministic RAW→FETCH→NORMALIZE→HASH→DEDUP→STORE→METADATA pipeline, deterministic dedup reason, region/language/publisher fields | Keep model + auto hash; add `region` col extension, `content_hash` already; enhance `DocumentNormalizer` to retain source/URL/title/author/pub_date/retrieval time/language/content/hash/metadata; add `DeduplicationService` with deterministic ordering and `is_duplicate_of` pointer + `dedup_reason` enum; no near-duplicate vector yet (deferred); validate pipeline preserves metadata |
| **Claims / extractor** | ✅ Exists, Claim model + ClaimExtractor | **KEEP + ALIGN** | `src/claims/models.py`, `extractor.py` | Partial — verification_status string default unverified, 8-state drift; missing evidence/claim_sources/claim_evidence joins; embedding present | Keep table; add `run_id` nullable column via migration; map verification_status 8→5 is Phase 4 but Phase 1 should add V1 enum alias and keep string compat; extractor remains stubbed for Phase 1 slice |
| **Provenance & Graph** (SourceLineage, GraphNode/Edge) | ✅ Exists, independence, lineage, store | **KEEP** | `src/provenance/*`, `src/graph/*` | Compatible, generic graph overlay is V1 approach | Keep as-is for Phase 1; no changes required now; ensure imports in `alembic/env.py` remain |
| **Verification & Confidence** | ✅ Exists, deterministic matrix + ConfidenceScorer + Contradiction + Adversarial | **KEEP** | `src/verification/{engine,contradiction,adversarial,models,repository}.py`, `src/confidence/scorer.py` | Most mature, 8-state vs 5-state is only drift but Phase 1 does not run full verification | Keep without modification; note mapping `verified→VERIFIED` etc deferred to Phase 6; ensure no business logic depends on hard-coded 0.92 thresholds beyond EVIDENCE_MODEL |
| **API** (FastAPI jobs/health, deps) | ✅ Exists, stub endpoints | **REFACTOR** | `src/api/v1/{router,health,jobs}.py`, `src/api/deps.py`, `src/main.py` | Minimal — jobs endpoints return fake uuid/completed stub, not persisting; missing POST /research/jobs → create ResearchJob + persist + enqueue, GET /research/jobs/{id}, GET /health, optional cancel; business logic in routes (should use DI/service) | Replace stubs with real persistence: add `POST /research/jobs` (accept prompt → create ResearchJob + ResearchSpec + Run → enqueue arq → return job ID), `GET /research/jobs/{id}`, `GET /health` (DB/Redis/LLM checks); extract business logic to `src/research/service.py` + DI; use repository pattern; no hard-coded secrets/model names/rankings |
| **Reporting** | ✅ Exists, stub generator | **KEEP** | `src/reporting/generator.py` | Stub — not needed Phase 1 full but keep placeholder | Keep stub; Phase 1 integration test validates job persisted + worker loads + budget initialized + state updated + clean exit, not full report |
| **Testing harness** | ✅ 124 tests (unit/integration/security) | **KEEP + GROW** | `tests/{unit,integration,security}/*` | Compatible — no failures; missing 12 categories A-L tests for Phase 1 new subsystems | Keep all 124 green; add tests for config validation, model routing, ResearchSpec serialization, budget, source registry, entity repo, doc ingestion/dedup, migrations, worker idempotency, API job creation, error handling (mocks/fakes, no live LLM/search) |
| **Embedding system** | ✅ VECTOR(1536) via pgvector | **REUSE** | `src/documents/models.py`, `src/claims/models.py` (`VECTOR(1536)`) | Compatible — ARCHITECTURE §11 freezes 1536 | Keep VECTOR(1536) only; introduce `EmbeddingProvider` with dimension/embed/embed_batch + configurable dimension (default 1536) via config; pgvector only; no hard-coded 0.92 threshold; semantic similarity != truth |
| **Redis/arq worker** | ⚠️ Intent only (deps present, no worker) | **NEW** | `arq` in `pyproject.toml`, no worker code | Missing — need enqueue/execute/retry/failure/idempotency via sha256(job+phase+hash), structured logging | Create `src/worker/{tasks,queue,settings}.py` using arq+Redis only; implement idempotency, retry with backoff, structured logging with job_id/run_id/task_id/phase/role/model/source/timing/token/cost/status/error; no full orchestration yet |
| **Budget accounting** | ❌ Missing | **NEW** | — | Spec AGENT_CONTRACTS §6 + RESEARCH_STATE_MACHINE §4: soft 1.0/2.0/5.0 hard +20%, reserve/record_usage/remaining/can_continue/exceeded | Implement `src/budget/manager.py` BudgetManager tracking LLM calls/tokens/cost (estimated+actual), search calls, docs, iterations; soft/hard enforcement before expensive work; recursive research cannot bypass |
| **Source registry + YAML** | ❌ Missing (source_id free string only) | **NEW** | — | SOURCE_MODEL.md registry schema 1.2 | Implement `src/sources/{registry,models,repository,connector}.py` + `configs/sources/*.yaml` seeded V1 set (small useful set, not hard-coded rankings): tavily, brave, sec_edgar, gnews/news, reddit_public etc; fields source_id/name/domain/country/region/language/source_type/authority_level/purpose DISCOVERY/VERIFICATION/CONTEXT/access_method/enabled; validation at startup |
| **Entity repository** | ❌ Missing | **NEW** | — | DATA_MODEL §2.4: entities/entity_aliases/companies/people | Implement `src/entities/{models,repository}.py` CRUD + find/search by alias/canonical; no sophisticated probabilistic resolution yet; UNIQUE (job_id, entity_type, normalized_name); gin trigram indexes |
| **ResearchSpec** | ❌ Missing | **NEW** | — | Must be typed/serializable/persistable/versioned, idempotent via deterministic hashes | Implement `src/research/spec.py` / `schemas.py` with fields objective, entity_type, geography, regions, countries, languages, industries, inclusion_criteria, exclusion_criteria, research_dimensions, source_classes, depth, budget, max_iterations/max_candidates/max_documents/max_cost, created_at; versioned + hash |
| **Config YAML bundle** | ❌ Missing (`configs/` dir absent) | **NEW** | — | ARCHITECTURE §2 configs pure data, no code deps | Create `configs/models.yaml`, `budgets.yaml`, `scoring/`, `sources/`, `regions/`, `languages/` with validation; ensure no secrets in YAML |
| **Observability** | ⚠️ Partial (structlog dep, no structured logging) | **NEW/EXTEND** | `structlog` in deps but not wired | Need structured logging with job_id/run_id/task_id/phase/role/model/source/timing/token/cost/status/error | Add `src/core/logging.py` + `src/observability/*` with structlog JSON, correlation context vars, no secrets |
| **Migrations 002+** | ❌ Missing (only 001) | **NEW** | `alembic/versions/initial_tables.py` only | DATA_MODEL.md plans 002 v1_entities_sources_evidence, 003 v1_budget_scores, 004 constraints, 005 verification status | For Phase 1 minimal slice, 002 must cover research_runs, research_queries, sources, entities/entity_aliases, run_id/region/budget cols; keep append-only, preserve backward compat |
| **API budget integration** | ❌ Missing | **NEW** | — | Phase 1 pipeline PROMPT→ResearchSpec→DISCOVERY→DOCUMENT INGESTION→ENTITY→EVIDENCE in later phases | Phase 1 only implements PROMPT→ResearchSpec→DISCOVERY→DOCUMENT INGESTION→ENTITY (+ evidence infra stub) via job endpoint + worker foundation |

---

## 3. Compatibility & Conflict Summary

- **No Kafka/Neo4j/K8s/crawler/bypass/private social** — existing codebase has none; Phase 1 must not introduce.
- **Three configurability mandates enforced:**
  - Embedding dimension: existing VECTOR(1536) matches mandate; Phase 1 must add `EmbeddingProvider` with configurable dimension (default 1536) and not hard-code elsewhere.
  - Evidence thresholds: existing scorer uses deterministic factors but check for hard-coded 0.92 snippet validation threshold — must move to `configs/scoring/` and separate semantic relevance/source authority/claim alignment/extraction quality/temporal relevance; semantic similarity != truth.
  - Budget: existing has none; Phase 1 must implement quick/standard/deep as configurable YAML defaults (e.g. 1.0/2.0/5.0 USD hard/soft, change without code).
- **Backward compatibility:** 001 tables remain; 002+ adds nullable/defaulted columns first, backfills, then constraints; existing 124 tests must stay green.
- **Import boundaries:** V1 layering `configs → core → llm+sources → extraction/documents/entities/evidence → search/social → verification/scoring → research/planner/discovery → apps` must be hardened but Phase 1 only introduces foundation, no circular deps.

---

## 4. Reuse Strategy

- **REUSE as-is (no rewrite):** `core/errors`, `core/retry`, `core/circuit_breaker`, `core/security`, `provenance/*`, `graph/*`, `verification/*` (except enum map), `confidence/scorer`, `documents` dedup logic, `llm` litellm core, `database.py` engine, test harness.
- **REFACTOR (extend, not replace):** `core/config.py`, `core/types.py`, `llm/provider.py`, `connectors/base.py`, `documents/models`+`normalizer`, `research/models`+`lifecycle`+`orchestrator`, `api/v1/jobs`, `alembic/env.py`, `main.py`.
- **NEW (create):** `configs/` bundle, `src/sources/` registry, `src/entities/` repo, `src/research/spec.py`+`service.py`, `src/budget/manager.py`, `src/worker/*`, `src/embeddings/*`, `src/observability/*`, migrations 002, integration test.

---

## 5. Gaps Explicitly Deferred (Not Phase 1 Scope)

- Full research engine (deep research, gap detection, recursive loop, verification engine 5-state, scoring report) — Phase 1 only infra foundations + vertical slice skeleton.
- Knowledge graph (Neo4j) — out of scope per freeze.
- Crawler/bypass/playwright private social extraction — out of scope, hard guard.
- UI (`apps/web`) — minimal API only in Phase 1.
- Eval harness (`benchmarks/`, `evals/`) — Phases 7+.
- Full multi-region/lang sharding — planner stub in Phase 1.

---

## 6. Audit Conclusion

- **Baseline is solid:** 124/124 green, typed Python, async SQLAlchemy, pgvector 1536, LiteLLM intent, document dedup working.
- **Phase 1 is additive:** ~55% new subsystems on top of 45% reusable core; no rewrite of working components; migrations append-only.
- **Risks mitigated:** keep 001 untouched, use deterministic dedup + idempotency hashes, enforce budget before expensive work, validate configs at startup, mocks for tests.
- **Ready for STEP 2:** Create `docs/PHASE1_IMPLEMENTATION_PLAN.md` (or inline plan) then execute Steps 3-15 sequentially.

**Auditor:** AgentsOrchestrator — Phase 1 Lead
**Next:** STEP 2 Phase 1 implementation plan → STEP 3 Configuration + model routing
