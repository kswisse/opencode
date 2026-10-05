# PHASE 1 Implementation Plan — Derived from Actual Codebase

**Date:** 2026-08-27  
**Based on:** `PHASE1_IMPLEMENTATION_AUDIT.md` + 124 tests green + frozen docs  
**Objective:** Build infra for vertical slice: config → LLM routing → ResearchSpec → source registry → entity persistence → document ingestion → migrations → worker foundation → budget → observability → API → integration test  
**Constraint:** Evolve `evidence-engine/`, not rewrite; 001 untouched; all 124 baseline must stay green

---

## Implementation Order & Dependencies

```
STEP 1 Audit (done) ─▶ STEP 2 Plan (this doc) ─┬─▶ STEP 3 Config + Model Routing
                                               ├─▶ STEP 4 ResearchSpec + Job Persistence (depends 3 for budget defaults)
                                               ├─▶ STEP 5 Budget Manager (depends 3,4)
                                               ├─▶ STEP 6 Source Registry (depends 3)
                                               ├─▶ STEP 7 Entity Repo (depends 9 migration)
                                               ├─▶ STEP 8 Document Ingestion (depends 3,6,7)
                                               ├─▶ STEP 9 Migrations (depends 4,6,7,8 schema)
                                               ├─▶ STEP 10 Worker (depends 4,5,8)
                                               ├─▶ STEP 11 API (depends 4,5,10)
                                               ├─▶ STEP 12 Integration Test (depends 11)
                                               ├─▶ STEP 13 Full Test Suite
                                               ├─▶ STEP 14 Documentation
                                               └─▶ STEP 15 DoD Audit
```

Parallelizable groups (dispatch subagents):
- Group A (after Step 3): Step 5 Budget, Step 6 Source Registry, Step 7 Entity Repo, Step 8 Document Ingestion — independent code paths if schema agreed upfront
- Group B (after Step 9): Step 10 Worker + Step 11 API skeletons

---

## STEP 3 — Configuration + Model Routing

**Goal:** Typed layered config via pydantic-settings + YAML domain configs, validation at startup, no secrets in YAML, role-based ModelRouter configurable.

**Files to create/modify:**
- Modify `src/core/config.py` → layered Settings
- Create `src/config/{loader,models,router}.py` or keep in `src/core/` + `src/llm/router.py`
- Create `configs/models.yaml`, `configs/budgets.yaml`, `configs/scoring/thresholds.yaml`, `configs/sources/*.yaml` placeholders, `configs/regions/*.json`, `configs/languages/*.json`
- Create `src/embeddings/provider.py` (EmbeddingProvider interface with dimension/embed/embed_batch, pgvector only, default 1536 via config)
- Modify `src/llm/provider.py` to implement V1 contract + delegate to router

**Tasks:**
1. Extend `Settings`:
   ```python
   class EmbeddingSettings: model=str, dimension=int=1536, provider=str="openai"
   class BudgetSettings: quick_soft=1.0, quick_hard=1.2, standard_soft=2.0, standard_hard=2.4, deep_soft=5.0, deep_hard=6.0
   class LLMSettings: provider=str="litellm", api_key env, models map
   class ResearchSettings: max_iterations etc from budgets.yaml
   # env vars for secrets/runtime infra; YAML for domain configs
   ```
2. Create `configs/models.yaml`:
   ```yaml
   roles:
     planner: "nemotron-3.5-lightning"  # Nemotron 3.5 Lightning per spec
     discovery: "nemotron-3.5-lightning"
     classification: "nemotron-3.5-lightning" # configurable
     entity_resolution: "nemotron-3.5-lightning"
     deep_research: "nemotron-3.5-ultra"
     verification: "nemotron-3.5-ultra"
     synthesis: "nemotron-3.5-ultra"
   fallback:
     planner: "gpt-4o-mini"
   provider: "litellm"
   ```
   No hard-coded names in business logic → router reads this.

