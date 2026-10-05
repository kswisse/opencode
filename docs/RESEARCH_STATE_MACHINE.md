# Research State Machine — Pipeline, Coverage, and Stopping Criteria

**Version:** V1 Freeze 2026-08-26  
**Package:** `packages/research` (`lifecycle.py`, `orchestrator.py`, `gap_detector.py`, `budget.py`)  
**DB:** `research_jobs.status` + `research_runs.status` + `research_runs.stopping_reason` + `retrieval_runs`/`verification_runs`  
**Principle:** *Explicit states for every transition that can consume budget or require retry. No implicit recursion.*

---

## 1. Full State Machine (V1 — 13 States)

### 1.1 States

```
                              ┌──────────┐
                              │ PENDING  │  job created, not yet planned
                              └────┬─────┘
                                   │ planner.run()
                              ┌────▼─────┐
     ┌────────────────────────┤  PLAN    │  prompt parsing, query expansion,
     │                        │ (planning)│  region/lang sharding, budget estimate
     │                        └────┬─────┘
     │                             │ fan-out queued
     │                        ┌────▼─────┐
     │                        │ DISCOVER │  parallel web/news/social/specialized
     │                        │(discovering) fetches via DiscoveryOrchestrator
     │                        └────┬─────┘
     │                             │ documents normalized
     │                        ┌────▼─────┐
     │                        │ NORMALIZE│  dedup (exact URL, canonical, content_hash,
     │                        │(normalizing) embedding near-duplicate, language detect)
     │                        └────┬─────┘
     │                             │
     │                        ┌────▼─────┐
     │                        │  DEDUP   │  alias collapse candidates (often folded into
     │                        │(deduping*)│  NORMALIZE; explicit state if candidate set > 20)
     │                        └────┬─────┘
     │                             │
     │                        ┌────▼─────┐
     │                        │ QUALIFY  │  entity resolution, candidate set,
     │                        │(qualifying) deterministic qualification rules
     │                        └────┬─────┘
     │                             │
     │              ┌──────────────▼──────────────┐
     │              │      GAP DETECTION          │  coverage matrix per candidate
     │              │    (gap_detecting)          │  FOUND/MISSING/UNCERTAIN/CONTESTED
     │              └──────────────┬──────────────┘
     │                             │ gaps + budget + iteration < max ?
     │              ┌──────────────▼──────────────┐
     │              │      DEEP RESEARCH          │  per-gap gap_queries → fetch
     │              │ (deep_researching)          │  bounded, tier-aware
     │              └──────────────┬──────────────┘
     │                             │ new documents → gap detection again
     │              ┌──────────────▼──────────────┐
     │              │      RECURSIVE              │  iterative loop: GAP ↔ DEEP
     │              │   (recursive)               │  until stopping criteria met
     │              └──────────────┬──────────────┘
     │                             │ stopping criteria met
     │                        ┌────▼─────┐
     │                        │  VERIFY  │  claim verification, contradiction
     │                        │(verifying) detection, adversarial pass (1-3 rounds)
     │                        └────┬─────┘
     │                             │
     │                        ┌────▼─────┐
     │                        │  SCORE   │  deterministic scoring + ranking per claim
     │                        │ (scoring)│  tier-weighted, explainable
     │                        └────┬─────┘
     │                             │
     │                        ┌────▼─────┐
     │                        │ FINALIZE │  report generation (citation-backed markdown
     │                        │(reporting)│  + JSON), cost accounting, partial reason
     │                        └────┬─────┘
     │                             │
     │              ┌──────────────▼──────────────┐
     │              │ COMPLETED | PARTIAL | FAILED │  terminal
     │              └─────────────────────────────┘
```

