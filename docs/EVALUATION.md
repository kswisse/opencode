# Evaluation — Benchmarks, Metrics, and Harness

**Version:** V1 Freeze 2026-08-26  
**Packages:** `tests/evals/`, `benchmarks/`, `packages/scoring` (metrics calc)  
**DB:** `benchmarks`, `eval_runs`  
**Principle:** *You cannot improve what you cannot measure. Every change must be comparable on the same benchmarks against the same baselines.*

---

## 1. Goals

- Provide **repeatable, evidence-grounded** measurement of engine quality vs two fixed baselines.
- Gate every PR and release: "Did recall/source diversity/entity accuracy regress?"
- Separate **cost/latency** from **quality** — a cheaper wrong answer is not better.
- Drive iterative improvement via per-category benchmarks (A–H) that map to V1 risks.

---

## 2. Benchmark Categories A–H (V1 — 8 Categories, ~40 Benchmarks Total)

Each category targets a distinct capability. Each benchmark is a JSON file in `benchmarks/<slug>.json` + row in `benchmarks` table.

| Cat | Name | What It Tests | Example Queries (3 per cat shown) | Ground Truth | Primary Risk Mitigated |
|-----|------|---------------|------------------------------------|--------------|------------------------|
| **A** | Entity Identity | Correctly identifying candidate entity (company/person) from prompt | "Acme AI Berlin 2023 seed AI startup" / "Founder of Perplexity AI" / "OpenAI founding date" | `expected_entities: [{canonical_name, normalized, type, domain}]` | Entity resolution accuracy |
| **B** | Funding & Investors | Amounts, dates, round type, investors (numeric + attribution) | "Acme AI seed round $3M lead investor" / "Series A for Anthropic 2023" / "Who led Seed for X 2024?" | `expected_claims: [{normalized_text, subject, predicate, object, event_time, amount_usd, investors[]}]` | Numeric hallucination, attribution error |
| **C** | Product & Technology | Product surface, tech stack, IP | "What does Acme AI build?" / "Tech stack of Notion AI" / "Patents held by DeepMind" | `expected_claims` + `coverage_dimension=product|tech` | Vague/unsupported product claims |
| **D** | Growth & Traction | Users, revenue, metrics, hiring signals | "Acme AI user count 2024" / "Revenue of Figma 2023" / "Headcount of OpenAI 2024" | `expected_claims` with numeric thresholds | Metric conflation, staleness |
| **E** | Market & Competition | Market size, competitors, positioning | "AI observability market size 2024" / "Competitors to Datadog" / "Positioning of Acme AI vs rivals" | `expected_claims` for market/competition dims | Source diversity, trade-press over-trust |
| **F** | Multi-Language / Multi-Region | Regional/language sharding, transliteration | "Công ty AI Hà Nội 2023 gọi vốn" (VI) / "Стартап ИИ Москва 2023" (RU) / "AI startup Shenzhen 2023" (ZH context via EN) | `expected_entities` with region/lang + alias transliteration | Regional bias, alias miss |
| **G** | Claim Verification & Contradiction | Verification states + contradiction detection under conflict | Query where two tier-1 sources disagree on amount/date | `expected_claims` with `expected_status` + `expected_contradictions: [{claim_a, claim_b, type, severity}]` | Verification calibration, contradiction blindness |
| **H** | Citation & Provenance | Evidence anchoring, citation coverage, primary-source ratio | Any above query but scored on citation | `expected_evidence_spans` — ground truth docs with primary flags | Bare URLs, unsupported claims |

**V1 count:** 5 benchmarks per category × 8 = **40 benchmarks** (4 per cat minimum, 40 total target; ship with 24 and expand to 40 by Phase 8). Each benchmark is ~1 query + ground truth + time_range hint.

**Benchmark JSON shape:**

```json
{
  "slug": "cat_B_acme_seed_2023",
  "category": "B",
  "name": "Acme AI seed round (amount + lead)",
  "description": "Verify amount, date, lead investor for Acme AI seed 2023",
  "query": "Acme AI seed round funding amount and lead investor 2023",
  "regions": ["eu"],
  "languages": ["en"],
  "time_range": ["2023-01-01","2023-12-31"],
  "depth": "standard",
  "expected_entities": [
    {"canonical_name": "Acme AI","type": "company","domain": "acme.ai"}
  ],
  "expected_claims": [
    {"normalized_text": "Acme AI raised $3M seed round on 2023-06-15 led by Speedrun","subject":"Acme AI","predicate":"raised","object":"$3M seed","event_time":"2023-06-15","amount_usd":3000000,"investors":["Speedrun"] }
  ],
  "expected_evidence_spans": [
    {"url_contains": "sec.gov","is_primary": true, "snippet_contains": "$3,000,000"}
  ],
  "expected_contradictions": [],
  "metrics_config": {"recall_threshold": 0.8, "primary_ratio_threshold": 0.3}
}
```

---

## 3. Metrics (V1 — 11 Metrics, Per-Benchmark + Aggregate)

### 3.1 Quality Metrics

