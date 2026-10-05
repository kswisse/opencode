# PHASE 2 IMPLEMENTATION AUDIT — Discovery MVP

**Date:** 2026-08-27  
**Phase:** 2 — Discovery MVP (Prompt → ResearchSpec → QueryPlan → Search → Fetch → Candidate Extraction → Dedup → Provenance)  
**Baseline:** commit 595db5a (161/161 tests), Alembic 001→002, integration slice green  
**Auditor:** AgentsOrchestrator (Phase 2)  
**Principles:** CORRECTNESS → EVIDENCE → COVERAGE → COST → PERFORMANCE → UX | DISCOVER BROADLY → VERIFY AGGRESSIVELY

---

## 1. Frozen Docs Read

- `docs/ARCHITECTURE.md` — logical arch, module boundaries, LLM/Source abstractions, worker/queue
- `docs/DATA_MODEL.md` — DDL 001–005, research_runs/research_queries, entities, evidence, scores
- `docs/AGENT_CONTRACTS.md` — 6 agent roles, I/O, DAG, retry/idempotency, budget
- `docs/SOURCE_MODEL.md` — tiers 1–5, authority, coverage, discovery/verification/context
- `docs/EVIDENCE_MODEL.md` — CLAIM→EVIDENCE→SOURCE→DOCUMENT, 5 verification states
- `docs/RESEARCH_STATE_MACHINE.md` — 13 states + terminals, gap/budget stopping criteria
- `docs/EVALUATION.md` — categories A–H, 11 metrics, 3 baselines
- `docs/PHASE1_IMPLEMENTATION_AUDIT.md` — 002 audit, infra baseline
- `docs/PHASE1_IMPLEMENTATION.md` — foundation deliverables
- `docs/PHASED_PLAN.md` — phases 0–9, DoD per phase, vertical slice
- `docs/FUTURE.md` + `docs/REPO_INSPECTION.md` — scope gates, reuse verdict

No contradictions found; Phase 2 is discovery-only (no deep research/scoring/report synthesis).

---

## 2. Implementation Inspection

### 2.1 Existing DB — Alembic

| Revision | Tables | Verdict |
|----------|--------|---------|
| `001 initial_tables` | `research_jobs`, `documents` (with `content_hash`, `embedding`, `uq_documents_job_url`), `claims`, `graph_nodes/edges`, `source_lineages`, `contradictions`, `retrieval_runs`, `verification_runs` | KEEP — solid base, pgvector 1536 frozen |
| `002 add_phase1_tables` | `research_specs` (id, objective, geography/regions/countries/languages, budget JSON), `entities`, `entity_aliases`, `entity_relationships`, `source_registry`, `research_queries` (job_id, spec_id, query_text, query_type, region, language, parent_query_id, iteration), `dimension_coverage`, plus `research_jobs.spec_id` + `budget_used` | KEEP — Phase 1 tables present; no duplication. Note: `research_queries` lacks `source_id/priority/dimension` fields needed for Phase 2; will EXTEND via 003 rather than recreate |

`research_jobs` current columns match freeze subset (spec_id, budget_used, languages, depth, status). No `research_runs` table yet (deferred to Phase 5) — OK for discovery scope, job-centric.

### 2.2 Existing Components — Detailed

