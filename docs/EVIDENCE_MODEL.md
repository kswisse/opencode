# Evidence Model — CLAIM → EVIDENCE → SOURCE → DOCUMENT

**Version:** V1 Freeze 2026-08-26  
**Packages:** `packages/evidence` (or `claims` + `evidence` + `provenance` + `graph`)  
**DB:** `claims`, `evidence`, `claim_evidence`, `claim_sources`, `documents`, `sources`, `source_lineages`  
**Principle:** *Every claim must be traceable to character-level spans in documents, each span to a source with tier, each source to a fetched document. No orphan claims.*

---

## 1. The Core Chain (Evidence-First)

```
                ┌──────────────────────────────────────────────────────────┐
                │                    RESEARCH JOB (query)                  │
                └────────────────────────────┬─────────────────────────────┘
                                             │
                          ┌──────────────────▼──────────────────┐
                          │               CLAIM                  │
                          │  normalized_text + S/P/O triple +    │
                          │  extraction_confidence + status      │
                          │  verification_status ∈ {verified,    │
                          │   supported, contested, unverified,  │
                          │   refuted}  + confidence 0-1         │
                          └──────────────┬───────────────────────┘
                                         │  * ──► claim_evidence (join, role+confidence)
                                         │
                          ┌──────────────▼───────────────────────┐
                          │              EVIDENCE                 │
                          │  snippet + char_start/end in         │
                          │  document.content + relevance_score  │
                          │  evidence_type {supporting,          │
                          │   contradicting, context, primary}   │
                          └──────────────┬───────────────────────┘
                                         │  evidence.document_id
                                         │
                          ┌──────────────▼───────────────────────┐
                          │              DOCUMENT                 │
                          │  url, canonical_url, title, author,  │
                          │  publisher, published_at, language,  │
                          │  region, content_hash, embedding     │
                          └──────────────┬───────────────────────┘
                                         │  document.source_id
                                         │
                          ┌──────────────▼───────────────────────┐
                          │               SOURCE                  │
                          │  registry id, tier 1-5, authority,   │
                          │  coverage, access_method             │
                          └──────────────────────────────────────┘

     Additional:  claim_sources  (claim ↔ source denormalized for fast scoring)
                  source_lineages (document ↔ document provenance graph)
                  contradictions (claim ↔ claim)
                  scores (per-claim scoring snapshot)
```

**Invariant:** `claim` never exists without at least one `evidence` row linking it to a `document`. Extraction that cannot anchor a snippet is discarded (or stored with `extraction_confidence < 0.4` and never surfaces in report).

---

## 2. Table Definitions (Authoritative — See DATA_MODEL.md DDL)

### 2.1 `claims`

| Column | Type | Notes |
|--------|------|-------|
| `id` | UUID PK | |
| `job_id` | UUID FK research_jobs | |
| `run_id` | UUID FK research_runs | added 002 |
| `document_id` | UUID FK documents | primary extraction doc (first evidence) |
| `normalized_text` | TEXT | canonical form of assertion |
| `subject` | VARCHAR(500) | SPO triple subject (e.g., "Acme AI") |
| `predicate` | VARCHAR(500) | (e.g., "raised") |
| `object` | VARCHAR(500) | (e.g., "$3M seed") |
| `event_time` | TIMESTAMPTZ | temporal anchor (e.g., 2023-06-15) |
| `extraction_confidence` | FLOAT 0-1 | LLM self-confidence on extraction |
| `verification_status` | VARCHAR(50) | V1 freeze enum below |
| `verification_reasoning` | TEXT | deterministically generated or LLM-assisted |
| `embedding` | VECTOR(1536) | for dedup/similarity |

**Indexes:** `job_id`, `run_id`, `document_id`, `verification_status`, `embedding HNSW (deferred)`.

### 2.2 `evidence`

| Column | Type | Notes |
|--------|------|-------|
| `id` | UUID PK | |
| `job_id` / `run_id` | UUID FK | |
| `document_id` | UUID FK documents | |
| `source_id` | VARCHAR FK sources | tier snapshot |
| `snippet` | TEXT | 200-500 char span, verbatim or lightly normalized |
| `char_start` | INTEGER nullable | offset in `documents.content` |
| `char_end` | INTEGER nullable | exclusive |
| `relevance_score` | NUMERIC 0-1 | retriever/LLM relevance vs claim |
| `evidence_type` | VARCHAR | `supporting | contradicting | context | primary` |
| `metadata` | JSONB | extraction trace, quote confidence |
| `created_at` | TIMESTAMPTZ | |

**Indexes:** `job_id`, `run_id`, `document_id`, `source_id`, `evidence_type`.