3. Create `configs/budgets.yaml` mirroring RESEARCH_STATE_MACHINE §4.1:
   ```yaml
   depth_budgets:
     quick: {soft_usd: 1.0, hard_usd: 1.2, max_shards: 6, max_iterations: 1, max_claims: 50}
     standard: {soft_usd: 2.0, hard_usd: 2.4, max_shards: 12, max_iterations: 2, max_claims: 150}
     deep: {soft_usd: 5.0, hard_usd: 6.0, max_shards: 16, max_iterations: 3, max_claims: 400}
   ```

4. Create `src/llm/router.py` ModelRouter:
   - `__init__(config_path="configs/models.yaml", settings: Settings)`
   - `model_for_role(role: LLMRoleV1) -> str` (new 7-role enum)
   - `provider_for_role(role) -> str`
   - `estimate_cost(prompt_tokens, completion_tokens, role) -> float` via litellm pricing or fallback table
   - `fallback_model(role) -> str`
   - Expose metadata, tracking

5. Extend `LLMProvider` to V1 contract:
   ```python
   async def generate(prompt, system, role, temperature, max_tokens) -> str
   async def structured_generate(prompt, system, role, schema: type[BaseModel]) -> BaseModel
   async def stream(prompt, system, role) -> AsyncIterator[str]
   def estimate_cost(prompt_tokens, completion_tokens, role) -> float
   def model_for_role(role) -> str  # delegate to router
   async def health_check() -> bool
   # keep complete/json as aliases for backward compat
   ```

6. Create `src/embeddings/provider.py` EmbeddingProvider:
   - `dimension: int` (from config, default 1536)
   - `async def embed(text: str) -> list[float]`
   - `async def embed_batch(texts: list[str]) -> list[list[float]]`
   - Uses litellm.embedding(api_key, model) or stub; pgvector only

7. YAML loader `src/core/yaml_loader.py`: `load_yaml(path) -> dict`, validate with pydantic, raise ConfigError with diagnostic

8. Startup validation: `validate_config()` called in `src/main.py lifespan` or `create_app()`, fails fast if YAML invalid or dimension != VECTOR dims

9. Tests: `tests/unit/test_config_validation.py`, `test_model_router.py`, `test_embedding_provider.py` with mocks

**Verification:** `pytest tests/unit/test_config_validation.py tests/unit/test_model_router.py -v`; `python -c "from src.core.config import settings; validate"` ; `alembic check` still pass; no secrets in YAML (grep).

---

## STEP 4 — ResearchSpec + Research Job Persistence

**Goal:** Typed, serializable, persistable, versioned, idempotent ResearchSpec + job/run/query tables.

**Files:**
- Create `src/research/spec.py` (ResearchSpec)
- Create `src/research/schemas.py` (Pydantic for API)
- Modify `src/research/models.py` (extend ResearchJob, add ResearchRun, ResearchQuery)
- Create `src/research/repository.py` extensions or `src/research/job_repository.py`
- Create `src/research/service.py` (business logic, not in routes)

**ResearchSpec fields** (per prompt):
```
objective, entity_type, geography, regions, countries, languages, industries,
inclusion_criteria, exclusion_criteria, research_dimensions, source_classes,
depth, budget, max_iterations/max_candidates/max_documents/max_cost, created_at
+ version: str = "1.0"
+ spec_hash: str (sha256 deterministic)
```

**Implementation:**
1. `ResearchSpec` as `BaseModel` with:
   - `version: str = "1.0"`
   - `spec_hash() -> str` = sha256(sorted JSON of all fields except created_at)
   - `to_json()`, `from_json()`, `validate()`
   - Downstream workers cannot mutate original intent without explicit transitions → spec stored immutable in `research_jobs.planner_plan` or new `spec_json` column

2. `ResearchJob` extensions (via migration 002 nullable first):
   - Add `regions JSONB`, `depth_config JSONB`, `planner_plan JSONB`, `config_hash VARCHAR(64)`, `model_versions JSONB`, `budget_soft_usd NUMERIC`, `budget_hard_usd NUMERIC`, `cost_usd`, `cost_tokens`, `fetch_count`, `partial_reason VARCHAR(100)`, `report_json JSONB`
   - Keep existing columns; add new as nullable server_default