| Component | File | Current Behavior | Classification | Reason |
|-----------|------|------------------|----------------|--------|
| **ResearchSpec** | `src/planner/models.py` | Pydantic, fields: objective, entity_type, geography, regions, countries, languages, industries, inclusion/exclusion, research_dimensions, source_classes, depth, budget, max_iterations/candidates/documents/cost, `spec_hash()` deterministic (sorted lower/strip), `to_json/from_json` | KEEP | Correct idempotent spec. No change needed; will be consumed by QueryPlanner. |
| **Planner (LLM-backed)** | `src/planner/planner.py` | Calls `LLMProvider.json` with fixed system prompt → `ResearchSpec(**response)` | KEEP | Reused for Phase 2 query planning fallback; new QueryPlanner will delegate to it optionally but not replace |
| **ResearchService** | `src/research/service.py` | `create_job(prompt, depth, languages, regions, budget_usd)` → builds ResearchSpec from BudgetConfig/BUDGET_PRESETS, persists `research_specs` + `ResearchJob` (query, normalized_query, languages, spec_id, budget_used {config, usage, spec_hash}), flush, logger job_created; `get_job/list_jobs` | KEEP | Idempotent via spec_hash (advisory), correct DI separation from routes. Will be reused by discovery orchestrator to load spec/job. |
| **ModelRouter** | `src/llm/router.py` | Loads `configs/models.yaml` roles/planner/discovery/classification/entity_resolution/deep_research/verification/synthesis → Nemotron defaults, fallback map, `model_for_role`, `estimate_cost` via _FALLBACK_PRICING | KEEP | 7 roles correctly configured. Phase 2 query expansion + candidate extraction will route via DISCOVERY/PLANNER — no refactor |
| **LLMProvider** | `src/llm/provider.py` | `generate(structured_generate via json+schema validation/stream via litellm/estimate_cost/model_for_role/health_check` + `complete/json` legacy compat, StubProvider/RecordingProvider | KEEP | V1 contract satisfied (4 methods). Query expansion + CandidateExtractor will use `structured_generate` + schema validation; no change |
| **BudgetManager** | `src/budget/manager.py` | BudgetUsage (queries, documents, candidates, cost_usd, prompt/completion tokens, fetch_count, search_calls, llm_calls) + soft/hard usd, reserve/record_usage/record_llm/record_fetch/snapshot/can_continue/remaining/exceeded, BUDGET_PRESETS via budgets.yaml depth_budgets | KEEP | Reuse directly for discovery: track search calls, fetches, LLM extractions, enforce reserve before expensive ops, PARTIAL on hard_hit |
| **SourceRegistry** | `src/sources/registry.py` + `models.py` | SourceEntry (source_id, name, country/region/language, source_type, authority_level 1-5, enabled, purpose, config), `from_yaml`/`from_directory` loads `configs/sources/*.yaml`, _map_single handles new tier/coverage format, filters by_tier/country/region/type/purpose, prioritize_for_country | EXTEND (minor) | Keep registry; extend SourceEntry with `tier/authority_score/access_method/timeout_ms/max_results/rate_limit` pass-through for connector creation (currently discards some YAML fields into `config`). No duplicate abstraction. |
| **Source YAMLs** | `configs/sources/{brave_search,gnews,reddit_public,sec_edgar,tavily}.yaml` + `defaults.yaml` | 5 seed sources with tier, authority_score, coverage regions/languages, access_method, purpose arrays, env_key, rate_limit/timeout | KEEP | Broad sources prioritized; will be consumed by SearchConnector factory. No hard-coded countries in Python — configs drive planner |
| **Region/Language Configs** | `configs/regions/{eu,us,vn}.json`, `configs/languages/{en,vi}.json` | EU/US/VN with code/name/languages/search_domains/preferred_sources/timezone; languages with transliteration | KEEP | Phase 2 query planning will load dynamically via directory scan — supports hundreds without code change |
| **DocumentIngestion** | `src/documents/ingestion.py` | `normalize(raw, job_id, source_id)` → DocumentNormalizer → hash+metadata enrichment, `dedup_and_store` (exact_url→canonical→content_hash deterministic sorted by url, is_duplicate_of pointer), `ingest(raws, job_id, source_id)` batch, `doc_hash` sha256(url|content_hash) | KEEP | Reuse exactly — Phase 2 must NOT create second document system. Fetch → normalize via DocumentIngestion |
| **DocumentNormalizer** | `src/documents/normalizer.py` | `normalize(RawResult→Document)` with job_id/source_id/url/title/author/published_at/retrieved_at/content (raw.content or snippet), metadata | KEEP | Correct minimal normalizer; discovery fetcher will enrich via same path |
| **Deduplicator** | `src/documents/dedup.py` | dedup_by_exact_url / canonical_url / content_hash | KEEP | Will be reused for result dedup (canonical URL) — separate concern from candidate dedup |
| **Document model/repo** | `src/documents/models.py/repository.py` | UUID, job_id FK, source_id, url/canonical_url/title/author/publisher/published_at/retrieved_at/language/content/content_hash/mime_type/is_duplicate_of/dedup_reason/metadata/embedding VECTOR(1536) | KEEP | Persist via existing repo; Phase 2 adds search_results/candidate tables alongside, not duplicating |
| **EntityRepository** | `src/entities/repository.py` | Pydantic Entity/EntityAlias/EntityRelationship models, CRUD + find_by_name/alias, find_or_create | KEEP (shape) | Note: currently Pydantic in-memory shape, not SQLAlchemy. Will EXTEND (not duplicate) to add normalization hook for CandidateNormalizer (legal suffix stripping, alias lookup). Keep existing for tests. |
| **Research models** | `src/research/models.py` | ResearchJob with spec_id/budget_used, lifecycle columns | KEEP | Discovery orchestrator updates status via lifecycle; no schema rewrite |
| **Worker (arq)** | `src/worker/tasks.py`, `queue.py`, `settings.py` | `run_research_job(ctx, job_id, run_id, phase)` with _idempotency_key sha256(job:phase:payload_hash[:12]), budget init, status planning→discovering→completed, structured logging with job_id/run_id/task_id/phase/role/model/source/timing/cost, idempotency skip if not pending/planning | EXTEND | Keep idempotency/budget/logging scaffolding; extend to call DiscoveryOrchestrator instead of stub transitions, add discovery-specific phases, bounded concurrency, budget checks per operation |
| **ResearchOrchestrator (legacy)** | `src/research/orchestrator.py` | Two-pass sequential for-connector search → normalize → dedup → extract claims → verify → red_team → partial logic | REFACTOR reference | Do not duplicate; new DiscoveryOrchestrator will be separate discovery-only orchestrator (no verify/score). Legacy orchestrator stays for Phase 1 tests but not used in Phase 2 flow |
| **Connector Protocol** | `src/connectors/base.py` | Protocol SourceConnector (search/query Fetch/health, name), dataclass SearchQuery (query, time_range, languages, max_results, result_type), RawResult (url/title/snippet/content/published_at/author/source_name/metadata), ConnectorStatusInfo | REFACTOR → EXTEND | Keep protocol but Phase 2 needs SearchConnector interface returning SearchResult (see below) with provider/source_id/query_id/rank/publication_date/language/country. Will introduce `src/discovery/search_connector.py` with formal SearchResult + SearchResultNormalizer; keep base Protocol for backward compat |
| **WebSearchConnector** | `src/connectors/web_search.py` | httpx placeholder returning [] | KEEP as stub | Production-shaped connectors will live in src/discovery/providers/ |
| **Claim extraction** | `src/claims/extractor.py` | LLM.json → Claim rows | KEEP for verification phase | Candidate extraction is separate discovery concept (CandidateMention, not Claim) — will create new module, not reuse claim extractor |
| **Lifecycle** | `src/research/lifecycle.py` | JobLifecycle transition map + can_partial_complete | EXTEND | Add discovering substates if needed (smallest compatible change), keep PENDING→PLANNING→DISCOVERING→RETRIEVING→NORMALIZING→EXTRACTING→... existing. Will document compatible extension without breaking 161 tests |
| **API** | `src/api/v1/jobs.py` | POST /research/jobs → ResearchService.create_job + enqueue_research_job + warning if Redis down | KEEP | Vertical slice starts from same endpoint; worker now does real discovery |