**Evidence types:**

- `supporting` — snippet directly asserts claim.
- `contradicting` — snippet asserts negation or incompatible value (e.g., different amount/date).
- `context` — relevant but neither supporting nor contradicting (used for scoring staleness/temporal consistency).
- `primary` — snippet is from tier-1 primary source (filing, official domain) — `is_primary` flag in `claim_sources` derived from this.

**Snippets are not bare URLs.** Each evidence row must contain a snippet; bare URL references without char-anchored span are stored as `metadata.citation_url` but not counted as evidence for verification.

### 2.3 `claim_evidence` (join, with role)

| Column | Notes |
|--------|-------|
| `claim_id, evidence_id` | composite PK |
| `role` | `supporting | contradicting | context` (mirrors evidence_type but allows override per-claim) |
| `confidence` | per-edge confidence 0-1 (source quality × snippet quality) |

### 2.4 `claim_sources` (denormalized for scoring)

| Column | Notes |
|--------|-------|
| `claim_id, source_id` | composite PK |
| `evidence_count` | how many evidences from this source support claim |
| `is_primary` | true if any evidence from source is `primary` |
| `tier` | snapshot of `sources.tier` at job time |

### 2.5 `documents` (see DATA_MODEL.md)

Key provenance columns: `source_id`, `url`, `canonical_url`, `content_hash`, `is_duplicate_of`, `language`, `region`, `embedding`.

### 2.6 `source_lineages` (provenance graph — see §4)

### 2.7 `scores` (deterministic snapshot)

Per-claim scoring snapshot with `final_score`, `confidence`, `factors` JSON, `rank`.

---

## 3. Claim Model (Extraction → Normalization → Verification)

### 3.1 Claim Extraction (via LLM, anchored)

**Extractor contract (`packages/evidence/extractor.py` or `claims/extractor.py`):**

```python
class ClaimExtractor:
    async def extract(self, document: Document, job_id: UUID, run_id: UUID) -> list[ClaimCandidate]:
        # calls LLMProvider.structured_generate with schema:
        # {claims: [{normalized_text, subject, predicate, object, event_time, snippet, char_start, char_end, confidence}]}
        # temperature 0.2, EXTRACTION_MODEL

@dataclass
class ClaimCandidate:
    normalized_text: str
    subject: str | None
    predicate: str | None
    object: str | None
    event_time: datetime | None
    snippet: str             # must be substring of document.content (validated)
    char_start: int | None
    char_end: int | None
    extraction_confidence: float
    source_id: str           # inherited from document.source_id
```

**Validations before insert:**

1. `snippet` must be substring of `document.content` (fuzzy match ≥ 0.92 if char offsets missing). If not found → discard candidate or mark `confidence -= 0.3`.
2. `char_start/end` if provided must align with `content` slice — if mismatch, recompute via `content.find(snippet)`.
3. `normalized_text` dedup per run: `cosine(claim.embedding, existing.embedding) < 0.12` → merge into canonical claim, keep max `extraction_confidence`, append additional `evidence` row (no duplicate claim row).
4. `extraction_confidence < 0.4` → still inserted but flagged `verification_status=unverified` and excluded from `verified/supported` sets unless corroborated.

### 3.2 Normalization Rules

- Trim, collapse whitespace, strip citations like `[1]`.
- Normalize numbers: `$3M` → `$3,000,000` in `object` canonical but preserve original `normalized_text`.
- Dates: ISO-8601 in `event_time`; relative dates resolved by LLM with `document.published_at` as anchor.
- Subjects: company names normalized per `entities.normalized_name` (e.g., "Acme AI, Inc." → "acme ai").

### 3.3 Verification States (V1 Freeze — 5 states)

Existing 8-state (`verified/probably_true/.../outdated`) is mapped to **V1 5-state** (simpler, less hallucinated calibration):

| V1 Status | Meaning | Condition (Deterministic Engine) | Confidence Range | Report Badge |
|-----------|---------|-----------------------------------|------------------|--------------|
| **`verified`** | Strongly supported, no credible contradicting evidence | `supporting ≥ 2` independent tier-weighted evidences, `contradicting == 0`, at least one tier 1-2 | 0.80–1.0 | ✅ Verified |
| **`supported`** | Supported but lighter (single source or weaker corroboration) | `supporting == 1` (tier 1-3) OR `supporting ≥ 2` with one weak tier | 0.60–0.79 | ✓ Supported |
| **`contested`** | Both supporting and contradicting evidence of comparable weight | `supporting > 0 && contradicting > 0 && |tier_weighted_support - tier_weighted_contra| < threshold` | 0.35–0.59 | ⚠️ Contested |
| **`refuted`** | Contradicting evidence outweighs supporting | `contradicting` tier-weighted sum > `supporting` by threshold | 0.10–0.34 | ✗ Refuted |
| **`unverified`** | Insufficient evidence (no supporting, or only tier 4-5 weak) | `supporting == 0` or only tier 5 | 0.0–0.29 | ○ Unverified |