3. New `ResearchRun` model:
   ```python
   class ResearchRun(Base): id UUID PK, job_id FK, run_number int, status str, budget_soft/hard, cost_usd, prompt_tokens, completion_tokens, fetch_count, stopping_reason, coverage_snapshot JSONB, iteration_count, started_at/completed_at, error, metadata JSONB, created_at; unique(job_id, run_number)
   ```

4. New `ResearchQuery` model:
   ```python
   class ResearchQuery(Base): id UUID PK, job_id FK, run_id FK nullable, raw_query Text, expanded_query Text, region str, language str, purpose str(check discovery/verification/context/gap_fill/recursive), rank int, metadata JSONB, created_at
   ```

5. Deterministic hashes:
   - Job spec hash: `sha256(normalized_query + depth + regions + languages + source_strategy)`
   - Query hash: `sha256(run_id + expanded_query + region + language + purpose)`
   - Idempotency key for API: check existing `research_jobs` where spec_hash match within window → return existing job_id

6. Repository: `ResearchJobRepository.create(spec: ResearchSpec) -> ResearchJob`, `get(job_id)`, `list`, `update_status(job_id, status via lifecycle)`, `ResearchRunRepository.create(job_id)`, `ResearchQueryRepository.bulk_create(...)`

7. Tests: `tests/unit/test_research_spec.py` (serialization, versioned, hash deterministic), `test_job_persistence.py` (CRUD with aiosqlite or real PG via docker if available)

**Verification:** Create spec → persist → reload → assert hash stable; test idempotency (same prompt twice returns same job if within dedup window or creates new with different hash).

---

## STEP 5 — Budget Accounting

**Goal:** BudgetManager with reserve/record_usage/remaining/can_continue/exceeded, track LLM calls/tokens/cost, search calls, docs, iterations, soft/hard limits, checks before expensive work.

**Files:**
- Create `src/budget/manager.py`
- Create `src/budget/models.py` (CostRecord, BudgetSnapshot)
- Modify `src/research/models.py` to link cost tracking (already added columns)
- Update `src/core/config.py` to load budgets.yaml

**Interface:**
```python
@dataclass BudgetSnapshot(soft_usd, hard_usd, spent_usd, spent_tokens, fetch_count, soft_hit, hard_hit)
@dataclass CostRecord(prompt_tokens, completion_tokens, cost_usd, fetch_count, docs_count, iteration)

class BudgetManager:
  def __init__(settings, db_session_factory)
  async def initialize(job_id, run_id, depth) -> BudgetSnapshot
  async def reserve(run_id, estimated_cost: float) -> bool
  async def record_llm(run_id, prompt_tokens, completion_tokens, cost_usd, role, model)
  async def record_fetch(run_id, count=1)
  async def record_documents(run_id, count)
  async def remaining(run_id) -> BudgetSnapshot
  def can_continue(snapshot)->bool # soft check
  def exceeded(snapshot)->str|None # returns hard/soft or None
  def can_llm(est_cost, snapshot)->bool
  def can_fetch(snapshot)->bool
```

**Enforcement:**
- Soft → no new recursive passes, still finish in-flight; hard → abort and mark PARTIAL
- Every LLM/fetch checks before call via `can_llm`/`can_fetch`
- Recursive research cannot bypass: gap loop checks `remaining()` each iteration

**Config:** Loads `configs/budgets.yaml` depth_budgets; change without code

**Tests:** `tests/unit/test_budget_manager.py` with Fake DB (in-memory dict or aiosqlite), test soft/hard enforcement, reserve/record/remaining, can_continue, exceeded, cost tracking

---

## STEP 6 — Source Registry

**Goal:** source_id/name/domain/country/region/language/source_type/authority_level/purpose DISCOVERY/VERIFICATION/CONTEXT/access_method/enabled, seeded small useful V1 set, not hard-coded rankings, YAML+DB cache.

