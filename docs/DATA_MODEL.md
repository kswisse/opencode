# V1 Data Model — PostgreSQL + pgvector

**Version:** V1 Freeze 2026-08-26  
**DB:** PostgreSQL 16+ + `pgvector`  
**ORM:** SQLAlchemy 2.0 async (`asyncpg`)  
**Migrations:** Alembic (single lineage, append-only)  
**Principles:** Evidence-first, provenance-preserving, deterministically queryable, embed-friendly

---

## 1. ER Overview (Text)

```
research_jobs 1──* research_runs 1──* research_queries
     │                    │
     │                    ├─* retrieval_runs (per connector per run)
     │                    ├─* verification_runs (per round)
     │                    └─* scores (per claim per run)
     │
     *──* documents ──* evidence ──* claim_evidence *──* claims ──* claim_sources *── sources
          │                │                                          │              │
          │                │                                          │              └─* source_lineages (docA→docB)
          │                └── citation spans (evidence char offsets) │
          │                                                          *── contradictions (claimA↔claimB)
          │
          *──* social_posts (polymorphic to documents, optional) ── social_authors

     *──* entities ──* entity_aliases
     *──* companies ──* funding_rounds ── investors
              │──* people (founders/employees) ── investors
              └── markets

     benchmarks 1──* eval_runs (records config_hash, model_versions, metrics)
```

**Key invariants:**

- `research_jobs` = user intent (immutable after creation except status/report). One job may have many `research_runs` (retries or deeper passes).
- `research_runs` = execution attempt (status, started/completed, cost, token counts, partial reason). All documents/claims/evidence are scoped to a `run_id` (not just `job_id`) for reproducibility.
- `research_queries` = expanded queries × regions × languages — one row per shard.
- `documents` = normalized fetched content with embedding + dedup linkage.
- `evidence` = **char-range span** inside a document that supports/mentions a claim (the citation anchor).
- `claims` = normalized assertion + triple + embedding, scoped to a run.
- `claim_sources` / `claim_evidence` = joins that materialize CLAIM→EVIDENCE→SOURCE→DOCUMENT.
- `entities` / `entity_aliases` = resolved canonical entity with aliases (company/person).
- `scores` = deterministic score snapshot per claim per run (auditable).
- `benchmarks` / `eval_runs` = evaluation datasets and comparative results.

---

## 2. Full Schema DDL (Authoritative for Alembic)

> Existing `001` tables are marked ✅. All new tables are 002+ migrations. Existing tables gain columns via 002+ (additive, nullable/defaulted first).

### 2.1 Extensions

```sql
CREATE EXTENSION IF NOT EXISTS vector;   -- pgvector
CREATE EXTENSION IF NOT EXISTS pg_trgm;  -- for alias trigram search
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
```

### 2.2 Research Jobs / Runs / Queries