**Mapping from legacy (transition compatibility):**

```
verified       → verified
probably_true  → supported
partially_supported → supported (if at least 1 strong) else contested
contested      → contested
probably_false → refuted
false          → refuted
outdated       → refuted (with staleness penalty in factors)
unverified     → unverified
```

- `verification_reasoning` is a templated string: `"{n} supporting (tiers {…}), {m} contradicting, independence={score}, primary={bool}"` — deterministic, not LLM free-text (LLM may append one sentence polish in report phase only).
- Confidence factors (see `verification/engine.py` + `confidence/scorer.py`): `evidence_quality`, `source_independence`, `primary_evidence`, `temporal_consistency`, `corroboration`, `contradiction_penalty`, `provenance_uncertainty`, `staleness_penalty` → blended into final score 0-1 (explainable).

**Why 5 not 8:** Fewer bins → more stable eval metrics (claim-level F1), less LLM calibration drift. The confidence float provides nuance.

### 3.4 Claim Lifecycle

```
extract (unverified, 0.2) ──▶ verify (deterministic engine sets status+confidence)
                              │
                              ├─▶ contradict (ContradictionEngine pairs contested claims)
                              │
                              ├─▶ rescore (Scorer sets scores.final_score + rank)
                              │
                              └─▶ report (surface only supported+verified+contested in summary; unverified/refuted in appendix)
```

Claims are never hard-deleted; status transitions appended via updated row + `verification_runs` audit.

---

## 4. Provenance & Lineage

### 4.1 Source Lineage Graph (`source_lineages`)

Captures **how documents relate** — critical for `source_independence`.

```python
class LineageRelationship(str, Enum):
    DERIVED_FROM = "derived_from"           # B is primary filing, A summarizes it
    CITES = "cites"                         # A cites B
    QUOTES = "quotes"                       # A quotes B verbatim
    REPOSTS = "reposts"                     # A reposts B (syndication)
    COPIES = "copies"                       # A copies B largely (copy-paste)
    SUMMARIZES = "summarizes"
    INDEPENDENTLY_REPORTS = "independently_reports"  # A and B arrived independently at same fact
```

**Population:**

- Heuristic pass (deterministic): `content_hash` near match, `canonical_url` share, `title` edit distance + timestamp order → `COPIES/REPOSTS` with confidence.
- Embedding pass: `cosine(docA.embedding, docB.embedding) > 0.92` + published-at proximity → `COPIES` or `SUMMARIZES`.
- LLM pass (optional, budget-controlled): for high-stakes claims (tier 1 vs tier 1 conflict), call `EXTRACTION_MODEL` to classify relationship.

**Independence scoring (`provenance/independence.py`):**

```python
def independence_score(claim: Claim) -> float:
    # For each pair of evidences supporting claim:
    #   if lineage relationship is COPIES/REPOSTS/CITES/QUOTES → penalty
    #   if INDEPENDENTLY_REPORTS or no lineage edge → bonus
    #   plus domain diversity (distinct registrable domains)
    #   plus tier diversity (more tiers → higher independence)
    # Return 0–1 (1 = fully independent sources)
```

Scores below 0.4 → `weaken(- "Sources may share common origin")` in confidence explanation.

### 4.2 Temporal Consistency & Staleness

- Each evidence carries `document.published_at`. Claim's `event_time` compared → `staleness_penalty` if evidence is >12 months older than event, or if newer contradicting evidence exists.
- `temporal_consistency` factor is 1.0 if all supporting evidences cluster within a reasonable window, lower if contradictions are recent while support is old.

---

## 5. Citation Extraction & Anchoring

### 5.1 How Citations Are Anchored

**Not a bare URL list.** Each citation is an `evidence` row with:

- `document_id` + `char_start/end` + `snippet` (verbatim slice)
- `source_id` + tier badge
- `relevance_score` (how well snippet supports claim)

**Character offsets:**

1. Extractor LLM emits `snippet` + approximate `char_start/end`. Validated by `content.find(snippet)` (trim-normalized). If fuzzy (< 0.92 match) → discard offsets, keep snippet-only (still verifiable via search within doc).
2. Normalizer recomputes canonical offsets if mismatch > 5 chars.
3. UI highlights `content[char_start:char_end]` when user clicks citation.

