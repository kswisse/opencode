# Phased Implementation Plan — Global Multi-Source Intelligence Engine V1

**Version:** V1 Freeze 2026-08-26  
**Phases:** 0–9 (0 = freeze, 9 = release-ready)  
**Source of Truth:** This doc + `docs/ARCHITECTURE.md` ADRs + `docs/DATA_MODEL.md` migrations  
**Principle:** *Each phase ends with a Definition of Done (DoD) that is demonstrable, tested, and eval-measured. No phase advances without DoD.*

---

## Phase Map (Spec Alignment)

| Phase | Name | Corresponds to Spec | Duration Estimate* | DoD Gate |
|-------|------|---------------------|-------------------|----------|
| **0** | Architecture Freeze | Spec Phase 0 | 1 week (this freeze) | 7 docs + repo inspection + phased plan + risks + vertical slice — human sign-off |
| **1** | Foundation & Vertical Slice | Infra + LLM abstraction + Source registry + Minimal pipeline | 2 weeks | Vertical slice E2E (query→report) with real PG/Redis, stub LLM, 2 connectors, citation report |
| **2** | Planner & Query Expansion | Prompt parsing, planning, query expansion, multi-region/lang config | 1.5 weeks | Planner produces shards × regions × langs, tested on cat F benchmarks, coverage dims seeded |
| **3** | Discovery & Extraction | Multi-region web/news/social discovery, candidate extraction, dedup | 2 weeks | 8–16 parallel shards, dedup stats, 40+ docs/job, candidate set deduped, category A recall ≥0.75 stubbed |
| **4** | Entity Resolution & Qualification | Entity resolution, aliases, candidate dedup, qualification | 1.5 weeks | Entity resolution accuracy ≥0.85 on cat A/F, alias collapse, candidate set qualified |
| **5** | Deep Research & Recursion | Deep research, gap detection, recursive loop, budget/stopping | 2 weeks | Gap detection + recursive loop bounded, budget hard/soft enforced, coverage+gain stopping proven |
| **6** | Evidence & Verification | Claim→Evidence→Source chain, provenance, contradiction, scoring | 2 weeks | Evidence anchored (≥0.90 citation coverage), verification 5-state, contradiction recall ≥0.70, deterministic scoring |
| **7** | Evaluation Harness | Benchmarks A–H, harness, baseline comparison | 1.5 weeks | 24–40 benchmarks × 3 variants, harness in CI, comparison table, regression gate |
| **8** | API + Minimal UI Polish | Basic API surface, UI, report generation, observability hardening | 1.5 weeks | All `/api/v1/*` endpoints, Next.js pages (submit/history/report/eval), citation badges, metrics + traces |
| **9** | Hardening & Release | Migrations squash check, perf, cost tuning, release report | 1 week | All evals green, budget within depth targets, docs frozen, release notes with eval appendix |

*Estimates assume 1 senior + 1 mid engineer + eval/fixtures support; compressible with more parallel workers inside phases.*

---

## Phase 0 — Architecture Freeze (Current — DoD Checklist)

**Goal:** Freeze all V1 contracts so Phases 1–9 execute without re-architecture.

**Deliverables (Freeze):**
- [x] `docs/ARCHITECTURE.md` (logical arch, module boundaries, LLM/source abstractions, worker/queue, API, repo justification, smallest vertical slice)
- [x] `docs/DATA_MODEL.md` (full DDL 002–005, ER, pgvector, migrations)
- [x] `docs/AGENT_CONTRACTS.md` (6 roles, I/O, DAG, retry/idempotency, budget)
- [x] `docs/SOURCE_MODEL.md` (registry schema, tiers 1-5, authority/coverage/access_method, discovery/verification/context separation)
- [x] `docs/EVIDENCE_MODEL.md` (CLAIM→EVIDENCE→SOURCE→DOCUMENT, verification states, contradiction, citations)
- [x] `docs/RESEARCH_STATE_MACHINE.md` (13 states, coverage dims FOUND/MISSING/UNCERTAIN/CONTESTED, 5 stopping criteria)
- [x] `docs/EVALUATION.md` (categories A–H, 11 metrics, 3-baseline comparison, harness)
- [x] `docs/FUTURE.md` (deferred list with rationale)
- [x] `docs/REPO_INSPECTION.md` (new vs existing, reusable, conflicts)
- [x] `docs/PHASED_PLAN.md` (this file — DoD per phase, risks, dependencies, vertical slice)
- [ ] Human review + sign-off (6 open questions in ARCHITECTURE.md §11, plus cross-doc opens) → **freeze locked**