**Files:**
- Create `src/sources/{models,registry,repository,connector}.py`
- Create `configs/sources/*.yaml` (5-6 seeded)
- Modify `src/connectors/base.py` to align with new SourceDef

**SourceDef schema** (pydantic, validated at startup):
```python
class SourceDef(BaseModel):
  id: str (pattern ^[a-z0-9_]+$)
  display_name: str
  tier: int 1-5
  authority_score: float 0-1
  coverage: Coverage(region/language/industry/entity_type)
  source_type: Literal["web_search","news","social","specialized"]
  access_method: Literal["api","rss","scrape","playwright","snapshot"]
  purpose: list[Literal["DISCOVERY","VERIFICATION","CONTEXT"]]  # PURPOSE enum
  domain: str|None
  country: str|None
  region: str|None
  language: str|None
  authority_level: str|None
  enabled: bool
  rate_limit_per_min: int|None
  timeout_ms: int = 30000
  max_results: int = 20
  requires_key: bool
  env_key: str|None
  search_url: str|None
  is_active: bool
```

**Seeded V1 set (small useful, not hard-coded rankings):**
- `tavily` (tier2, web_search, api, DISCOVERY/CONTEXT, global)
- `brave_search` (tier2, web_search, api, DISCOVERY)
- `sec_edgar` (tier1, specialized, api, VERIFICATION)
- `gnews` or `news_api` (tier2, news, rss/api, DISCOVERY/VERIFICATION)
- `reddit_public` (tier4, social, api, DISCOVERY/CONTEXT)
- Include `domain`, `country`, `region`, `language`, `source_type`, `authority_level`, `purpose` fields per spec

**Implementation:**
1. YAML files under `configs/sources/` one per source
2. `SourceRegistry` loads YAMLs, validates via Pydantic, upserts to `sources` table on startup
3. `SourceRepository` CRUD + `active()`, `by_tier()`, `by_region()`, `by_purpose()`
4. `SourceConnector` Protocol already exists → ensure compatibility; new sources implement same iface
5. No hard-coded rankings: ranking derived from `tier` + `authority_score` at query time, configurable via YAML only
6. Validator `scripts/validate_sources.py` (or inline) rejects private social blocklist, playwright without robots_respected etc (but minimal for Phase 1)

**Tests:** `tests/unit/test_source_registry.py` (loader validation, seeded set loads, tier not hard-coded, disabled source filtered)

---

## STEP 7 — Entity Repository

**Goal:** entities/entity_aliases/companies/people CRUD + find/search by alias/canonical, no sophisticated probabilistic resolution yet.

**Files:**
- Create `src/entities/{models,repository}.py`
- Modify `alembic/env.py` to import new models

**Schema** (DATA_MODEL §2.4 but scoped for Phase 1):
```sql
entities(id UUID PK, job_id FK, run_id FK, entity_type str, canonical_name Text, normalized_name Text, description Text, domain Text, metadata JSONB, confidence float, created_at)
UNIQUE(job_id, entity_type, normalized_name)
indexes: job_id, type, canonical_trgm, normalized

entity_aliases(id UUID PK, entity_id FK, alias Text, alias_normalized Text, source str, confidence float, metadata JSONB, created_at)
UNIQUE(entity_id, alias_normalized)
indexes: entity_id, alias_trgm
```

**Repository:**
```python
class EntityRepository:
  async def create(entity: Entity) -> Entity
  async def get(entity_id) -> Entity|None
  async def find_by_canonical(job_id, canonical_name) -> Entity|None
  async def find_by_alias(job_id, alias) -> Entity|None  # trigram search
  async def search(job_id, query: str) -> list[Entity]  # alias + canonical LIKE
  async def list_for_job(job_id) -> list[Entity]
  async def add_alias(entity_id, alias, source, confidence)

# Companies/People projections mirror entities but lean in Phase 1:
# Provide CompanyRepository, PeopleRepository if schema includes companies/people tables
# If DATA_MODEL domain tables (companies/people/funding_rounds) are too heavy for Phase 1, stub them as entities with type=company/person + metadata, and create tables via migration 002 but minimal columns
```