### 2.3 Missing Components (NEW — does not exist)

| Component | Expected Location | Status |
|-----------|-------------------|--------|
| QueryExpansion / QueryPlanner | — | NEW |
| QueryPlan (structured queries with text/language/country/region/dimension/priority/parent_query/reason/source_restrictions) | — | NEW |
| SearchConnector formal interface search(query, options)→SearchResult[] | — | NEW (extension of Protocol) |
| SearchResult (result_id, query_id, title, url, domain, snippet, source_id, rank, publication_date, language, country, metadata) + normalization | — | NEW |
| Production-shaped search providers (TavilySearchConnector, BraveSearchConnector, GNewsConnector, RedditPublicConnector) + deterministic FakeConnector | — | NEW |
| DocumentFetcher (httpx, timeout 10s, retry 1, max 1MB, content-type, redirects, robots respect, failed fetch keeps SearchResult) | — | NEW (thin wrapper reusing DocumentIngestion) |
| CandidateExtractor (LLM structured_generate → CandidateMention with candidate_name/entity_type/description/evidence_text/confidence/source/document ref validation) | — | NEW |
| CandidateNormalizer (deterministic whitespace/punct/case/legal suffix strip, lower, alias via EntityRepository) | — | NEW |
| CandidateDeduplicator (L1 exact normalized name, L2 canonical domain/URL, L3 alias, L4 fuzzy >=0.92 difflib, L5 semantic deferred) | — | NEW |
| Discovery Provenance (candidate_id, query_id, source_id, document_id nullable, evidence snippet, timestamp, confidence, provider, method) | — | NEW |
| DiscoveryOrchestrator (bounded async coordination, budget, fallback A→B→C, idempotency, concurrency via Semaphore) | — | NEW |
| DB tables: search_results, candidate_mentions, candidate_discoveries/provenance | — | NEW (migration 003) |
| Evaluation benchmark 10–20 Q (ordinary/niche/geographic/company/low-visibility) | — | NEW |