**Exit Gate:** No code beyond `docs/` until sign-off.

---

## Phase 1 — Foundation & Vertical Slice

**Goal:** Minimal E2E that proves infra + LLM abstraction + discovery→report loop with minimal external deps.

### Scope
- `docker-compose.yml` (postgres:16+pgvector, redis:7, api, worker, web) + `.env.example` + `alembic upgrade head`
- `packages/llm` V1 contract (`generate/structured_generate/stream/estimate_cost`) + `StubProvider` + `RecordingProvider`, cost accumulator, budget table plumbing
- `packages/sources` registry YAML loader + validator + `sources` table cache (2 sample sources: `tavily`, `sec_edgar`)
- `configs/sources/*.yaml`, `configs/scoring/budget.yaml` (placeholders)
- Hardened `ResearchJob` → `research_runs` split (migration 002 subset)
- Single happy-path orchestrator variant: `POST /research` → planner stub (1 query) → discovery (2 connectors mocked in CI) → fetch 5 docs via `StubConnector` → normalize/dedup → claim extract via `StubProvider` (3–5 claims) → verify (supporting=1) → score → report markdown
- API: `POST /research`, `GET /research/{id}`, `GET /research/{id}/report`, `GET /health`
- Tests: vertical slice integration test (`tests/integration/test_vertical_slice.py`) + unit for LLM registry/budget

### DoD
- `docker-compose up --build` boots all services, `pytest` green (including vertical slice).
- One fixed query (e.g., "Acme AI Berlin 2023") produces a citation-backed markdown report via API + UI job page, with `job_id` correlation in logs and `research_runs.cost_usd` recorded.
- No real external API keys required (stubs).
- `alembic upgrade/downgrade` clean.

### Risks & Mitigations
- **Risk:** pgvector image pull flakiness → Mit: pin `pgvector/pgvector:pg16`, cache layer, fallback to `postgres:16` + manual `CREATE EXTENSION`.
- **Risk:** Stub fidelity hides real LLM/connector bugs → Mit: `RecordingProvider` fixture to replay real LiteLLM JSON, not handmade stubs only.

### Dependencies
- Phase 0 sign-off.

---

## Phase 2 — Planner & Query Expansion

**Goal:** Prompt parsing, query expansion, multi-region/language sharding, and coverage dimension seeding.

### Scope
- `packages/planner`: `PromptParser`, `QueryExpander`, `PlanningService` reading `configs/regions/*.json` and `configs/languages/*.json`
- Region inference (keywords/TLD hints) + language detect + transliteration for aliases
- Expanded queries 2–5 (quick), 5–10 (standard), 10–16 (deep) with `region`/`language`/`purpose` sharding
- `research_queries` table + `CoverageMatrix` seeding
- Planner tests on cat F Vietnamese/Russian benchmarks (stubbed connectors)
- Configs: `us.json`, `eu.json`, `vn.json`, `ru.json` + `languages/vi.json`

### DoD
- Planner on query "Công ty AI Hà Nội 2023 gọi vốn" emits shards for `regions=[vn, global]` `languages=[vi, en]` with at least one `vi` shard.
- Query expansion recall ≥ 0.75 on cat A subset (via eval harness stub).
- Budget estimate emitted per plan, gated by `budget_soft`.

### Risks
- **LLM cost explosion for expansion** → Mit: temperature 0.3 + max 16 shards + deterministic prune if estimate > soft.
- **Region inference over-triggers** → Mit: deterministic keyword/TLD heuristics first, LLM only for ambiguous queries.

### Dependencies
- Phase 1 (LLM contract, budget plumbing, `research_queries`).

---

## Phase 3 — Discovery & Extraction

**Goal:** Multi-region web/news/social discovery at scale, candidate extraction, dedup.

### Scope
- `packages/search`: `TavilyConnector`, `BraveConnector` (+ `SearX` stub), `NewsConnector` (GDELT/NewsAPI)
- `packages/social`: `RedditPublicConnector`, `XPublicConnector` (stubbed if no key), bounded social fetch
- `packages/crawling`: `Fetcher` (httpx + `robots.txt`), `Extractor` (trafilatura/BS4), Playwright fallback (opt-in)
- `packages/discovery`: `DiscoveryOrchestrator` fan-out 8–16 shards, dedup (exact URL, canonical, content_hash, near-duplicate via embeddings)
- `packages/extraction`: chunking, embedding (`litellm.embedding`), citation span prep
- Candidate extraction (heuristic + LLM) — pre-resolution candidate set
- `retrieval_runs` per connector per run + `connector_statuses` partial handling