**Note:** No sophisticated probabilistic resolution yet → only exact normalized_name + alias_normalized trigram; deterministic.

**Tests:** `tests/unit/test_entity_repository.py` (CRUD, alias search, canonical search, duplicate handling)

---

## STEP 8 — Document Ingestion Infrastructure

**Goal:** Pipeline RAW→FETCH→NORMALIZE→HASH→DEDUP→STORE→METADATA, retain source/URL/title/author/pub date/retrieval time/language/content/hash/metadata, deterministic dedup.

**Files:**
- Modify `src/documents/normalizer.py` (retain full metadata)
- Modify `src/documents/dedup.py` (deterministic)
- Create `src/documents/ingestion.py` (pipeline orchestrator) or `src/documents/service.py`
- Create `src/documents/metadata.py` if needed

**Pipeline steps:**
1. RAW: `RawResult` from connector (url, title, snippet, content, published_at, author, source_name, metadata)
2. FETCH: already fetched by connector; ingestion validates `max_document_size_bytes`, `max_content_length`
3. NORMALIZE: `DocumentNormalizer.normalize(raw, job_id, source_id) -> Document`
   - Retain source/URL/title/author/pub_date/retrieval time/language/content/hash/metadata
   - Canonicalize URL (lower, strip fragment, sort query params deterministically where possible)
   - Language detection stub (default en unless raw.language)
   - Content hash via sha256
4. HASH: deterministic dedup hashes:
   - `url_hash = sha256(normalized_url)`
   - `content_hash = sha256(content)`
   - `canonical_url_hash` if applicable
5. DEDUP: deterministic ordering:
   - Sort docs by url stabily before dedup
   - `dedup_by_exact_url` → `dedup_by_canonical_url` → `dedup_by_content_hash` in sequence, each stable, last write wins but first encountered kept
   - Set `is_duplicate_of` + `dedup_reason` enum
   - No vector near-duplicate in Phase 1 (deferred)
6. STORE: bulk upsert with `uq_documents_job_url` + idempotency via `on_conflict_do_nothing` or `on_conflict_do_update` preserving first
7. METADATA: store in `metadata` JSONB with retrieval trace (timing, http_status, source tier)

**Deterministic:** Same input docs in any order produce same dedup result when sorted first.

**Tests:** `tests/unit/test_document_ingestion.py` (pipeline end-to-end with Fake connector, hash stability, dedup deterministic, metadata retained, duplicate pointer)

---

## STEP 9 — Database Migrations

**Goal:** Alembic append-only, compare existing schema vs DATA_MODEL.md, avoid duplicates, preserve backward compat, verify upgrade from clean+existing, downgrade where practical.

**Files:**
- Create `alembic/versions/002_v1_phase1_foundation.py`

**Contents (minimal Phase 1 vertical slice):**
```python
# Add columns to research_jobs (nullable with defaults where needed):
# - regions JSONB, depth_config JSONB, planner_plan JSONB, config_hash VARCHAR(64), model_versions JSONB
# - budget_soft_usd, budget_hard_usd NUMERIC(10,4), cost_usd, cost_tokens, fetch_count, partial_reason, report_json

# Add run_id, region, fetch_duration_ms, http_status to documents (nullable)

# Add run_id to claims, contradictions, retrieval_runs, verification_runs

# New tables:
# - research_runs
# - research_queries
# - sources
# - entities, entity_aliases
# - companies, people (minimal, or as projections; if defer funding_rounds/investors/markets to later, still create entities tables)
# - scores/reports optional but Phase 1 needs scores table for budget? Include minimal scores

# Use pgvector still VECTOR(1536) where needed

# Indexes as per DATA_MODEL

# Downgrade drops new tables/columns
```

**Avoid duplicates:** Check existing table names before create; use `op.create_table` only if not exists pattern or rely on alembic lineage (001 is only prior, so safe).

**Backward compat:** All new columns nullable or server_default; backfill existing rows: set `documents.region='us'`, `run_id` to first run of job (but Phase 1 no existing runs, so just nullable).