| # | Metric | Definition | How Computed | Target (V1) | Category Weight |
|---|--------|------------|--------------|-------------|-----------------|
| 1 | **Recall** | Fraction of `expected_claims` found (matched) | `matched / expected` where match = `cosine(claim.embedding, expected.embedding) > 0.88` + predicate/object overlap | ≥ 0.75 (standard), ≥ 0.85 (deep) | All |
| 2 | **Precision** | Fraction of returned claims that are correct (not hallucinated) | `correct / returned` where correct = matched to any expected or verified via tier-1 | ≥ 0.70 | All |
| 3 | **Claim F1** | Harmonic mean of recall+precision at claim level | `2PR/(P+R)` | ≥ 0.72 | G, H |
| 4 | **Source Diversity** | Distinct sources/tiers/regions represented | `distinct(source_id) / returned_claims` + tier entropy | `distinct ≥ 3` + entropy ≥ 0.7 | E, F |
| 5 | **Regional Coverage** | Was region-sharded discovery executed? | `shards with region==benchmark.region >0 AND docs from that region >0` | 1.0 for F | F |
| 6 | **Language Coverage** | Was language-sharded discovery executed? | similar to regional | 1.0 for F | F |
| 7 | **Entity Accuracy** | Correct entity resolved (canonical + aliases) | `entity_match = normalized_name exact OR alias trigram >0.88` | ≥ 0.85 | A, F |
| 8 | **Citation Coverage** | Fraction of claims that have ≥1 evidence span with char offsets | `claims_with_evidence / total_claims` | ≥ 0.90 | H |
| 9 | **Primary-Source Ratio** | Fraction of claims supported by tier-1 primary evidence | `claims_with_primary / total_claims` | ≥ 0.30 (target), measure not gate in V1 | B, G, H |
| 10 | **Contradiction Recall** | Fraction of `expected_contradictions` detected | `detected / expected` | ≥ 0.70 | G |
| 11 | **Cost/Latency** | `cost_usd`, `latency_ms` (p50/p95), `tokens` | instrumented per run | `cost ≤ depth_budgets.soft` | All (separate track) |

**Metric computation location:** `packages/scoring/metrics.py` (deterministic, no LLM). Each metric has a pure function `metric(expected, actual) -> float + details`.

### 3.2 Aggregate Views

- **Per-category aggregate:** mean + median + pass-rate (fraction ≥ threshold).
- **Overall:** weighted mean across categories (equal weights in V1).
- **Regression guard:** CI fails if any category mean drops > 5% vs main branch baseline.

---

## 4. Baselines (Must Compare 3 Variants on Every Eval Run)

| Variant | `engine_variant` | What It Is | Purpose |
|---------|------------------|------------|---------|
| **BASELINE SEARCH** | `baseline_search` | Direct search connector results → naive dedup → top-K snippets as “report” (no LLM extraction, no verification, no scoring) | Lower bound — measures value of verification/synthesis |
| **BASELINE LLM** | `baseline_llm` | Raw LLM prompt (query → LLM with no retrieval) → answer with no citations | Upper bound for hallucination; lower bound for grounding |
| **ENGINE** | `engine` | Full V1 engine (planner→discovery→…→report) with same connectors | The candidate under test |

**Comparison table (per benchmark, per eval run):**

```
Benchmark: cat_B_acme_seed_2023

                    Recall  Precision  F1    Citation  Primary  Cost    Latency
baseline_search     0.45    0.60       0.51  0.10      0.05     $0.01   1200ms
baseline_llm        0.60    0.40       0.48  0.00      0.00     $0.03    800ms
engine (V1)         0.85    0.78       0.81  0.95      0.40     $1.40   8200ms
```

Harness automatically runs **all 3 variants** per benchmark per `eval_runs` invocation and stores each as separate `eval_runs` rows sharing a `group_id`.

---

## 5. Harness Design

### 5.1 Components

```
benchmarks/                 # JSON files, one per benchmark (versioned)
  cat_A_*.json
  cat_B_*.json
tests/evals/                # harness code
  harness.py               # BenchmarkHarness: load → run variant → score → persist
  baselines.py             # BaselineSearch / BaselineLLM runners
  metrics.py               # 11 metric calculators (pure, tested)
  reporter.py              # markdown comparison tables, CI gating
src/api/v1/eval.py         # endpoints: POST /eval/runs, GET /eval/runs/{id}, GET /eval/benchmarks
scripts/eval.py            # CLI: python scripts/eval.py --category A,B --variant engine,baseline_search
```

### 5.2 `BenchmarkHarness` Contract

```python
@dataclass
class EvalRunResult:
    benchmark_id: UUID
    benchmark_slug: str
    engine_variant: Literal["baseline_search","baseline_llm","engine"]
    config_hash: str
    model_versions: dict
    metrics: dict[str, float]      # the 11 metrics
    details: dict                  # per-metric breakdown, artefact IDs
    passed: bool                   # all thresholds met?
    latency_ms: int
    cost_usd: float

class BenchmarkHarness:
    async def run_one(self, benchmark: Benchmark, variant: str) -> EvalRunResult: ...
    async def run_all(self, category_filter: list[str] | None, variants: list[str]) -> list[EvalRunResult]: ...
    def score(self, benchmark: Benchmark, artefacts: Artefacts) -> dict[str, float]: ...
```