### DoD
- 12-shard plan fans out to 12 parallel searches, 60+ raw results → ≥40 deduped docs/job.
- Dedup stats correct: exact_url + content_hash + near_duplicate (via stubbed embeddings) measured.
- Category A recall ≥0.75 on stubbed fixtures; discovery handles partial connector failure (→ `PARTIAL` not `FAILED`).
- Crawling respects `robots.txt`; social only public (CI guard validates).

### Risks
- **Rate limits / 429 storms** → Mit: per-source token bucket + circuit breaker + 503→partial.
- **Playwright flakiness** → Mit: fallback disabled by default, only on `scrape` failure + flag.

### Dependencies
- Phase 2 (shards).

---

## Phase 4 — Entity Resolution & Qualification

**Goal:** Resolve canonical entities, aliases, candidate dedup, qualification rules.

### Scope
- `packages/entities`: `EntityResolver`, alias normalization (lower + strip + transliterate + trigram), alias collapse, candidate set dedup (cosine + shared domain)
- Domain projections: `companies`, `people`, `funding_rounds/investors/markets` — lean projections from claims/evidence
- `entities` / `entity_aliases` tables, `graph_nodes` with `mentions` edges
- Qualification: deterministic rules (e.g., `confidence >= 0.5 && evidence_count >=2` or tier-1 present)
- Region/lang specific alias handling (e.g., "Hà Nội AI" transliteration)

### DoD
- Entity accuracy ≥0.85 on cats A/F (stubbed), alias collapse idempotent.
- Candidate set dedup correct for cases like "Acme AI vs Acme Corp" disambiguation hint.
- `companies` rows queryable with `funding_rounds` linkage.

### Risks
- **Entity conflation (two firms same name)** → Mit: require domain/shared alias + evidence count, flag `uncertain` if collision.
- **LLM over-extraction** → Mit: confidence threshold 0.7 + at-least-2-evidence gate.

### Dependencies
- Phase 3 (documents).

---

## Phase 5 — Deep Research & Recursion

**Goal:** Gap detection, recursive deep research loop, budget-aware stopping.

### Scope
- `packages/research/gap_detector.py`: coverage matrix per candidate (10 dims) → `FOUND/MISSING/UNCERTAIN/CONTESTED` → `GapReport` + `gap_queries`
- `packages/research/budget.py`: `BudgetController` (hard/soft) + `research_runs.stopping_reason`
- Deep Research workers: tier-aware gap queries (funding → tier 1-2, market → tier 2-3)
- Recursive loop: `GAP → DEEP → GAP` until coverage+diminishing+budget+iterations+confidence
- `scores` table not yet (next phase), but coverage confidence uses claim `extraction_confidence` until scorer exists

### DoD
- Gap detection identifies `funding: MISSING` → emits tier 1-2 gap query → fetches additional docs → matrix updates to `FOUND`.
- Budget soft/hard enforced: soft stops new iteration, hard stops fetches mid-iteration, both produce `PARTIAL` with reason.
- Max iterations 1/2/3 by depth respected; diminishing gain (<5%) early-stops.
- Integration test: 2-iteration recursive run with stubbed deep docs achieves coverage_complete.

### Risks
- **Endless loop on contested dimension** → Mit: contested is terminal for that dim (no further gap_fill for contested → verify handles it).
- **Budget miscount** → Mit: every LLM/fetch calls `record_*` synchronously; nightly check `sum(cost) ≈ budget_spent`.

### Dependencies
- Phase 4 (entities/candidates).

---

## Phase 6 — Evidence & Verification

**Goal:** Full CLAIM→EVIDENCE→SOURCE→DOCUMENT chain, anchored citations, tier-weighted verification, contradiction detection, deterministic scoring.

### Scope
- `evidence` / `claim_evidence` / `claim_sources` tables + repos
- Citation char-offset normalizer (`content.find(snippet)` validation)
- `VerificationEngine` 5-state mapping + `ProvenanceAnalyzer` independence (copy-graph via embeddings + lineage)
- `ContradictionEngine` (pairwise numeric/temporal, severity)
- Deterministic scorer/ranker (`packages/scoring`): tier-weighted support, recency, coverage, explainable factors + rank
- `verification_runs`, `scores` persistence