```sql
-- 001 exists; 002 adds columns. Shown as final V1 target.
CREATE TABLE research_jobs (
    id                UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    query             TEXT NOT NULL,                      -- raw user prompt
    normalized_query  TEXT,                               -- after prompt parsing
    status            VARCHAR(50) NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending','planning','discovering','retrieving','normalizing',
                          'qualifying','deep_researching','gap_detecting','recursive',
                          'verifying','scoring','reporting','completed','partial','failed')),
    current_pass      VARCHAR(50) NOT NULL DEFAULT 'discovery'
        CHECK (current_pass IN ('discovery','deep','verification','adversarial')),
    depth             VARCHAR(50) NOT NULL DEFAULT 'standard' CHECK (depth IN ('quick','standard','deep')),
    source_strategy   VARCHAR(50) NOT NULL DEFAULT 'broad',
    time_range_start  TIMESTAMPTZ,
    time_range_end    TIMESTAMPTZ,
    languages         JSONB,                              -- ["en","vi","ru"] + per-region hints
    regions           JSONB,                              -- ["us","eu","vn"]  -- 002: new
    depth_config      JSONB,                              -- budget caps, max_queries, etc. -- 002
    -- provenance of the job itself
    planner_plan      JSONB,                              -- expanded queries, entities heuristically extracted -- 002
    config_hash       VARCHAR(64),                        -- sha256 of configs snapshot
    model_versions    JSONB,                              -- {llm_provider, models per role} -- 002
    -- timestamps / retry
    created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    started_at        TIMESTAMPTZ,
    completed_at      TIMESTAMPTZ,
    retry_count       INTEGER NOT NULL DEFAULT 0,
    max_retries       INTEGER NOT NULL DEFAULT 3,
    last_error        TEXT,
    -- aggregated counters (denormalized for fast UI; source of truth is child tables)
    total_documents        INTEGER NOT NULL DEFAULT 0,
    retrieved_documents    INTEGER NOT NULL DEFAULT 0,
    claims_extracted       INTEGER NOT NULL DEFAULT 0,
    contradictions_found   INTEGER NOT NULL DEFAULT 0,
    connector_statuses     JSONB,                          -- deprecated after 003, kept for compat
    report            TEXT,                               -- markdown (large reports move to reports table in 004)
    report_json       JSONB,                              -- structured report -- 003
    -- budget (added 003)
    budget_soft_usd   NUMERIC(10,4),
    budget_hard_usd   NUMERIC(10,4),
    cost_usd          NUMERIC(10,4) NOT NULL DEFAULT 0,
    cost_tokens       INTEGER NOT NULL DEFAULT 0,
    fetch_count       INTEGER NOT NULL DEFAULT 0,
    partial_reason    VARCHAR(100) -- 'budget_soft' | 'budget_hard' | 'coverage_stalled' | 'max_iterations' | null
);
CREATE INDEX ix_research_jobs_status ON research_jobs(status);
CREATE INDEX ix_research_jobs_created_at ON research_jobs(created_at);
CREATE INDEX ix_research_jobs_partial_reason ON research_jobs(partial_reason) WHERE partial_reason IS NOT NULL;

-- 002: new — one execution attempt of a job (enables retries + deep passes + eval reproducibility)
CREATE TABLE research_runs (
    id                UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_id            UUID NOT NULL REFERENCES research_jobs(id) ON DELETE CASCADE,
    run_number        INTEGER NOT NULL DEFAULT 1,
    status            VARCHAR(50) NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending','planning','discovering','retrieving','normalizing',
                          'qualifying','deep_researching','gap_detecting','recursive',
                          'verifying','scoring','reporting','completed','partial','failed')),
    -- budget for this run
    budget_soft_usd   NUMERIC(10,4),
    budget_hard_usd   NUMERIC(10,4),
    cost_usd          NUMERIC(10,4) NOT NULL DEFAULT 0,
    prompt_tokens     INTEGER NOT NULL DEFAULT 0,
    completion_tokens INTEGER NOT NULL DEFAULT 0,
    fetch_count       INTEGER NOT NULL DEFAULT 0,
    -- stopping criteria trace
    stopping_reason   VARCHAR(100), -- 'coverage_complete' | 'diminishing_gain' | 'budget_soft' | 'budget_hard' | 'max_iterations' | 'confidence_threshold' | null
    coverage_snapshot JSONB,        -- {identity:FOUND, founders:MISSING, ...}
    iteration_count   INTEGER NOT NULL DEFAULT 0,
    started_at        TIMESTAMPTZ,
    completed_at      TIMESTAMPTZ,
    error             TEXT,
    metadata          JSONB,        -- connector_health, timing breakdown
    created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (job_id, run_number)
);
CREATE INDEX ix_research_runs_job_id ON research_runs(job_id);
CREATE INDEX ix_research_runs_status ON research_runs(status);

-- 002: new — expanded query shards
CREATE TABLE research_queries (
    id                UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_id            UUID NOT NULL REFERENCES research_jobs(id) ON DELETE CASCADE,
    run_id            UUID REFERENCES research_runs(id) ON DELETE CASCADE, -- null for planning-phase queries
    raw_query         TEXT NOT NULL,
    expanded_query    TEXT NOT NULL,
    region            VARCHAR(20) NOT NULL DEFAULT 'us',
    language          VARCHAR(10) NOT NULL DEFAULT 'en',
    purpose           VARCHAR(30) NOT NULL DEFAULT 'discovery'
        CHECK (purpose IN ('discovery','verification','context','gap_fill','recursive')),
    rank              INTEGER NOT NULL DEFAULT 0, -- planner ranking
    metadata          JSONB,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX ix_research_queries_job_id ON research_queries(job_id);
CREATE INDEX ix_research_queries_run_id ON research_queries(run_id);
CREATE INDEX ix_research_queries_purpose ON research_queries(purpose);
CREATE INDEX ix_research_queries_region_lang ON research_queries(region, language);
```

### 2.3 Sources Registry & Documents