**Verification:**
- `alembic upgrade head` from clean DB (delete PG data or use aiosqlite for test)
- `alembic upgrade head` from existing 001 state (should migrate)
- `alembic downgrade -1` + `upgrade head` idempotent
- `alembic check` (if available)

**Update `alembic/env.py`** to import new models for autogenerate: `ResearchRun`, `ResearchQuery`, `Source`, `Entity`, `EntityAlias`, etc.

---

## STEP 10 — Redis/arq Worker Foundation

**Goal:** arq+Redis only, enqueue/execute/retry/failure/idempotency via sha256(job+phase+hash), structured logging, no full orchestration yet.

**Files:**
- Create `src/worker/{queue,settings,tasks,logging}.py`
- Create `src/core/logging.py` (structlog config)

**Queue design:**
```python
# src/worker/settings.py
class WorkerSettings(BaseSettings):
  redis_url: str
  queue_name: str = "research"
  max_jobs: int = 8
  job_timeout: int = 360

# src/worker/queue.py
async def enqueue_research_job(redis, job_id: UUID, prompt: str, depth: str) -> str

# src/worker/tasks.py
async def process_research_job(ctx, job_id: str, run_id: str) -> dict
  # Load job from DB
  # Initialize budget
  # Update status via lifecycle (PENDING→PLANNING→DISCOVERING... but Phase 1 minimal: just PLANNING→DISCOVERING→COMPLETED loop)
  # Structured logging: logger.info("phase", job_id=..., run_id=..., phase=..., timing=..., cost=...)
  # Idempotency: key = sha256(job_id + phase + hash(input))
  # Check existing research_runs with same key before work; if found return cached
  # Retry via arq retry logic (exponential backoff + jitter, max 3)
  # Failure: set job.last_error, status=failed, log error without secrets
```

**Observability:**
- structlog JSON with fields: job_id/run_id/task_id/phase/role/model/source/timing/token/cost/status/error
- No secrets logged (api_key redacted)
- Prometheus counters stubbed (increment in-memory for tests)

**Idempotency:**
- `idempotency_key = hashlib.sha256(f"{job_id}:{phase}:{hash}".encode()).hexdigest()`
- Store in `research_runs.metadata.idempotency_key` or separate `task_idempotency` table? For Phase 1, check `research_runs` or `documents` uniqueness before insert (uq_documents_job_url gives idempotency for docs)
- arq retry safe: same key returns same output without duplicate DB writes (use upsert)

**No full orchestration yet:** Worker foundation just runs minimal job lifecycle; discovery fetching mocked in tests, not real connectors.

**Tests:** `tests/unit/test_worker_idempotency.py` (enqueue same job twice → same result, retry logic, structured logging capture)

---

## STEP 11 — FastAPI Research Job Endpoint

**Goal:** POST /research/jobs → accept prompt → create ResearchJob → persist → enqueue → return job ID; GET /research/jobs/{id}; GET /health; optional cancel; business logic not in routes; dependency injection.

**Files:**
- Modify `src/api/v1/jobs.py` (real implementation)
- Create `src/research/service.py` (ResearchService)
- Modify `src/api/deps.py` (add get_db_session, get_queue, get_budget etc)
- Modify `src/main.py` (lifespan, config validation, router inclusion)

**Endpoints:**
```python
POST /api/v1/research/jobs  # or POST /research/jobs per spec — provide both aliases
  Request: {prompt: str, depth: str="standard", regions: list[str]|None, languages: list[str]|None, budget: float|None}
  Response: {job_id: UUID, status: str, created_at: datetime}
  Logic: ResearchService.create_job(prompt, depth, ...) → persist ResearchJob+ResearchRun+ResearchQueries stub → enqueue arq → return 201

GET /api/v1/research/jobs/{job_id}
  Response: {job_id, status, query, created_at, started_at, completed_at, budget_soft/hard, cost_usd, error}
  Logic: ResearchJobRepository.get(job_id)

GET /api/v1/research/jobs  # list, optional pagination
GET /api/v1/health         # DB SELECT 1, Redis ping, LLM health_check (stub)
POST /api/v1/research/jobs/{job_id}/cancel (optional)
```