**Evidence span policy:**

- Min snippet length 50 chars, max 500 chars (prevents trivial quotes).
- Snippet must be contiguous in `document.content`; no stitching.
- Quoted text preserved verbatim; ellipses `…` allowed only if char offsets bookend it.

### 5.2 Evidence Types & Primary Evidence

- `primary` = snippet from tier-1 source that is the original issuance (filing, official site). UI shows `†`dagger.
- `supporting` / `contradicting` resolved per-claim via `claim_evidence.role` — same evidence can be `supporting` for Claim A but `context` for Claim B.
- `primary_source_available` boolean per claim (any evidence is `primary`) influences confidence (+0.1 if true).

---

## 6. Contradictions

### 6.1 Contradiction Representation (`contradictions` table)

| Column | Notes |
|--------|-------|
| `id` | UUID PK |
| `job_id`, `run_id` | FKs |
| `claim_a_id`, `claim_b_id` | FK claims (A != B) |
| `contradiction_type` | `direct` (A negates B) / `temporal` (different dates) / `numeric` (different amounts) / `attribution` (different actor) |
| `severity` | `low/medium/high/critical` (critical = tier 1 vs tier 1 numeric conflict) |
| `description` | deterministic: "Claim A ($3M seed on 2023-06-15 via SEC) vs Claim B ($5M seed on 2023-08 via TechCrunch)" |
| `resolution` | `unresolved | a_prevails | b_prevails | both_contested | needs_human` |
| `metadata` | {delta, temporal_gap, tier_pair} |

**Detection (`verification/contradiction.py`):**

- Pairwise over claims of same candidate/dimension where `cosine(embedding) > 0.85` and either numeric delta > 10% or temporal mismatch > 7 days → candidate.
- Severity: `critical` if both claims are `verified/supported` + tier 1-2 + large numeric delta; `high` if tier mix; `medium/low` otherwise.
- No LLM in hot path for detection; LLM pass optional for description polish.

**Resolution:**

- Deterministic: higher tier-weighted support prevails (`a_prevails`/`b_prevails`); if equal → `both_contested`.
- UI surfaces contradictions in report callout with evidence badges and `needs_human` for `critical` unresolved.

---

## 7. Confidence & Scoring (Link to Scoring Engine)

- Per-claim `scores` row stores `final_score` 0-1, `confidence` (same as final for V1), factor breakdown (`evidence_quality`, `source_independence`, `primary_evidence`, `temporal_consistency`, `corroboration`, `contradiction_penalty`, `provenance_uncertainty`, `staleness_penalty`), and `explanation.supporting/weakening` arrays.
- `final_score` blending (see `confidence/scorer.py`): `(sum positive factors - penalties + 1)/2` bounded 0-1, plus tier weighting. Deterministic math — auditable, reproducible given same evidence set.

---

## 8. Provenance Invariants (Hard)

1. **No orphan claim:** `claims.document_id` not null + at least one `claim_evidence` row exists at insert time.
2. **Evidence must anchor:** `evidence.snippet` not empty; `document_id` valid; `source_id` matches `documents.source_id`.
3. **Source lineage acyclicity:** `source_lineages` graph may have cycles via syndication, but `independence_score` handles it via visited-set; report collapses cycles.
4. **Embedding optional but recommended:** Claims without embedding still verifiable but skipped for near-duplicate dedup.
5. **Auditability:** Every mutation that touches `claims.verification_status` also writes `verification_runs` row; report generation writes `reports` row. Full chain reconstructable from run_id.

---

## 9. Relation to Agent Contracts

- **PLANNER:** no evidence yet (seeds `research_queries`).
- **DISCOVERY / SOCIAL / DEEP RESEARCH:** write `documents` → `evidence` (per-document snippet extraction) → `claims` (if claim extraction enabled per doc).
- **ENTITY RESOLVER:** links claims to `entities` via `graph_nodes` with `edge_type=mentions`.
- **VERIFICATION/SYNTHESIS:** reads `claim_evidence` + `claim_sources` + `source_lineages` to produce `verification_status` + `contradictions` + `scores` + report markdown with citation anchors.

---

## 10. Open Questions

- **Char offset precision:** V1 allows nullable offsets (Phase 1 snippet-only) — confirm timeline to make offsets non-nullable (Phase 3 after normalizer hardening).
- **Evidence per document density:** Cap at N evidences per document (default 10) to prevent LLM explosion on long docs — confirm cap or leave uncapped with budget gate.
- **Outdated mapping:** `outdated` legacy status maps to `refuted` + staleness penalty — confirm no separate `outdated` display needed in report.