`* DEDUP is shown separate for clarity; in V1 code it is part of NORMALIZE unless candidate set explosion (>20 candidates) forces a dedicated pass. Included as a named state for observability.*

### 1.2 Transition Table (Authoritative — `lifecycle.py`)

```python
VALID_TRANSITIONS: dict[JobStatus, list[JobStatus]] = {
    JobStatus.PENDING:          [JobStatus.PLANNING, JobStatus.FAILED],
    JobStatus.PLANNING:         [JobStatus.DISCOVERING, JobStatus.FAILED],
    JobStatus.DISCOVERING:      [JobStatus.RETRIEVING, JobStatus.FAILED, JobStatus.PARTIAL],
    JobStatus.RETRIEVING:       [JobStatus.NORMALIZING, JobStatus.FAILED, JobStatus.PARTIAL],
    JobStatus.NORMALIZING:      [JobStatus.QUALIFYING, JobStatus.DEDUP, JobStatus.FAILED, JobStatus.PARTIAL],
    JobStatus.DEDUP:            [JobStatus.QUALIFYING, JobStatus.FAILED],
    JobStatus.QUALIFYING:       [JobStatus.GAP_DETECTING, JobStatus.VERIFYING, JobStatus.FAILED, JobStatus.PARTIAL],
    JobStatus.GAP_DETECTING:    [JobStatus.DEEP_RESEARCHING, JobStatus.VERIFYING, JobStatus.FAILED, JobStatus.PARTIAL],
    JobStatus.DEEP_RESEARCHING: [JobStatus.GAP_DETECTING, JobStatus.RECURSIVE, JobStatus.FAILED, JobStatus.PARTIAL],
    JobStatus.RECURSIVE:        [JobStatus.GAP_DETECTING, JobStatus.VERIFYING, JobStatus.FAILED, JobStatus.PARTIAL],
    JobStatus.VERIFYING:        [JobStatus.SCORING, JobStatus.FAILED],          # scoring is next, even on partial verify
    JobStatus.SCORING:          [JobStatus.REPORTING, JobStatus.FAILED],
    JobStatus.REPORTING:        [JobStatus.COMPLETED, JobStatus.PARTIAL, JobStatus.FAILED],
}
# Loop allowance: GAP_DETECTING ↔ DEEP_RESEARCHING ↔ RECURSIVE is the only cycle.
# Loop bounded by: max_iterations (2-3 by depth), diminishing gain, budget.
```

- **Any-state → FAILED:** only on unrecoverable error (e.g., planner invalid query + retries exhausted). Soft failures produce `PARTIAL` via `REPORTING`.
- **Any early state → PARTIAL:** allowed from `DISCOVERING`, `RETRIEVING`, `NORMALIZING`, `QUALIFYING`, `GAP_DETECTING`, `DEEP_RESEARCHING`, `RECURSIVE` per `can_partial_complete()` — meaning we have enough documents to attempt verify/score/report even if connectors failed.
- **VERIFYING never → PARTIAL directly:** it always continues to SCORING/REPORTING so the user gets a report even if verification is thin — report marks uncovered.

### 1.3 `JobStatus` Enum (V1 Freeze — 13 + 3 terminals)

```python
class JobStatus(str, Enum):
    PENDING = "pending"
    PLANNING = "planning"
    DISCOVERING = "discovering"       # alias for DISCOVER
    RETRIEVING = "retrieving"         # fetch content (often merged with discovering in code)
    NORMALIZING = "normalizing"
    DEDUP = "dedup"
    QUALIFYING = "qualifying"
    GAP_DETECTING = "gap_detecting"
    DEEP_RESEARCHING = "deep_researching"
    RECURSIVE = "recursive"
    VERIFYING = "verifying"
    SCORING = "scoring"
    REPORTING = "reporting"
    COMPLETED = "completed"           # terminal
    PARTIAL = "partial"               # terminal (still has report)
    FAILED = "failed"                 # terminal (no report or minimal)

class PassType(str, Enum):
    DISCOVERY = "discovery"
    DEEP = "deep"
    ADVERSARIAL = "adversarial"
    VERIFICATION = "verification"
```

Existing 12-state `JobStatus` in `evidence-engine` is a subset — new states (`DEDUP`, `QUALIFYING`, `GAP_DETECTING`, `DEEP_RESEARCHING`, `RECURSIVE`, `SCORING`) are additive; old values remain valid (migration not required, just enum extension).

---

## 2. Coverage Dimensions & States

### 2.1 Dimensions (V1 — 10, Configurable via `configs/scoring/coverage.yaml`)

| Dimension | Meaning | Required? (for completion) | Tier Bias |
|-----------|---------|-----------------------------|-----------|
| `identity` | Company/product existence, legal name, domain, headquarters | Yes | Tier 1 (official registry/site) |
| `founders` | Founders/team, roles, backgrounds | Yes | Tier 1 (company site) + tier 2 |
| `product` | What it builds, tech stack, product surface | Yes | Tier 1 (docs/site) + demo |
| `funding` | Rounds, amounts, dates, investors, lead | Depth-dependent | Tier 1 (filings) + Crunchbase snapshot |
| `growth` | Users, revenue, traction metrics, hiring | Depth-dependent | Tier 2 + tier 1 (filings if public) |
| `market` | TAM/SAM, market sizing, vertical | Context | Tier 2–3 (analyst reports) |
| `competition` | Competitors, positioning, differentiation | Context | Tier 3 + tier 4 (social sentiment) |
| `tech` | Architecture, IP, patents, stack details | Depth-dependent | Tier 1 (patents, docs) |
| `customers` | Named customers, case studies, testimonials | Context | Tier 1 (case studies) + tier 3 |
| `risks` | Litigation, regulatory, controversy, red flags | Yes (for trust) | Tier 1 (filings, court) + tier 2 |

`identity/founders/product/risks` are **required dimensions** — a job cannot be `COMPLETED` if any is `MISSING` (must be `FOUND` or at least `UNCERTAIN` with contested disclosure). Other dimensions are required for `deep` depth, advisory for `standard/quick`.

### 2.2 Dimension State

```python
class CoverageState(str, Enum):
    FOUND = "found"           # satisfying evidence meets threshold
    MISSING = "missing"       # no credible evidence
    UNCERTAIN = "uncertain"   # thin/conflicting evidence, low confidence
    CONTESTED = "contested"   # strong contradicting evidence exists