```sql
-- 002: new — source registry (cache of configs/sources/*.yaml, queryable)
CREATE TABLE sources (
    id                VARCHAR(255) PRIMARY KEY,  -- registry key e.g., "sec_edgar", "tavily", "reddit_public"
    display_name      TEXT NOT NULL,
    tier              SMALLINT NOT NULL CHECK (tier BETWEEN 1 AND 5),
    authority_score   NUMERIC(4,3) NOT NULL DEFAULT 0.5 CHECK (authority_score BETWEEN 0 AND 1),
    coverage          JSONB,                     -- ["us","eu"] or ["tech","finance"]
    access_method     VARCHAR(20) NOT NULL CHECK (access_method IN ('api','rss','scrape','playwright','snapshot')),
    search_url        TEXT,
    fetch_url_template TEXT,
    rate_limit_per_min INTEGER,
    timeout_ms        INTEGER NOT NULL DEFAULT 30000,
    max_results       INTEGER NOT NULL DEFAULT 20,
    robots_respected  BOOLEAN NOT NULL DEFAULT true,
    requires_key      BOOLEAN NOT NULL DEFAULT false,
    is_active         BOOLEAN NOT NULL DEFAULT true,
    health_status     VARCHAR(20) NOT NULL DEFAULT 'unknown' CHECK (health_status IN ('unknown','healthy','degraded','down')),
    last_health_check TIMESTAMPTZ,
    metadata          JSONB,                    -- tier rationale, license notes
    created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX ix_sources_tier ON sources(tier);
CREATE INDEX ix_sources_is_active ON sources(is_active) WHERE is_active;

-- 001 exists; final V1 view (adds region, citation_spans link via evidence instead)
CREATE TABLE documents (
    id                UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_id            UUID NOT NULL REFERENCES research_jobs(id) ON DELETE CASCADE,
    run_id            UUID REFERENCES research_runs(id) ON DELETE CASCADE, -- 002: added
    source_id         VARCHAR(255) NOT NULL REFERENCES sources(id),
    url               TEXT NOT NULL,
    canonical_url     TEXT,
    title             TEXT,
    author            VARCHAR(500),
    publisher         VARCHAR(500),
    published_at      TIMESTAMPTZ,
    retrieved_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    language          VARCHAR(10) NOT NULL DEFAULT 'en',
    region            VARCHAR(20) NOT NULL DEFAULT 'us', -- 002
    content           TEXT NOT NULL,
    content_hash      VARCHAR(64), -- sha256 hex
    mime_type         VARCHAR(100) NOT NULL DEFAULT 'text/html',
    is_duplicate_of   UUID REFERENCES documents(id),
    dedup_reason      VARCHAR(100), -- 'exact_url' | 'canonical_url' | 'content_hash' | 'near_duplicate'
    metadata          JSONB,
    embedding         VECTOR(1536), -- pgvector
    -- 003: provenance helpers
    fetch_duration_ms INTEGER,
    http_status       SMALLINT,
    CONSTRAINT uq_documents_job_url UNIQUE (job_id, url)
);
CREATE INDEX ix_documents_job_id ON documents(job_id);
CREATE INDEX ix_documents_run_id ON documents(run_id);
CREATE INDEX ix_documents_content_hash ON documents(content_hash);
CREATE INDEX ix_documents_canonical_url ON documents(canonical_url);
CREATE INDEX ix_documents_source_id ON documents(source_id);
CREATE INDEX ix_documents_published_at ON documents(published_at);
-- HNSW for cosine similarity; built CONCURRENTLY in migration to avoid lock
-- CREATE INDEX ix_documents_embedding_hnsw ON documents USING hnsw (embedding vector_cosine_ops)
--       WITH (m = 16, ef_construction = 64);
-- Keep IVFFLAT fallback commented for small datasets

-- Backfill for existing rows: region='us', run_id = first run of job (done in 002 data migration)
```

### 2.4 Entities & Aliases

```sql
-- 002: new — canonical entity (company, person, product, market, etc.)
CREATE TABLE entities (
    id                UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_id            UUID NOT NULL REFERENCES research_jobs(id) ON DELETE CASCADE, -- null for global entities post-V1; scoped in V1
    run_id            UUID REFERENCES research_runs(id) ON DELETE CASCADE,
    entity_type       VARCHAR(30) NOT NULL CHECK (entity_type IN ('company','person','product','funding_round','investor','market','technology','unknown')),
    canonical_name    TEXT NOT NULL,
    normalized_name   TEXT NOT NULL, -- lowercased, punctuation-stripped, for dedup
    description       TEXT,
    domain            TEXT,          -- e.g., "openai.com"
    metadata          JSONB,         -- open: identifiers, links
    confidence        NUMERIC(4,3) NOT NULL DEFAULT 0.7,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (job_id, entity_type, normalized_name)
);
CREATE INDEX ix_entities_job_id ON entities(job_id);
CREATE INDEX ix_entities_type ON entities(entity_type);
CREATE INDEX ix_entities_canonical_trgm ON entities USING gin (canonical_name gin_trgm_ops);
CREATE INDEX ix_entities_normalized ON entities(normalized_name);

CREATE TABLE entity_aliases (
    id                UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    entity_id         UUID NOT NULL REFERENCES entities(id) ON DELETE CASCADE,
    alias             TEXT NOT NULL,
    alias_normalized  TEXT NOT NULL,
    source            VARCHAR(50) NOT NULL DEFAULT 'heuristic' CHECK (source IN ('heuristic','llm','human','import')),
    confidence        NUMERIC(4,3) NOT NULL DEFAULT 0.7,
    metadata          JSONB,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (entity_id, alias_normalized)
);
CREATE INDEX ix_entity_aliases_entity_id ON entity_aliases(entity_id);
CREATE INDEX ix_entity_aliases_alias_trgm ON entity_aliases USING gin (alias gin_trgm_ops);
```