---

## 3. Verdict Matrix — Full 14-Component Table (required)

| # | Component | File(s) | Verdict | Reason | Risk if Duplicated |
|---|-----------|---------|---------|--------|-------------------|
| 1 | **ResearchSpec** | `src/planner/models.py` | **KEEP** | Versioned spec_hash, budget integration correct, deterministic, idempotent | Duplicate spec model would break job persistence + hash consistency |
| 2 | **QueryExpansion** | NEW `src/discovery/query_planner.py` | **NEW** | No query expansion exists; planner only emits single ResearchSpec | Reusing claim planner would conflate intent parsing with query sharding |
| 3 | **QueryPlanner / QueryPlan** | NEW `src/discovery/query_planner.py` | **NEW** | No QueryPlan abstraction; existing research_queries is storage not planning logic. Must implement priority 1-5, dimension (7 dims), language/country/region, parent_query, reason, source_restrictions, budget-aware limits (2–16 queries), DRY dedup key (lower+trim+collapse + lang+country+source) | Hard-coding countries in Python would violate global-foundation requirement |
| 4 | **SearchConnector (interface)** | NEW `src/discovery/search_connector.py` (extends `src/connectors/base.py` Protocol) | **EXTEND** | Keep base Protocol for compat, introduce formal `SearchConnector` interface `search(query, options) → SearchResult[]` + concrete contracts | Second interface would leak provider formats; must normalize centrally |
| 5 | **SearchResult (+ Normalizer)** | NEW `src/discovery/models.py` + `search_normalizer.py` | **NEW** | No SearchResult model; RawResult leaks source-specific fields. Must define result_id (deterministic), query_id, title, url, domain, snippet, source_id, rank, publication_date, language, country, metadata; normalize all providers to this | Provider-specific formats leaking would break orchestrator agnosticism |
| 6 | **DocumentFetcher** | NEW `src/discovery/fetcher.py` (reusing `src/documents/ingestion.py`) | **NEW thin wrapper** | No fetcher with timeout(10s)/retry1/rate-limit/circuit/budget/max1MB/robots/content-type handling. Must delegate normalization/hash/dedup/store to existing DocumentIngestion — do NOT create second document system | Duplicate document pipeline would cause hash/dedup drift + orphan docs |
| 7 | **CandidateExtractor** | NEW `src/discovery/extractor.py` | **NEW** | ClaimExtractor extracts Claim vs Document; Phase 2 needs CandidateMention (candidate_name, entity_type, description, evidence_text, confidence 0-1, source/document refs assigned by system not LLM). Must use structured_generate + Pydantic schema validation, reject malformed/hallucinated IDs | Reusing ClaimExtractor would mix verification claim model with discovery candidate model |
| 8 | **CandidateNormalizer** | NEW `src/discovery/normalizer.py` | **NEW** | No candidate normalization; EntityRepository only does alias lookup without legal suffix stripping/case/punct folding. Must implement deterministic: whitespace/punct/case/legal suffixes (Ltd/Inc/GmbH etc) stripped, lowercased, alias via EntityRepository | Sophisticated probabilistic normalization deferred; conservative deterministic required |
| 9 | **CandidateDeduplicator** | NEW `src/discovery/deduplicator.py` | **NEW** | No candidate dedup layers. Must implement L1 exact normalized, L2 canonical domain/URL, L3 alias, L4 fuzzy difflib ≥0.92, L5 semantic deferred; explainable, conservative (false merge > duplicate) | Over-aggressive merge would collapse distinct entities — violates provenance fidelity |
| 10 | **DiscoveryOrchestrator** | NEW `src/discovery/orchestrator.py` | **NEW** | No bounded orchestrator; legacy ResearchOrchestrator is sequential two-pass without budget/concurrency/provenance. Must coordinate: load spec → QueryPlan → prioritize → execute searches (bounded) → normalize → persist search_results → fetch docs → ingest → extract candidates → normalize → dedup → persist provenance → update coverage → enforce budget → update job state. No provider-specific logic, no prompt details, no DB details in orchestrator | Giant agent anti-pattern forbidden — must separate components |
| 11 | **Discovery Provenance** | NEW `src/discovery/provenance.py` + DB `candidate_discoveries` | **NEW** | No provenance persistence for query×source×document×candidate multiplicity. Must persist multiple discovery records per candidate (not collapsed), fields: candidate_id, query_id, source_id, document_id nullable, evidence snippet, timestamp, confidence, provider, method; every candidate has ≥1 discovery | Orphan candidate breaks evidence traceability; provenance is core deliverable |
| 12 | **Budget integration** | **KEEP** `src/budget/manager.py` — extend usage | **KEEP** | BudgetManager already tracks search_calls, fetches, llm tokens/cost, reserve/record/snapshot/can_continue/hard-hit PARTIAL. Orchestrator must call `reserve` before search/LLM, `record_usage` after, `soft_hit` warning, `hard_hit` stop cleanly | Bypass would violate cost controls |
| 13 | **Concurrency** | NEW (asyncio.Semaphore via orchestrator + config `budgets.yaml`/`concurrency`) | **NEW** | No bounded concurrency; legacy orchestrator sequential. Must add max_concurrent_searches (e.g., 6), fetches (8), extractions (4) from budgets.yaml, explicit Semaphore, never unlimited | Unlimited gather would cause rate-limit storms + budget explosion |
| 14 | **State Machine** | **EXTEND** `src/research/lifecycle.py` + `src/core/types.py` | **EXTEND** | Current JobStatus has all V1 states but transitions only cover PENDING→PLANNING→DISCOVERING→RETRIEVING→NORMALIZING→EXTRACTING→VERIFYING→RED_TEAM→REPORTING→COMPLETED/PARTIAL/FAILED. Must integrate query planning/discovery/ingestion/extraction/dedup substates via smallest compatible change (map DISCOVERING→RETRIEVING→NORMALIZING→EXTRACTING to discovery pipeline stages, keep terminal PARTIAL logic, add `can_partial_complete` coverage) | Rewriting lifecycle would break 161 tests; smallest diff required |