```

**Per-candidate coverage matrix:**

```python
@dataclass
class CoverageMatrix:
    candidate_id: UUID
    candidate_name: str
    dimensions: dict[str, CoverageState]   # dimension → state
    evidence_counts: dict[str, int]        # dimension → # evidences
    confidence_by_dim: dict[str, float]    # dimension → avg confidence of claims in dim
    tier_by_dim: dict[str, int]            # dimension → best tier found
    updated_at: datetime

# Example:
# {
#   "identity": FOUND,   "evidence_counts": {"identity": 5}, "confidence_by_dim": {"identity": 0.91}
#   "founders": FOUND
#   "product":  UNCERTAIN
#   "funding":  MISSING     → gap_query will target funding
#   "growth":   MISSING
#   "market":   CONTESTED
#   ...
# }
```

**How state is computed (deterministic, in `gap_detector.py`):**

For each dimension:

1. Gather claims tagged with that dimension (extractor labels claims with `coverage_dimension` heuristically, or LLM-classified).
2. Count tier-weighted supporting evidences, average `scores.confidence` per dimension.
3. Map to state:

```
if tier_weighted_support >= 1.5 and avg_confidence >= 0.7 and contradicting == 0 → FOUND
elif tier_weighted_support > 0 and contradicting_weighted >= support*0.7      → CONTESTED
elif tier_weighted_support > 0 and avg_confidence < 0.6                       → UNCERTAIN
else                                                                           → MISSING
```

Thresholds are config-driven (`configs/scoring/coverage.yaml`).

### 2.3 Gap Detection Output

```python
@dataclass
class GapReport:
    matrix: CoverageMatrix
    gaps: list[Gap]                 # one per MISSING/UNCERTAIN/CONTESTED dimension
    overall_coverage: float         # 0-1, FOUND/(total required)
    suggested_queries: list[GapQuery]

@dataclass
class Gap:
    dimension: str
    state: CoverageState
    reason: str                     # "No tier 1-2 evidence for funding"
    priority: Literal["high","medium","low"]  # required dims = high
```

Gap detection is **deterministic** (no LLM) — LLM is used only to *rephrase* gap queries politely, not to decide gaps.

---

## 3. Stopping Criteria (5 Conditions — Any Terminal)

The recursive loop `GAP_DETECTING ↔ DEEP_RESEARCHING` terminates when **any** of:

### 3.1 Coverage Complete

- All required dimensions are `FOUND` or `CONTESTED` with disclosure (i.e., user is told about the conflict).
- For `deep` depth, additionally: non-required dimensions are not `MISSING` (they may be `UNCERTAIN`/`FOUND`).
- Recorded as `stopping_reason="coverage_complete"`.

### 3.2 Diminishing Gain

- New iteration added `< 5%` new claims vs prior iteration AND no dimension changed state (MISSING→FOUND).
- Measured as `gain = new_claims / total_claims_prior`. Threshold configurable `diminishing_gain_threshold: 0.05` in `budget.yaml`.
- Prevents endless fetch for marginal evidence.
- `stopping_reason="diminishing_gain"`.

### 3.3 Budget Exhausted

- **Soft limit:** `spent_usd >= soft_usd` → finish in-flight deep worker, **no new iteration**, continue to VERIFY. Marked `partial_reason="budget_soft"` if overall job later is partial.
- **Hard limit:** `spent_usd >= hard_usd` → abort new fetches/LLM calls *immediately*, proceed to VERIFY with whatever is in DB. `stopping_reason="budget_hard"`.
- Applies to both `llm_cost_usd` and `fetch_count` (whichever hits first).

### 3.4 Max Iterations

- `quick: 1`, `standard: 2`, `deep: 3` (config `depth_budgets.max_iterations`).
- Iteration count = `research_runs.iteration_count` (incremented each DEEP_RESEARCH → GAP cycle).
- `stopping_reason="max_iterations"`.

### 3.5 Confidence Threshold

- If `avg(scores.confidence for required dimensions) >= 0.85` and at least two independent tier 1-2 sources per required dimension → early stop (already trustworthy).
- `stopping_reason="confidence_threshold"`.

**Orchestrator check (pseudocode):**

```python
async def should_continue_gap_loop(matrix: CoverageMatrix, run: ResearchRun, budget: BudgetSnapshot) -> tuple[bool, str]:
    if matrix.overall_coverage >= 1.0:
        return False, "coverage_complete"
    if budget.hard_hit:
        return False, "budget_hard"
    if run.iteration_count >= max_iterations[run.depth]:
        return False, "max_iterations"
    if matrix.gain < diminishing_threshold:
        return False, "diminishing_gain"
    if matrix.avg_confidence_required >= 0.85 and matrix.min_independent_sources >= 2:
        return False, "confidence_threshold"
    if budget.soft_hit:
        return False, "budget_soft"
    return True, "continue"