### DoD
- ≥0.90 citation coverage (claims with ≥1 anchored evidence span).
- Verification states match expected on cat G contradictions benchmark (recall ≥0.70).
- Scoring deterministic: same evidence set → same `final_score` + `rank` (test via double-run).
- Contradiction severity `critical` flagged correctly for tier 1 vs tier 1 numeric conflict.
- Evidence spans have `char_start/end` or snippet-only fallback documented.

### Risks
- **Snippet hallucination (LLM invents snippet not in doc)** → Mit: substring validation ≥0.92, discard or penalty if not found.
- **Source independence over-penalty** → Mit: domain diversity + lineage confidence threshold before penalty.

### Dependencies
- Phase 5 (claims from deep research).

---

## Phase 7 — Evaluation Harness

**Goal:** Benchmarks, baselines, harness, and CI gating.

### Scope
- `benchmarks/` 24–40 JSON files (categories A–H) + `benchmarks/fixtures/` (recorded doc payloads)
- `tests/evals/harness.py`, `baselines.py`, `metrics.py`, `reporter.py`
- 11 metrics computed deterministically
- `benchmarks` / `eval_runs` tables + `api/v1/eval.py` endpoints (`POST /eval/runs`, `GET /eval/runs/{id}`, `GET /eval/benchmarks`)
- CLI `scripts/eval.py`
- CI: stubbed eval on PR, live eval nightly (if keys)

### DoD
- `python scripts/eval.py --category A,B,G,H --variants engine,baseline_search,baseline_llm --stubbed` produces comparison table with all 3 variants and deltas.
- CI fails PR if any category mean drops >5% vs main.
- `GET /eval/runs?benchmark=cat_B_acme_seed_2023` comparison JSON correct.
- 11 metrics correct per spec (unit-tested).

### Risks
- **Fixture drift vs live** → Mit: fixtures immutable; live drift tracked separately, not auto-overwritten.
- **Ground truth subjectivity** → Mit: benchmarks store `expected_claims` as normalized_text + triple; cosine match 0.88 threshold, not exact string.

### Dependencies
- Phases 1–6 (engine to evaluate).

---

## Phase 8 — API + Minimal UI Polish

**Goal:** Complete API surface, Next.js minimal UI, report generation, observability hardening.

### Scope
- API completeness: `POST /research`, `GET /research/{id}`, `GET /research/{id}/report` (markdown+JSON), `GET /research/{id}/claims`, `GET /research/{id}/evidence`, `GET /research/{id}/documents`, `GET /research` (history), `POST /research/{id}/retry`, `GET /sources`, `GET /eval/*`, `GET /health`
- `ReportGenerator`: citation-backed markdown + JSON with `†`dagger primary badges, contradictions callout, confidence badges
- `apps/web` (Next.js): `/` (form), `/jobs` (history), `/jobs/[id]` (progress+budget+coverage), `/jobs/[id]/report`, `/eval` (comparison table) — Tailwind, no graph viz
- Observability: OTEL spans, Prometheus metrics, `structlog` correlation
- Error handling: `429 budget`, `503 connector degraded`, `last_error` disclosure

### DoD
- API manual smoke: create job → poll → report returned with citations and `cost_usd` + `partial_reason` if partial, paginated.
- UI: create job, watch live progress (2s poll), view report with citation popovers, view eval comparison.
- `GET /health` includes DB/Redis/LLM connector checks.
- OTEL traces and Prometheus counters visible (at least `llm_cost_usd`, `discovery_docs_total`, `verification_claims_total`).

### Risks
- **XSS via markdown report** → Mit: markdown sanitized, links `rel=nofollow`, no raw HTML.
- **Report N+1 query storm** → Mit: bulk fetch `claims`+`evidence`+`sources` in one join per run.

### Dependencies
- Phase 7 (eval endpoints share API plumbing).

---

## Phase 9 — Hardening & Release

**Goal:** Release-ready: migrations finalized, perf/cost tuning, documentation, release notes with eval appendix.