### Additional Audited Components

| Component | Verdict | Reason |
|-----------|---------|--------|
| LLMProvider generate/structured_generate/stream/estimate_cost | KEEP | Correctly tested, no refactor |
| Source YAMLs (5 seeds) | KEEP | Real connector shape, SourceRegistry filtering works |
| Document deduplication (exact/canonical/content_hash) | KEEP | Deterministic, will reuse for result URL dedup (canonical lower+strip /, fragment) |
| API POST /research/jobs | KEEP | Correctly enqueues worker; vertical slice entrypoint |
| Worker idempotency (sha256 job+phase+hash) | KEEP | Retry-safe; extend to cover query/search_result/candidate hashes |
| Config path validation (models/budgets/sources/regions/languages) | KEEP | No secrets in YAML verified, budgets 6/8/4 concurrency proposed |
| Alembic 002 tables (research_queries, entities, source_registry, dimension_coverage) | KEEP | Will append 003 without altering 001/002 (append-only) |

---

## 4. Global Foundation Check

- `configs/regions/*.json` drives region/country/language — no hard-coded countries in Python ✓ (only ResearchSpec defaults geography=["global"])
- Hundreds of regions possible without code change — QueryPlanner will scan `configs/regions` directory dynamically ✓
- Languages similarly via `configs/languages` ✓
- Preferred sources per region already in JSON `preferred_sources` — planner will honor ✓