**DI & Separation:**
- `src/research/service.py` contains `create_job`, `get_job`, `cancel_job` business logic
- Routes only parse request/response and inject dependencies (`db: AsyncSession`, `queue: ArqRedis`, `budget_manager: BudgetManager`)
- No giant classes, no circular deps, no business logic in routes

**Validation:**
- Pydantic request models with `prompt: str = Field(min_length=1, max_length=5000)`
- Depth enum validation (quick/standard/deep)
- Config validation at startup (already)

**Tests:** `tests/unit/test_api_job_creation.py` (TestClient with mocked DB + queue, job persisted, enqueue called, GET returns same, health 200, error handling 422 etc)

---

## STEP 12 — Integration Test

**Goal:** POST /jobs → spec persisted → job persisted → worker loads job → budget initialized → state updated → clean exit

**File:** `tests/integration/test_phase1_vertical_slice.py` (or `tests/integration/test_research_job_flow.py`)

**Steps:**
1. Use `AsyncClient` or `TestClient` against `create_app()` with overridden `get_db_session` using aiosqlite or test PG fixture
2. `POST /api/v1/research/jobs` with `{"prompt": "Acme AI Berlin 2023 seed startup", "depth": "standard"}`
3. Assert 201 + `job_id` returned
4. Query DB directly: assert `research_jobs` row exists with `query==prompt`, `status==pending`, `planner_plan` or `spec` json stored, `budget_soft_usd` set from budgets.yaml
5. Simulate worker: call `process_research_job(ctx, job_id, run_id)` directly with mocked Redis (FakeRedis) and DB session
6. Assert worker loads job, initializes budget via BudgetManager, updates `research_runs` status, no duplicate on retry (idempotency)
7. Assert final state `completed` or `partial` with `cost_usd` recorded, logs contain job_id/run_id
8. Clean exit: DB session closed, no orphan tasks

**Mocks/fakes:** No live LLM/search; use `StubLLMProvider`, `StubConnector`, `FakeBudget`, `FakeRedis`

**Verification:** Run `pytest tests/integration/test_phase1_vertical_slice.py -v` green.

---

## STEP 13 — Full Test Suite

**Goal:** Ensure 124 baseline still pass, add coverage for 12 categories A-L, mocks only.

**12 categories** (per prompt):
- A config validation
- B model routing
- C ResearchSpec serialization
- D budget
- E source registry
- F entity repo
- G doc ingestion
- H dedup
- I migrations
- J worker idempotency
- K API job creation
- L error handling

**Files already planned:** Each step includes its unit test file; this step aggregates and ensures all pass plus existing 124.

**Run:**
- `pytest -q` → expect 124 + new tests (target 140+). All green.
- `alembic upgrade head && pytest` CI gate simulation
- `ruff`/`mypy` if available (optional, but run if installed)

**No live dependencies:** All new tests use mocks/fakes, aiosqlite for DB, fakeredis for Redis, StubProvider for LLM

---

## STEP 14 — Documentation

**Goal:** `docs/PHASE1_IMPLEMENTATION.md` with implemented/reused/migrations/config/model routing/API/worker/testing/limitations/deferred; document any ADR changes explicitly.

**File:** `docs/PHASE1_IMPLEMENTATION.md` and `evidence-engine/docs/PHASE1_IMPLEMENTATION.md` (copy)

**Sections:**
- ## Implemented (list with files)
- ## Reused (table from audit, marked preserved)
- ## New Files (paths)
- ## Modified Files (paths + rationale)
- ## Database (migrations/tables/status — alembic history, 001+002, tables created)
- ## Model Routing (role→model table, config file, fallback, estimate_cost)
- ## Budget (config YAML, soft/hard enforcement details)
- ## Worker (queue name, retry 3 backoff, idempotency sha256, structured logging fields)
- ## API (endpoints list + sample curl)
- ## Tests (baseline 124/new/total/failures)
- ## Architecture Changes (NONE or list with ADR)
- ## Known Limitations (what Phase 1 does NOT do)
- ## Phase 2 Readiness (READY/NOT READY checklist)