### 2.5 Domain Tables (Company/People/Funding/Market)

> Kept intentionally lean for V1 — these are **projections from claims/evidence**, not manual entry. Verification and scoring join through them.

```sql
CREATE TABLE companies (
    id                UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    entity_id         UUID NOT NULL REFERENCES entities(id) ON DELETE CASCADE,
    job_id            UUID NOT NULL REFERENCES research_jobs(id) ON DELETE CASCADE,
    run_id            UUID REFERENCES research_runs(id) ON DELETE CASCADE,
    name              TEXT NOT NULL,
    legal_name        TEXT,
    domain            TEXT,
    founded_year      SMALLINT,
    headquarters      TEXT,
    industry          TEXT,
    employee_count    INTEGER,
    description       TEXT,
    metadata          JSONB,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (job_id, entity_id)
);
CREATE INDEX ix_companies_job_id ON companies(job_id);
CREATE INDEX ix_companies_entity_id ON companies(entity_id);

CREATE TABLE people (
    id                UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    entity_id         UUID NOT NULL REFERENCES entities(id) ON DELETE CASCADE,
    job_id            UUID NOT NULL REFERENCES research_jobs(id) ON DELETE CASCADE,
    run_id            UUID REFERENCES research_runs(id) ON DELETE CASCADE,
    full_name         TEXT NOT NULL,
    role              TEXT, -- "CEO", "CTO", etc.
    company_id        UUID REFERENCES companies(id) ON DELETE SET NULL,
    bio               TEXT,
    metadata          JSONB,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX ix_people_job_id ON people(job_id);
CREATE INDEX ix_people_company_id ON people(company_id);

CREATE TABLE funding_rounds (
    id                UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id        UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    job_id            UUID NOT NULL REFERENCES research_jobs(id) ON DELETE CASCADE,
    run_id            UUID REFERENCES research_runs(id) ON DELETE CASCADE,
    round_type        VARCHAR(30) CHECK (round_type IN ('pre_seed','seed','series_a','series_b','series_c','series_d_plus','ipo','grant','unknown')),
    amount_usd        NUMERIC(16,2),
    currency          VARCHAR(10) NOT NULL DEFAULT 'USD',
    announced_at      DATE,
    lead_investor     TEXT,
    metadata          JSONB,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX ix_funding_rounds_company_id ON funding_rounds(company_id);
CREATE INDEX ix_funding_rounds_job_id ON funding_rounds(job_id);

CREATE TABLE investors (
    id                UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    entity_id         UUID NOT NULL REFERENCES entities(id) ON DELETE CASCADE,
    job_id            UUID NOT NULL REFERENCES research_jobs(id) ON DELETE CASCADE,
    name              TEXT NOT NULL,
    investor_type     VARCHAR(30) CHECK (investor_type IN ('vc','angel','pe','corporate','government','unknown')),
    metadata          JSONB,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE funding_round_investors (
    funding_round_id  UUID NOT NULL REFERENCES funding_rounds(id) ON DELETE CASCADE,
    investor_id       UUID NOT NULL REFERENCES investors(id) ON DELETE CASCADE,
    PRIMARY KEY (funding_round_id, investor_id)
);

CREATE TABLE markets (
    id                UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_id            UUID NOT NULL REFERENCES research_jobs(id) ON DELETE CASCADE,
    run_id            UUID REFERENCES research_runs(id) ON DELETE CASCADE,
    name              TEXT NOT NULL,
    size_usd          NUMERIC(18,2),
    cagr              NUMERIC(6,3),
    metadata          JSONB,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

### 2.6 Claims / Evidence / Claim Sources (Evidence-First Core)

```sql
-- 001 exists; final view adds run_id, evidence/claim_sources split
CREATE TABLE claims (
    id                    UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_id                UUID NOT NULL REFERENCES research_jobs(id) ON DELETE CASCADE,
    run_id                UUID REFERENCES research_runs(id) ON DELETE CASCADE, -- 002
    document_id           UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE, -- primary extraction doc (may have many evidences)
    normalized_text       TEXT NOT NULL,
    subject               VARCHAR(500),
    predicate             VARCHAR(500),
    object                VARCHAR(500),
    event_time            TIMESTAMPTZ,
    extraction_confidence FLOAT NOT NULL DEFAULT 0.0 CHECK (extraction_confidence BETWEEN 0 AND 1),
    verification_status   VARCHAR(50) NOT NULL DEFAULT 'unverified'
        CHECK (verification_status IN ('verified','supported','contested','unverified','refuted')),
    verification_reasoning TEXT,
    embedding             VECTOR(1536),
    created_at            TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX ix_claims_job_id ON claims(job_id);
CREATE INDEX ix_claims_run_id ON claims(run_id);
CREATE INDEX ix_claims_document_id ON claims(document_id);
CREATE INDEX ix_claims_verification_status ON claims(verification_status);
-- CREATE INDEX ix_claims_embedding_hnsw ON claims USING hnsw (embedding vector_cosine_ops) WITH (m=16, ef_construction=64);

-- 002: new — evidence span (char offsets inside document content)
CREATE TABLE evidence (
    id                UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_id            UUID NOT NULL REFERENCES research_jobs(id) ON DELETE CASCADE,
    run_id            UUID REFERENCES research_runs(id) ON DELETE CASCADE,
    document_id       UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    source_id         VARCHAR(255) NOT NULL REFERENCES sources(id),
    -- citation anchor
    snippet           TEXT NOT NULL,                   -- extracted snippet (<= 500 chars)
    char_start        INTEGER,                         -- offset in documents.content
    char_end          INTEGER,
    relevance_score   NUMERIC(4,3) NOT NULL DEFAULT 0.5,
    evidence_type     VARCHAR(30) NOT NULL DEFAULT 'supporting'
        CHECK (evidence_type IN ('supporting','contradicting','context','primary')),
    metadata          JSONB,                           -- extraction trace, quote confidence
    created_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX ix_evidence_job_id ON evidence(job_id);
CREATE INDEX ix_evidence_run_id ON evidence(run_id);
CREATE INDEX ix_evidence_document_id ON evidence(document_id);
CREATE INDEX ix_evidence_source_id ON evidence(source_id);
CREATE INDEX ix_evidence_type ON evidence(evidence_type);

-- 002: new — many-to-many claim ↔ evidence (a claim may have N evidences across docs)
CREATE TABLE claim_evidence (
    claim_id          UUID NOT NULL REFERENCES claims(id) ON DELETE CASCADE,
    evidence_id       UUID NOT NULL REFERENCES evidence(id) ON DELETE CASCADE,
    role              VARCHAR(30) NOT NULL DEFAULT 'supporting'
        CHECK (role IN ('supporting','contradicting','context')),
    confidence        NUMERIC(4,3) NOT NULL DEFAULT 0.7,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (claim_id, evidence_id)
);
CREATE INDEX ix_claim_evidence_claim_id ON claim_evidence(claim_id);
CREATE INDEX ix_claim_evidence_evidence_id ON claim_evidence(evidence_id);

-- 002: new — claim ↔ source provenance (denormalized for fast tier-weighted scoring; source of truth is evidence→documents→sources)
CREATE TABLE claim_sources (
    claim_id          UUID NOT NULL REFERENCES claims(id) ON DELETE CASCADE,
    source_id         VARCHAR(255) NOT NULL REFERENCES sources(id),
    evidence_count    INTEGER NOT NULL DEFAULT 1,
    is_primary        BOOLEAN NOT NULL DEFAULT false,
    tier              SMALLINT NOT NULL CHECK (tier BETWEEN 1 AND 5),
    first_seen_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (claim_id, source_id)
);
CREATE INDEX ix_claim_sources_source_id ON claim_sources(source_id);
```

### 2.7 Social (Scoped, Public Only — V1)

```sql
-- 002: new — polymorphic extension of documents for social (shares documents.id 1:1 or standalone)
CREATE TABLE social_posts (
    id                UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id       UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    job_id            UUID NOT NULL REFERENCES research_jobs(id) ON DELETE CASCADE,
    run_id            UUID REFERENCES research_runs(id) ON DELETE CASCADE,
    platform          VARCHAR(20) NOT NULL CHECK (platform IN ('reddit','x','youtube','news_comments')),
    post_id           VARCHAR(255) NOT NULL, -- platform-native ID
    author_id         VARCHAR(255),
    author_handle     VARCHAR(255),
    title             TEXT,
    body              TEXT,
    score             INTEGER,               -- upvotes/likes (snapshot)
    comment_count     INTEGER,
    published_at      TIMESTAMPTZ,
    url               TEXT NOT NULL,
    metadata          JSONB,                 -- subreddit, community, etc.
    created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (platform, post_id)
);
CREATE INDEX ix_social_posts_job_id ON social_posts(job_id);
CREATE INDEX ix_social_posts_platform ON social_posts(platform);

CREATE TABLE social_authors (
    id                UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    platform          VARCHAR(20) NOT NULL,
    author_id         VARCHAR(255) NOT NULL,
    handle            VARCHAR(255),
    display_name      TEXT,
    follower_count    INTEGER,
    is_verified       BOOLEAN NOT NULL DEFAULT false,
    metadata          JSONB,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (platform, author_id)
);
```

### 2.8 Scores, Contradictions, Lineages, Runs (Existing + Extended)

```sql
-- 002: new — deterministic score snapshot per claim per run (auditable, not recomputed on read)
CREATE TABLE scores (
    id                UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    claim_id          UUID NOT NULL REFERENCES claims(id) ON DELETE CASCADE,
    job_id            UUID NOT NULL REFERENCES research_jobs(id) ON DELETE CASCADE,
    run_id            UUID NOT NULL REFERENCES research_runs(id) ON DELETE CASCADE,
    final_score       NUMERIC(5,4) NOT NULL CHECK (final_score BETWEEN 0 AND 1),
    confidence        NUMERIC(5,4) NOT NULL CHECK (confidence BETWEEN 0 AND 1),
    tier_weighted_support NUMERIC(6,3) NOT NULL DEFAULT 0,
    recency_score     NUMERIC(4,3) NOT NULL DEFAULT 0,
    coverage_score    NUMERIC(4,3) NOT NULL DEFAULT 0,
    factors           JSONB NOT NULL, -- {evidence_quality, source_independence, primary_evidence, temporal_consistency, corroboration, contradiction_penalty, staleness_penalty, ...}
    explanation       JSONB,          -- {supporting:[], weakening:[]}
    rank              INTEGER,        -- deterministic rank within job/run
    created_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX ix_scores_claim_id ON scores(claim_id);
CREATE INDEX ix_scores_job_id ON scores(job_id);
CREATE INDEX ix_scores_run_id ON scores(run_id);
CREATE INDEX ix_scores_rank ON scores(job_id, run_id, rank) WHERE rank IS NOT NULL;

-- 001 exists — contradictions (claimA ↔ claimB)
CREATE TABLE contradictions (
    id                UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_id            UUID NOT NULL REFERENCES research_jobs(id) ON DELETE CASCADE,
    run_id            UUID REFERENCES research_runs(id) ON DELETE CASCADE, -- 002 adds
    claim_a_id        UUID NOT NULL REFERENCES claims(id) ON DELETE CASCADE,
    claim_b_id        UUID NOT NULL REFERENCES claims(id) ON DELETE CASCADE,
    contradiction_type VARCHAR(100) NOT NULL, -- 'direct', 'temporal', 'numeric', 'attribution'
    severity          VARCHAR(20) NOT NULL DEFAULT 'medium' CHECK (severity IN ('low','medium','high','critical')),
    description       TEXT,
    resolution        VARCHAR(30) CHECK (resolution IN ('unresolved','a_prevails','b_prevails','both_contested','needs_human')),
    metadata          JSONB,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    CHECK (claim_a_id <> claim_b_id)
);
CREATE INDEX ix_contradictions_job_id ON contradictions(job_id);
CREATE INDEX ix_contradictions_run_id ON contradictions(run_id);
CREATE INDEX ix_contradictions_claim_a ON contradictions(claim_a_id);
CREATE INDEX ix_contradictions_claim_b ON contradictions(claim_b_id);

-- 001 exists — source_lineages (document provenance graph)
CREATE TABLE source_lineages (
    id                UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_a_id     UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    document_b_id     UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    relationship      VARCHAR(50) NOT NULL CHECK (relationship IN ('derived_from','cites','quotes','reposts','copies','summarizes','independently_reports')),
    confidence        FLOAT NOT NULL DEFAULT 0.0,
    evidence          TEXT,
    metadata          JSONB,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    CHECK (document_a_id <> document_b_id)
);
CREATE INDEX ix_source_lineages_doc_a ON source_lineages(document_a_id);
CREATE INDEX ix_source_lineages_doc_b ON source_lineages(document_b_id);

-- 001 exists — graph_nodes/edges (evidence-graph overlay)
CREATE TABLE graph_nodes (
    id                UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    node_type         VARCHAR(50) NOT NULL CHECK (node_type IN ('claim','document','source','entity','event','author','evidence')),
    node_id           UUID NOT NULL, -- FK polymorphic (app-enforced)
    metadata          JSONB,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX ix_graph_nodes_node_type ON graph_nodes(node_type);
CREATE INDEX ix_graph_nodes_node_id ON graph_nodes(node_id);
CREATE INDEX ix_graph_nodes_type_id ON graph_nodes(node_type, node_id);

CREATE TABLE graph_edges (
    id                UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_node_id    UUID NOT NULL REFERENCES graph_nodes(id) ON DELETE CASCADE,
    target_node_id    UUID NOT NULL REFERENCES graph_nodes(id) ON DELETE CASCADE,
    edge_type         VARCHAR(50) NOT NULL CHECK (edge_type IN ('supports','contradicts','derived_from','cites','mentions','authored_by','resolves_to')),
    metadata          JSONB,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    CHECK (source_node_id <> target_node_id)
);
CREATE INDEX ix_graph_edges_source ON graph_edges(source_node_id);
CREATE INDEX ix_graph_edges_target ON graph_edges(target_node_id);
CREATE INDEX ix_graph_edges_type ON graph_edges(edge_type);
CREATE INDEX ix_graph_edges_source_target ON graph_edges(source_node_id, target_node_id);

-- 001 exists — retrieval_runs / verification_runs (per-run now)
CREATE TABLE retrieval_runs (
    id                UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_id            UUID NOT NULL REFERENCES research_jobs(id) ON DELETE CASCADE,
    run_id            UUID REFERENCES research_runs(id) ON DELETE CASCADE, -- 002 adds
    connector_name    VARCHAR(100) NOT NULL,
    status            VARCHAR(50) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending','running','complete','failed','timeout','rate_limited')),
    documents_retrieved INTEGER NOT NULL DEFAULT 0,
    error             TEXT,
    started_at        TIMESTAMPTZ,
    completed_at      TIMESTAMPTZ,
    metadata          JSONB,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX ix_retrieval_runs_job_id ON retrieval_runs(job_id);
CREATE INDEX ix_retrieval_runs_run_id ON retrieval_runs(run_id);

CREATE TABLE verification_runs (
    id                UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_id            UUID NOT NULL REFERENCES research_jobs(id) ON DELETE CASCADE,
    run_id            UUID REFERENCES research_runs(id) ON DELETE CASCADE, -- 002 adds
    round_number      INTEGER NOT NULL DEFAULT 1,
    claims_verified   INTEGER NOT NULL DEFAULT 0,
    contradictions_detected INTEGER NOT NULL DEFAULT 0,
    duration_ms       INTEGER,
    metadata          JSONB,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX ix_verification_runs_job_id ON verification_runs(job_id);
CREATE INDEX ix_verification_runs_run_id ON verification_runs(run_id);
```

### 2.9 Benchmarks / Eval Runs

```sql
CREATE TABLE benchmarks (
    id                UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    slug              VARCHAR(100) UNIQUE NOT NULL, -- "cat_A_startup_identity"
    category          VARCHAR(30) NOT NULL CHECK (category IN ('A','B','C','D','E','F','G','H')),
    name              TEXT NOT NULL,
    description       TEXT,
    query             TEXT NOT NULL,               -- input query
    expected_entities JSONB,                       -- ground truth (optional)
    expected_claims   JSONB,
    metrics_config    JSONB,                       -- per-category thresholds
    created_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE eval_runs (
    id                UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    benchmark_id      UUID NOT NULL REFERENCES benchmarks(id) ON DELETE CASCADE,
    engine_variant    VARCHAR(30) NOT NULL CHECK (engine_variant IN ('baseline_search','baseline_llm','engine')),
    job_id            UUID REFERENCES research_jobs(id) ON DELETE SET NULL, -- linked job if engine variant
    config_hash       VARCHAR(64) NOT NULL,
    model_versions    JSONB NOT NULL,
    metrics           JSONB NOT NULL, -- {recall, precision, source_diversity, regional, language, entity_accuracy, claim_f1, citation_coverage, primary_ratio, cost_usd, latency_ms}
    passed            BOOLEAN NOT NULL DEFAULT false,
    metadata          JSONB,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX ix_eval_runs_benchmark_id ON eval_runs(benchmark_id);
CREATE INDEX ix_eval_runs_variant ON eval_runs(engine_variant);
```

### 2.10 Reports (Optional Sidecar for Large Reports)

```sql
-- 003: optional — keeps research_jobs.report small; large reports paginated
CREATE TABLE reports (
    id                UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_id            UUID NOT NULL REFERENCES research_jobs(id) ON DELETE CASCADE,
    run_id            UUID NOT NULL REFERENCES research_runs(id) ON DELETE CASCADE,
    markdown          TEXT NOT NULL,
    json_payload      JSONB NOT NULL, -- structured report for API
    citation_count    INTEGER NOT NULL DEFAULT 0,
    claim_count       INTEGER NOT NULL DEFAULT 0,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (job_id, run_id)
);
```

---

## 3. ER Notes

- **No polymorphic FK enforcement at DB level** for `graph_nodes.node_id` / `reports` — app-layer checks + periodic orphan sweep job. Trade-off: flexibility vs. referential integrity; acceptable for evidence graph where node types evolve.
- **`documents.run_id` nullable in migration 002** — backfill existing rows to `MIN(research_runs.id)` per job before adding `NOT NULL` in 004 (after vertical slice stabilizes).
- **`evidence.char_start/char_end`** — nullable to support LLM-extracted snippets without precise offsets in Phase 1; Phase 3 adds char-offset normalizer with fallback to snippet-only.
- **Soft-delete none in V1** — dedup via `is_duplicate_of` pointer, not delete. Rationale: preserve audit trail + allow dedup reason analysis in evals.
- **Domain tables (`companies/people/etc.`) are 1:1 with `entities` per job** — `entities` is the canonical registry; domain tables are typed projections for scoring/reporting (avoids EAV).
- **Indexes are query-shaped** — each index maps to an access pattern in `AGENT_CONTRACTS.md` (e.g., `ix_documents_source_id` for tier-weighted scoring, `ix_claims_embedding_hnsw` for near-duplicate claim dedup).

---

## 4. pgvector Usage

- **Dimensions:** `VECTOR(1536)` frozen for V1 (OpenAI `text-embedding-3-small` + Gemini 1536-compatible). Changing dims is a breaking migration (re-embed all rows).

- **Columns:** `documents.embedding`, `claims.embedding` (per-document and per-claim). `evidence` does **not** have its own embedding — similarity is via claim embedding → document embedding.

- **Distance:** `cosine` (`vector_cosine_ops`) for semantic dedup and evidence retrieval. `l2` not used.

- **Index strategy:**

  | Rows per table | Index | Params | When |
  |---|---|---|---|
  | `< 50k` | No index (exact `ORDER BY embedding <=> query`) | — | Phase 1 vertical slice |
  | `50k–500k` | `IVFFLAT` | `lists=100`, `probes=10` | Phase 4 |
  | `> 500k` | `HNSW` | `m=16`, `ef_construction=64`, `ef_search=40` | Post-V1 if needed |

  Migration creates HNSW `CONCURRENTLY` after table reaches threshold — not on empty tables (HNSW build on empty is wasteful and locking).

- **Embedding generation:** `packages/extraction/embedder.py` (calls `litellm.embedding` with `llm_embedding_model`); batched, retryable, cost-counted via `BudgetController`. Null embeddings allowed (not all docs need embedding in `quick` depth).

- **Dedup thresholds:** `documents` near-duplicate if `cosine < 0.08` + `content_hash` mismatch → mark `is_duplicate_of` with `dedup_reason='near_duplicate'`. `claims` duplicate if `cosine < 0.12` → merge into canonical claim (keep max `extraction_confidence`).

---

## 5. Migrations Strategy (Alembic)

- **Single lineage from `001`** — never squash-replace 001. Additive migrations only until post-V1.
- **Planned migrations:**

  | Rev | Name | Contents |
  |-----|------|----------|
  | `001` | `initial_tables` | ✅ existing (9 tables) |
  | `002` | `v1_entities_sources_evidence` | `sources`, `entities`, `entity_aliases`, `evidence`, `claim_evidence`, `claim_sources`, `companies/people/funding_rounds/investors/markets`, `social_posts/authors`, `benchmarks/eval_runs`, add `research_runs`, `research_queries`, alter `documents`/`claims`/`contradictions` to add `run_id`, add `region` |
  | `003` | `v1_budget_scores` | add budget columns to `research_jobs`/`research_runs`, add `scores`, `reports`, `report_json` |
  | `004` | `v1_constraints_not_null` | backfill `run_id` NOT NULL, add check constraints, create HNSW indexes CONCURRENTLY |
  | `005` | `v1_verification_status_migration` | migrate `claims.verification_status` 8→5 states, add `confidence` column, backfill scores |

- **Data migrations:** Each schema migration may have a paired data backfill (e.g., `002` copies `connector_statuses` JSON into `retrieval_runs` if empty, links existing docs to first run). Backfills run in same migration inside `op.execute` with batch commits.

- **Downgrade:** Each migration implements `downgrade()` that drops added tables/columns (no data loss guarantee for vectors — downgrade is for dev only; prod uses forward-only via `alembic upgrade head`).

- **CI gate:** `alembic check` + `alembic upgrade head && pytest` on every PR. Migration file naming: `002_v1_...py`, description includes V1 phase.

- **Config hash in migrations:** `configs/` SHA mixed into `research_jobs.config_hash` at job creation — not a DB migration, but run-time provenance.

---

## 6. Typed Python Models (SQLAlchemy)

Each table maps to a `Mapped` class in its package (`src/research/models.py` → `ResearchJob`, `src/documents/models.py` → `Document`, etc.). V1 adds `src/entities/models.py` for `Entity`/`EntityAlias`, `src/evidence/models.py` for `Evidence`/`ClaimSource`. All models:

- Use `UUID(as_uuid=True)`, `mapped_column`, `DateTime(timezone=True)`.
- Implement `__init__` that auto-sets `content_hash` / `normalized_name` where applicable.
- Are imported in `alembic/env.py` for `target_metadata`.

---

## 7. Open Items for Review

- **Vector index timing:** Confirm HNSW deferred to 004 (not 002) — avoids slow CI on empty tables.
- **`research_jobs.report` vs `reports` table:** Keep `report` text column for vertical slice simplicity; migrate to `reports` sidecar in 003 when reports exceed 50k chars in practice.
- **`sources` as table vs YAML-only:** Freeze is **YAML source of truth, DB cache** — `sources` table is populated on startup from `configs/sources/*.yaml`; DB is queryable but not authoring surface in V1. Confirm.
- **`social_posts` scope:** V1 only Reddit/X public; `platform` enum will grow post-V1 — already designed as VARCHAR+check for easy extension.