---

## 5. Security & Scope Gates

- No auth bypass, no CAPTCHA, no private social scrape — `reddit_public` is public only ✓
- Document max 1MB (`settings.max_document_size_bytes=1048576`) + max_content_length 500k enforced in ingestion ✓
- Structured logging present, API keys never logged (LLMProvider uses env, not log) ✓
- LLM outputs validated via Pydantic before DB (structured_generate contract) — will enforce for CandidateExtractor ✓
- External content treated as untrusted (normalizer + size checks) — fetch must preserve same ✓
- No Phase 3 creep detected: no recursive deep research, no scoring/report synthesis in pipeline yet — audit guards remain ✓

---

## 6. Audit Conclusion

**Phase 1 baseline is sound (161/161).** No infra rewrite needed. Phase 2 must **add 9 new modules**, **extend 3 existing** (SourceRegistry passthrough, lifecycle small delta, worker to call DiscoveryOrchestrator), **reuse 6 core subsystems** (ResearchSpec, BudgetManager, SourceRegistry, DocumentIngestion, LLMProvider/Router, API). All extensions are backward-compatible; 002 data intact; 003 will be additive.

**Required new files (anticipated):**
```
src/discovery/__init__.py
src/discovery/query_planner.py      # QueryPlan, QueryExpansion, priority/budget/dimension limits
src/discovery/models.py             # SearchResult, CandidateMention, Candidate, Provenance dataclasses
src/discovery/search_connector.py   # SearchConnector Protocol + SearchResultNormalizer
src/discovery/providers/base.py
src/discovery/providers/tavily.py
src/discovery/providers/brave.py
src/discovery/providers/gnews.py
src/discovery/providers/reddit.py
src/discovery/providers/fake.py     # deterministic fake for tests
src/discovery/fetcher.py            # DocumentFetcher (httpx 10s, retry1, 1MB, robots)
src/discovery/extractor.py          # CandidateExtractor (structured_generate, schema validation)
src/discovery/normalizer.py         # CandidateNormalizer (legal suffixes, alias)
src/discovery/deduplicator.py       # CandidateDeduplicator L1-L5 conservative
src/discovery/provenance.py         # Provenance recorder
src/discovery/orchestrator.py       # DiscoveryOrchestrator (bounded concurrency, fallback, budget, idempotency)
alembic/versions/003_add_discovery_tables.py
configs/regions/*.json (reuse) + configs/languages/*.json (reuse)
tests/evaluation/benchmark_*.json + tests/unit/test_discovery*.py + tests/integration/test_discovery*.py
```

**Modified (append-only, backward compatible):**
- `src/research/lifecycle.py` — smallest transition tweak if needed
- `src/sources/registry.py` — expose tier/authority_score/timeout passthrough
- `src/worker/tasks.py` — wire DiscoveryOrchestrator, preserve idempotency/budget/logging
- `alembic/env.py` — import new models (if needed)

**Mirrored path:** `C:\Opencode\docs\PHASE2_IMPLEMENTATION_AUDIT.md` must equal this file.

---

## 7. Next Step

Proceed to implementation order (per prompt):

1. Audit ✓ (this file)
2. QueryPlanner/QueryPlan
3. SearchConnector + SearchResult + Normalizer + Providers + Fake
4. DocumentFetcher (reuse ingestion)
5. CandidateExtractor/Normalizer/Deduplicator
6. DB migration 003 (candidate_mentions, candidate_discoveries/provenance, search_results)
7. DiscoveryOrchestrator (bounded concurrency, budget, fallback A→B→C, idempotency, provenance)
8. Wire worker/state machine
9. Benchmark 10–20 Q
10. Integration mocked discovery job
11. 161 baseline + new tests pass, alembic upgrade head
12. Docs PHASE2_IMPLEMENTATION.md + FUTURE.md update
13. Final 24-checkbox DoD audit

*No duplicate abstractions will be created.*