### Scope
- Migration finality: 002–005 reviewed, forward-only prod path documented, `alembic check`
- Perf: report p95 < 200ms (cached), discovery p95 < 15s for standard, eval latency/cost tracked vs depth budgets
- Cost tuning: depth budgets validated against median of last 20 eval engine runs
- Security review: `MAX_DOCUMENT_SIZE`, `MAX_CONTENT_LENGTH`, prompt-injection tests expanded for planner verification
- Release notes: `docs/RELEASE_NOTES.md` with eval comparison (engine vs baseline_search vs baseline_llm) appendix, known limitations, deferred list link
- Docs freeze: all V1 docs marked `V1` with version, arch diagrams exported

### DoD
- All evals green (per-category thresholds met) on full 40 benchmarks with both stubbed and live (if available) runs.
- Budget within depth soft targets for median job per depth.
- `docker-compose up && pytest && python scripts/eval.py` passes from clean clone.
- Release tag `v1.0.0` with `docs/ARCHITECTURE.md` frozen.

### Risks
- **Last-mile migration pain** → Mit: no schema changes after Phase 8 without sign-off; migration dry-run on staging PG.
- **Cost regression post-tuning** → Mit: cost is a tracked metric, not a hard gate, but CI warns if p50 cost > soft+10%.

### Dependencies
- Phases 7–8 (evals + API/UI).

---

## Dependency Graph (Phases)

```
0 (freeze)
  └─▶ 1 (foundation/slice)
        └─▶ 2 (planner)
              └─▶ 3 (discovery/extraction)
                    └─▶ 4 (entity resolution)
                          └─▶ 5 (deep+recursive+budget)
                                └─▶ 6 (evidence+verification+scoring)
                                      └─▶ 7 (eval harness)
                                            └─▶ 8 (API+UI)
                                                  └─▶ 9 (hardening/release)
```

No phase can start until prior phase DoD is met (hard gate). Phases 2–3 and 7–8 have some parallelizable subtasks inside, but phases themselves are sequential because each builds on the prior's DB and contracts.

---

## Smallest Viable Vertical Slice (Detailed)

> Also summarized in `docs/ARCHITECTURE.md` §10. Detailed spec for Phase 1.

### Slice Query
`"Acme AI Berlin 2023 seed startup"` (fixed, deterministic)

### Slice Config
- `depth=standard`, `regions=[eu]`, `languages=[en]`
- 2 sources: `tavily` (mocked via `StubConnector`) + `sec_edgar` (mocked)
- 1 planner shard (no region expansion for simplicity)

### Slice Steps & Expected Artefacts

```
POST /research {query: "Acme AI Berlin 2023 ..."} → 201 {job_id, run_id, status: pending}
  │
  ├─ Planner: 1 shard → research_queries [1]
  ├─ Discovery: 2 connectors × 1 shard → 6 RawResults → 5 documents (1 deduped by content_hash)
  ├─ (No entity resolution yet — single candidate skipped)
  ├─ (No deep research — no gaps)
  ├─ Claims: StubProvider emits 4 claims (2 identity, 1 founders, 1 funding $3M)
  ├─ Verify: claims 1,2 → SUPPORTED, claim 3 → VERIFIED (if 2 docs corroborate), claim 4 → SUPPORTED (1 tier-1)
  ├─ Score: deterministic (factors computed)
  └─ Report: markdown with 4 citations + JSON payload

GET /research/{id}/report → {markdown: "# Acme AI ... [1†]...", json: {claims:[...], citations:[...]}, cost_usd: 0.12}
```

### Slice Infra
- `docker-compose` PG+Redis+API+Worker (web optional but not required for slice).
- Stubs: `StubConnector(search→6 RawResults)`, `StubLLMProvider(extract→4 claims)`.
- No `Playwright`, no social, no region/lang expansion, no recursive.

### Why This Slice Validates V1 Architecture
- Proves HTTP → Planner → Discovery → Document → Claim → Verification → Scoring → Report loop.
- Validates `research_jobs`/`research_runs`/`research_queries` wiring, idempotency, budget recording, evidence chain (claim→evidence→doc→source), and citation report.
- Entity resolution, deep recursion, multi-region, social, and eval harness layer on top with contracts already frozen — slice doesn't preclude them.

### Slice Tests
- `tests/integration/test_vertical_slice.py`: assert `POST` → poll `GET` until `completed` → `GET /report` contains `[1]` citations and `cost_usd > 0`.
- Unit: `test_llm_provider_v1_contract.py` (generate/structured_generate/stream/estimate_cost), `test_source_registry_loader.py`, `test_budget_controller_soft_hard.py`.