**Idempotency:** `eval_runs` rows keyed by `(benchmark_id, engine_variant, config_hash, model_versions_hash)` — re-running same config is idempotent (returns cached row unless `--force`).

### 5.3 Execution Flow

```
1. Load benchmarks from benchmarks/*.json → validate schema
2. For each benchmark × variant:
     a. Create research_jobs + research_runs (for engine) or stub for baselines
     b. Execute variant (engine → full orchestrator; baseline_search → direct connectors; baseline_llm → LLM only)
     c. Collect artefacts: claims, evidence, documents, contradictions, scores
     d. Score via metrics.py (deterministic, no LLM)
     e. Persist eval_runs row with metrics + latency/cost
3. Aggregate: per-category means, overall weighted mean, pass-rate
4. Reporter: markdown table + JSON + CI gate (exit 1 if regression)
5. API: GET /eval/runs/{group_id} returns comparison JSON for UI
```

### 5.4 Determinism & Reproducibility

- **Connector stubbing:** For CI, `StubConnector` with recorded `benchmarks/fixtures/<slug>/*.json` (captured real responses) ensures benchmarks are deterministic without live APIs. Flag `--live` hits real APIs for nightly run.
- **LLM stubbing:** `StubLLMProvider` with per-benchmark canned responses for fast CI; `--live-llm` uses real `litellm` for nightly/weekly.
- **Config snapshot:** `config_hash` + `model_versions` stored per eval run — comparing `engine` across commits is valid only if same hash; otherwise comparison warns.

### 5.5 CI Integration

```yaml
# .github/workflows/eval.yml (Phase 8)
- name: Eval (stubbed connectors, stubbed LLM)
  run: python scripts/eval.py --category A,B,G,H --variants engine,baseline_search,baseline_llm --stubbed
- name: Gate
  run: python tests/evals/reporter.py --check-regression --threshold 0.05
```

- **PR gate:** Runs 4 categories × 3 variants on stubbed data (~5 min). Fails if any metric drops > 5%.
- **Nightly:** Full 8 categories × 3 variants with live APIs/LLM (if keys present), reports to `benchmarks/history/*.json`.
- **Post-V1:** Eval runs populate a dashboard `/eval` in minimal UI.

---

## 6. Ability to Compare Variants (Requirement)

Harness **always** stores all 3 variants together:

- `eval_runs` has `group_id` (eval invocation ID) linking the 3 rows per benchmark.
- API `GET /eval/runs?benchmark=cat_B_acme_seed_2023&group_id=xxx` returns:

```json
{
  "benchmark": "cat_B_acme_seed_2023",
  "group_id": "uuid",
  "results": [
    {"variant":"baseline_search","metrics":{...},"cost_usd":0.01,"latency_ms":1200},
    {"variant":"baseline_llm","metrics":{...},"cost_usd":0.03,"latency_ms":800},
    {"variant":"engine","metrics":{...},"cost_usd":1.4,"latency_ms":8200}
  ],
  "deltas": {
    "engine_vs_baseline_search": {"recall":+0.40,"citation":+0.85},
    "engine_vs_baseline_llm": {"precision":+0.38,"primary_ratio":+0.40}
  }
}
```

UI `/eval` renders this as a comparison table plus sparkline of history.

---

## 7. What V1 Benchmarks Are NOT

- Not a training set — benchmarks are **held-out**; adding new benchmarks after failures is allowed but must be recorded as new slugs (not editing existing ground truth to pass).
- Not live-only — stubbed fixtures make them deterministic; live runs are nightly, not per-PR.
- Not comprehensive to all industries — V1 covers tech/startup/market examples; finance/bio/etc. deferred to post-V1 benchmarks.

---

## 8. Phased Rollout for Evals (see PHASED_PLAN.md)

- **Phase 1:** 4 benchmarks (A, B stubs) + harness skeleton + 2 metrics (recall, citation) — proves plumbing.
- **Phase 4:** All 8 categories defined (24 JSONs), stubbed fixtures captured, 6 metrics.
- **Phase 8:** All 40 benchmarks + 11 metrics + baselines comparison + API + UI dashboard + CI gate.
- **Phase 9:** Regression baseline locked; release report includes eval comparison appendix.

---

## 9. Open Questions

- **Ground truth maintenance:** Confirm nightly live runs are allowed to *update* stubbed fixtures via `scripts/capture_benchmark_fixtures.py` (with human review) — or keep fixtures immutable and treat live drift as eval signal. Proposal: **immutable fixtures; live drift tracked separately**.
- **Cost/latency thresholds:** Confirm engine cost targets (quick $1 / std $2 / deep $5) are gate thresholds or just tracked. Proposal: **tracked, not gated, in V1** — quality gates are primary.