```

All five are logged in `research_runs.stopping_reason` for audit and UI display.

---

## 4. Budget Controls (Hard vs Soft)

### 4.1 Budget Snapshot & Enforcement (see also AGENT_CONTRACTS.md §6)

```yaml
# configs/scoring/budget.yaml (frozen defaults — tunable, but require PR)
depth_budgets:
  quick:
    soft_usd: 1.0
    hard_usd: 1.2
    max_shards: 6
    max_iterations: 1
    max_claims: 50
  standard:
    soft_usd: 2.0
    hard_usd: 2.4
    max_shards: 12
    max_iterations: 2
    max_claims: 150
  deep:
    soft_usd: 5.0
    hard_usd: 6.0
    max_shards: 16
    max_iterations: 3
    max_claims: 400
per_claim_llm_cap_usd: 0.02
per_search_cost_estimate_usd: 0.005
fetch_cost_estimate_usd: 0.001
```

- **Soft:** Degrade gracefully — planner prunes shards, discovery halves `max_results`, entity resolver skips tail docs, deep research skips low-priority gaps, report uses template if hard.
- **Hard:** Immediate stop on new LLM/fetch; still verify/score/report with collected evidence; terminal is `PARTIAL` with `partial_reason="budget_hard"`.
- **Accounting:** Every agent calls `BudgetController.record_llm(cost)` and `record_fetch()` synchronously; `research_runs.cost_usd` is sum. Cost is `LLMProvider.estimate_cost` plus `fetch_count * fetch_cost_estimate`.

### 4.2 Observability

- UI shows live budget bar: `spent / soft (hard)` + iteration count + coverage ring.
- Prometheus: `budget_spent_usd{job_id, run_id}`, `budget_iterations`, `coverage_ratio`.
- `research_runs.metadata.budget_trace`: list of `{phase, spent, tokens, fetches, timestamp}` for post-mortem.

---

## 5. Deterministic Behaviors (No LLM Required for Control Flow)

- **State transitions:** Deterministic table (`VALID_TRANSITIONS`) — LLM never decides next state; `JobLifecycle.transition()` validates.
- **Gap detection:** Deterministic matrix from claim counts/tier weights — LLM only rewrites query phrasing.
- **Stopping criteria:** Arithmetic on counts/confidences/cost — no LLM.
- **Scoring & ranking:** Deterministic math — LLM only polishes `verification_reasoning` if budget permits and never changes status.

This guarantees **cost predictability** and **reproducibility**: re-running same job with same `config_hash` and `model_versions` but with stubbed sources yields identical state path (modulo source live content).

---

## 6. Failure & Idempotency Inside State Machine

- **Retry inside a state:** `arq` retries the worker task (idempotency key). DB state unchanged until task succeeds; then single `lifecycle.transition()` call advances.
- **Partial inside a state:** Worker may return `partial` (e.g., discovery with 60% connectors). Orchestrator advances anyway if `can_partial_complete(state)` — downstream phases adapt (e.g., verify with fewer documents, report discloses gaps).
- **Crash mid-state:** `research_runs.status` remains at crash state. On recovery, API `POST /research/{id}/retry` re-enqueues the same phase task with same idempotency key — safe to retry.
- **No lost updates:** `research_jobs.status` and `research_runs.status` updated only via `lifecycle.transition()` with row-level `SELECT … FOR UPDATE` inside transaction.

---

## 7. Relation to Other Docs

- **DATA_MODEL.md:** `research_runs.iteration_count`, `stopping_reason`, `coverage_snapshot` columns.
- **AGENT_CONTRACTS.md:** Each agent's `next_phase` hint must correspond to valid transition; orchestrator is tie-breaker.
- **EVIDENCE_MODEL.md:** Coverage dimensions derived from `claims.coverage_dimension` labeling + `scores` per dimension.

---

## 8. Open Questions

- **Threshold for coverage_complete:** Confirm 100% required dimensions must be `FOUND` vs allowing `UNCERTAIN` with explicit disclosure to count as "complete" for `PARTIAL→COMPLETED` upgrade. Freeze proposal: `FOUND` or `CONTESTED` only; `UNCERTAIN` still requires disclosure but stays `PARTIAL`.
- **Confidence threshold early-stop value:** 0.85 average — confirm not too high (0.80 might be more pragmatic for quick depth).