---

## Architectural Risks & Mitigations (Cross-Phase)

| # | Risk | Likelihood | Impact | Mitigation (Where Addressed) |
|---|------|------------|--------|------------------------------|
| 1 | **Unauthorized scraping temptation** (planner emits source that needs login/private) | Medium | High (legal) | Registry validator blocklist (`SOURCE_MODEL.md` §8) + CI guard + worker hard-abort, docs hard gate |
| 2 | **LLM cost explosion** (recursive loop or overly many shards) | Medium | High (budget) | BudgetController hard/soft, `max_shards`/`max_iterations` caps, deterministic prune, eval cost tracking, phase 5 hardening |
| 3 | **Entity resolution accuracy drift** (conflates two companies same name) | Medium | High (correctness) | Require domain/alias + evidence count, flag contested, eval cat A/F, phase 4 |
| 4 | **Source quality drift** (tier 2 press hallucinates, tier curator missed) | Low | Medium | Registry PR review, quarterly tier audit, verification weighting uses `authority_score` not just tier, eval primary-ratio metric |
| 5 | **Claim hallucination (LLM extracts unsupported claims)** | High | High | Snippet validation ≥0.92, `extraction_confidence<0.4` gate, verification 5-state not LLM-decided, eval precision |
| 6 | **Contradiction blindness** (misses tier1 vs tier1 conflict) | Medium | High (trust) | Pairwise numeric/temporal detector deterministic, `critical` severity, cat G benchmarks, phase 6 |
| 7 | **Latency regression** (deep loop adds 30s+ per iteration) | Medium | Medium (UX) | Iteration cap 1–3, streaming report via polling, OTEL traces per iteration, phase 9 perf gate |
| 8 | **pgvector index drift** (HNSW not built, exact scan slow on 500k) | Low | Medium | Index strategy §DATA_MODEL.md (defer HNSW to 004), nightly eval with 500k fixture before ship |
| 9 | **Migration breakage** (adding non-nullable column without backfill) | Medium | High | Migration 002 nullable+backfill first, 004 not-null, `alembic check` in CI, phase 9 migration audit |
| 10 | **Eval ground truth staleness** (benchmarks drift as web changes) | High | Medium | Fixtures immutable, stubbed eval is source of truth for CI; live eval nightly tracks drift separately, not auto-overwrites fixtures |

### Prioritization Order Enforced

Every mitigation respects `CORRECTNESS → EVIDENCE → COVERAGE → COST → PERFORMANCE → UX`. Example: we never trade verification accuracy for latency; we stop recursive depth for budget before costing, but not before coverage disclosure.

---

## Resource & Timeline Notes

- **No Kafka/K8s/Neo4j infra to provision** — keep ops lean.
- **Keys needed for live eval (Phase 7+):** `TAVILY_API_KEY`, `BRAVE_API_KEY` or SearX self-host, `REDDIT_CLIENT_ID` (optional), `OPENAI_API_KEY` or Anthropic/Gemini key. Stubbed runs work without any.
- **Hiring:** No custom ML hiring in V1 — deterministic components first.
- **Documentation debt:** Each phase writes/updates its `docs/*.md` section; PR template requires arch-decision checkbox ("Does this PR change a frozen contract? If yes, attach doc update").

---

## Exit Criteria for V1 Release (Phase 9 Gate)

- [ ] All 33 V1 items demonstrable via API or UI (trace from spec checklist).
- [ ] Eval: ≥0.75 recall (standard), ≥0.90 citation coverage, ≥0.70 contradiction recall, ≥0.85 entity accuracy on respective cats — or documented `PARTIAL` disclosure where not met.
- [ ] Budget median within `quick $1 / standard $2 / deep $5` soft caps on eval engine runs.
- [ ] `docker-compose up && pytest && python scripts/eval.py --stubbed` green from clean clone.
- [ ] `FUTURE.md` deferred list respected (no scoped creep in `main`).
- [ ] Human sign-off on open questions (ARCHITECTURE.md §11, DATA_MODEL.md §7, etc.) or explicit deferral recorded.

---

**Next:** Phase 0 sign-off → Phase 1 kickoff (create `global-intelligence-engine/` layout or evolve `evidence-engine/` alias, add `docker-compose.yml`, extend `LLMProvider` contract).