Document any architecture deviations explicitly with ADR format.

---

## STEP 15 — Final Phase 1 Audit vs Definition of Done (17 checkboxes)

**Checklist** (must all be checked):
- [ ] Repository audit completed (PHASE1_IMPLEMENTATION_AUDIT.md exists)
- [ ] Configuration implemented (Settings layered, YAML configs, validation at startup, no secrets in YAML)
- [ ] Model router implemented (role→model, provider, metadata, estimate_cost, fallback, configurable)
- [ ] ResearchSpec implemented (typed/serializable/persistable/versioned, deterministic hashes)
- [ ] Research job persistence implemented (research_jobs/research_runs/research_queries, idempotent hashes)
- [ ] Budget manager implemented (reserve/record_usage/remaining/can_continue/exceeded, tracking)
- [ ] Source registry implemented (source_id/name/domain/country/region/language/source_type/authority_level/purpose/access_method/enabled, seeded V1 set)
- [ ] Entity repository implemented (entities/entity_aliases/companies/people CRUD + alias search)
- [ ] Document ingestion validated (pipeline RAW→...→METADATA, deterministic dedup)
- [ ] Alembic migrations created (append-only, 002 covers new tables/cols, upgrade clean+existing, downgrade practical)
- [ ] Redis/arq worker foundation implemented (enqueue/execute/retry/failure/idempotency, structured logging)
- [ ] Structured observability implemented (logs with job_id/run_id/task_id/phase/role/model/source/timing/token/cost/status/error, no secrets)
- [ ] Minimal research API implemented (POST /research/jobs, GET /research/jobs/{id}, GET /health, optional cancel, DI)
- [ ] Integration path works (POST → spec persisted → job persisted → worker loads → budget init → state updated → clean exit)
- [ ] Existing 124 tests still pass + new tests pass
- [ ] Documentation updated (PHASE1_IMPLEMENTATION.md)
- [ ] No Phase 2+ scope implemented (no full engine, no Kafka/Neo4j/K8s/crawler/bypass/private social)

**Final Report Format** (must produce):
```
# PHASE 1 IMPLEMENTATION REPORT
## Status COMPLETE/PARTIAL/BLOCKED
## Implemented
## Reused
## New Files
## Modified Files
## Database (migrations/tables/status)
## Model Routing (role→model)
## Budget (config/enforcement)
## Worker (queue/retry/idempotency)
## API (endpoints)
## Tests (baseline/new/total/failures)
## Architecture Changes (NONE or list)
## Known Limitations
## Phase 2 Readiness READY/NOT READY
```

Emit to `docs/PHASE1_REPORT.md` and stdout.

---

## Risk Mitigations & Quality Gates

- After each step: `pytest -q` (ensure 124 still pass), `alembic upgrade head` dry-run, `ruff check` if available
- No secrets in YAML: grep for `api_key|secret|password` in configs/
- No hard-coded model names in business logic: grep `gpt-4o|nemotron` outside router/config
- No hard-coded 0.92 thresholds beyond scoring config: grep `0.92` outside `configs/scoring/`
- Idempotency: every worker task tested with double enqueue
- DI: routes contain no direct DB queries or budget logic

---

## Effort Estimate

- Steps 3-8: 60% of effort (config+router 10%, spec+job 15%, budget 10%, sources 10%, entities 8%, ingestion 7%)
- Steps 9-11: 25% (migrations 8%, worker 10%, API 7%)
- Steps 12-15: 15% (integration 5%, tests 5%, docs/audit 5%)

**Execution:** Steps 3-4 sequential, then Group A parallel, then Step 9, then Group B parallel, then 12-15 sequential. Use TodoWrite to track one in_progress at a time where dependencies exist, subagents for parallel independent sub-tasks.

