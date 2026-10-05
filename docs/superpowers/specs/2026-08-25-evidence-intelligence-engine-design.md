# Evidence Intelligence Engine — Design Specification

**Goal:** Build a general-purpose Evidence Intelligence Engine for deep web research, source discovery, claim extraction, provenance tracking, cross-source verification, contradiction detection, and auditable research reports.

**Stack:** Python 3.12+, FastAPI, SQLAlchemy async, PostgreSQL with pgvector, Redis (arq), LiteLLM, structlog, OpenTelemetry

**Status:** Architecture approved, pending implementation

---

## 1. Product Definition

### Core Problem

A normal search engine answers: "What information can I find?"

This system answers: "What information can I find, where did it originate, what evidence supports it, what evidence contradicts it, which sources are actually independent, and how confident should I be?"

### Optimization Principles

- **Evidence > source count**
- **Provenance > repetition**
- **Claim-level verification > article-level classification**
- **Primary evidence > secondary summaries**
- **Transparency > false certainty**
- **Auditability > magic**

### Scope

Supports arbitrary research topics: people, organizations, companies, politics, science, technology, current events, historical research, market intelligence, OSINT.

Does NOT include: opportunity-search module (scholarships, competitions, research opportunities) — deferred to future phase.

---

## 2. Architecture Overview

### Tech Stack

| Component | Technology |
|-----------|------------|
| API Framework | FastAPI |
| Database | PostgreSQL 16+ with pgvector extension |
| ORM | SQLAlchemy 2.0 async |
| Migrations | Alembic |
| Queue/Cache | Redis (arq for job queue) |
| LLM Provider | LiteLLM (supports OpenAI, Anthropic, local models) |
| Observability | structlog, OpenTelemetry, Prometheus |
| HTTP Client | httpx (async) |
| Testing | pytest, pytest-asyncio |

### Package Structure

```
evidence-engine/
├── src/
│   ├── core/                    # Types, errors, Result, config, retry, circuit_breaker
│   ├── research/                # ResearchJob, lifecycle, orchestration, two-pass model
│   ├── connectors/              # Connector interface + implementations
│   ├── documents/               # Document model, normalization, dedup, content hashing
│   ├── claims/                  # Claim extraction, status tracking
│   ├── provenance/              # Source lineage logic, independence analysis
│   ├── graph/                   # Evidence graph persistence, query API
│   ├── verification/            # VerificationEngine, ContradictionEngine
│   ├── confidence/              # Explainable confidence scoring
│   ├── llm/                     # LLM provider abstraction
│   ├── reporting/               # Report generation
│   └── observability/           # Logging, metrics, tracing
├── tests/
│   ├── unit/
│   ├── integration/
│   └── security/
├── alembic/
├── pyproject.toml
└── docker-compose.yml
```

### Module Dependency Rules

1. `core/` depends on nothing — foundation layer
2. `documents/`, `claims/`, `provenance/`, `graph/` depend only on `core/`
3. `connectors/` depends on `core/`, `documents/`
4. `verification/` depends on `core/`, `graph/`, `claims/`
5. `confidence/` depends on `core/`, `verification/`, `graph/`
6. `research/` depends on everything above (orchestration layer)
7. `reporting/` depends on `research/`, `graph/`, `confidence/`

---

## 3. ResearchJob Orchestration

### ResearchJob Model

```python
class JobStatus(str, Enum):
    PENDING = "pending"
    PLANNING = "planning"
    DISCOVERING = "discovering"
    RETRIEVING = "retrieving"
    NORMALIZING = "normalizing"
    EXTRACTING = "extracting"
    VERIFYING = "verifying"
    RED_TEAM = "red_team"
    REPORTING = "reporting"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"

class PassType(str, Enum):
    DISCOVERY = "discovery"
    ADVERSARIAL = "adversarial"

class ResearchJob(Base):
    __tablename__ = "research_jobs"
    
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    query: Mapped[str] = mapped_column(String(5000), nullable=False)
    normalized_query: Mapped[str | None] = mapped_column(String(5000))
    status: Mapped[str] = mapped_column(String(50), default=JobStatus.PENDING)
    current_pass: Mapped[str] = mapped_column(String(50), default=PassType.DISCOVERY)
    
    # Scope configuration
    time_range_start: Mapped[datetime | None]
    time_range_end: Mapped[datetime | None]
    languages: Mapped[list | None] = mapped_column(JSON)  # ["en", "vi", "ru"]
    depth: Mapped[str] = mapped_column(String(50), default="standard")  # quick | standard | deep
    source_strategy: Mapped[str] = mapped_column(String(50), default="broad")
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    started_at: Mapped[datetime | None]
    completed_at: Mapped[datetime | None]
    
    # Retry state
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    max_retries: Mapped[int] = mapped_column(Integer, default=3)
    last_error: Mapped[str | None] = mapped_column(Text)
    
    # Results summary
    total_documents: Mapped[int] = mapped_column(Integer, default=0)
    retrieved_documents: Mapped[int] = mapped_column(Integer, default=0)
    claims_extracted: Mapped[int] = mapped_column(Integer, default=0)
    contradictions_found: Mapped[int] = mapped_column(Integer, default=0)
    
    # Relationships
    connector_statuses: Mapped[list | None] = mapped_column(JSON)
    report: Mapped[str | None] = mapped_column(Text)  # Final report (Markdown)
```

### Lifecycle State Machine

```
PENDING
  │
  ▼
PLANNING ──(query planning, entity extraction, search strategy)
  │
  ▼
DISCOVERING ──(connector search, parallel across connectors)
  │
  ▼
RETRIEVING ──(document fetch, content extraction)
  │
  ▼
NORMALIZING ──(document normalization, deduplication)
  │
  ▼
EXTRACTING ──(claim extraction from documents)
  │
  ▼
VERIFYING ──(initial claim verification against evidence)
  │
  ▼
RED_TEAM ──(adversarial verification, contradiction search)
  │
  ▼
REPORTING ──(final report generation)
  │
  ▼
COMPLETED | PARTIAL | FAILED
```

**State transition rules:**
- Any state → FAILED: on unrecoverable error
- Any state → PARTIAL: when enough progress made but some connectors failed
- DISCOVERING → PARTIAL: if all connectors fail but we have cached documents
- RED_TEAM → REPORTING: when adversarial pass completes (even if some claims unverified)

### Connector Status Tracking

```python
class ConnectorStatus(BaseModel):
    connector_name: str
    status: Literal["pending", "running", "complete", "failed", "timeout", "rate_limited"]
    documents_retrieved: int = 0
    error: str | None = None
    retry_count: int = 0
    next_retry_at: datetime | None = None

class JobCoverageReport(BaseModel):
    connectors: list[ConnectorStatus]
    total_searched: int
    total_succeeded: int
    total_failed: int
    coverage_percentage: float
    partial: bool
```

**Coverage report example:**
```
Research Coverage:
  Google Search    COMPLETE  (42 documents)
  Reddit           COMPLETE  (18 documents)
  RSS Feeds        COMPLETE  (7 documents)
  YouTube          FAILED    (timeout after 30s)
  News API         COMPLETE  (23 documents)
  
  Total: 90 documents retrieved
  Coverage: 80% (4/5 connectors succeeded)
  Status: PARTIAL
```

---

## 4. Two-Pass Research Model

### Pass 1 — Discovery

**Goal:** Maximize relevant information coverage.

```
QueryPlanner
  → generates search queries, entities, topics
  → spawns parallel connector searches
  → each connector returns RawResults
  → DocumentNormalizer creates Document objects
  → Deduplicator removes exact/near duplicates
  → SourceLineageAnalyzer begins lineage tracking
  → ClaimExtractor extracts claims from documents
  → EvidenceGraph stores claims + evidence relationships
  → InitialVerification runs first-pass verification
```

**Discovery pass outputs:**
- Document corpus (deduplicated)
- Initial claim set
- Initial evidence graph
- Source lineage (初步)
- Initial confidence scores

### Pass 2 — Adversarial Verification

**Goal:** Actively try to DISPROVE initial conclusions.

```python
class AdversarialPass:
    async def run(self, job: ResearchJob, claims: list[Claim]) -> AdversarialResult:
        """Execute adversarial verification pass."""
        
        for round in range(self.max_rounds):
            # For each major claim:
            for claim in claims:
                # 1. Search for contradicting evidence
                contradictions = await self.search_contradictions(claim)
                
                # 2. Search for primary sources
                primary_sources = await self.search_primary_sources(claim)
                
                # 3. Verify source independence
                independence = await self.provenance.analyze_independence(claim.sources)
                
                # 4. Re-verify with new evidence
                new_result = await self.verifier.verify(claim, contradictions + primary_sources)
                
                # 5. If confidence changed significantly → may need more rounds
                if abs(new_result.confidence - claim.current_confidence) > 0.15:
                    self.needs_another_round = True
            
            if not self.needs_another_round:
                break  # Stable — no significant confidence changes
        
        return AdversarialResult(...)
```

**Adversarial pass terminates when:**
- All major claims re-verified, OR
- Max iterations reached (default: 3), OR
- No new evidence found in last iteration, OR
- No significant confidence changes in last iteration

---

## 5. Data Flow Details

### Query Planner

```python
class QueryPlan(BaseModel):
    entities: list[Entity]          # Extracted entities (people, orgs, etc.)
    topics: list[str]               # Topic expansions
    time_range: TimeRange | None    # Date constraints
    languages: list[str]            # Target languages
    search_queries: list[str]       # Generated search queries
    source_categories: list[str]    # ["news", "official", "social", "academic"]
    depth: str                      # quick | standard | deep
    priority_claim_types: list[str] # ["factual", "temporal", "causal"]

class QueryPlanner:
    async def plan(self, query: str, config: dict) -> QueryPlan:
        """Generate research plan from user query.
        
        Rules:
        - Must NOT hallucinate facts
        - Search expansion IS allowed
        - Entity extraction from query text only
        - Time range inference from query keywords
        """
        ...
```

### Source Connectors

```python
class SourceConnector(Protocol):
    """Interface for all source connectors."""
    
    async def search(self, query: SearchQuery) -> list[RawResult]:
        """Search the source for relevant content."""
        ...
    
    async def fetch(self, url: str) -> RawResult:
        """Fetch a specific URL."""
        ...
    
    async def health_check(self) -> bool:
        """Check if the connector is available."""
        ...
    
    @property
    def name(self) -> str: ...
    
    @property
    def rate_limit(self) -> RateLimitConfig: ...

class SearchQuery(BaseModel):
    query: str
    time_range: TimeRange | None = None
    languages: list[str] = Field(default_factory=lambda: ["en"])
    max_results: int = 20
    result_type: str = "all"  # all | news | discussion | video

class RawResult(BaseModel):
    url: str
    title: str
    snippet: str
    content: str | None = None  # Full content if fetchable
    published_at: datetime | None = None
    author: str | None = None
    source_name: str
    metadata: dict = Field(default_factory=dict)
```

**Built-in connectors:**
- `WebSearchConnector` — Google/Bing search via API
- `NewsConnector` — News API integration
- `RedditConnector` — Reddit API (public endpoints)
- `RSSConnector` — RSS/Atom feed reader
- `YouTubeConnector` — YouTube Data API
- `OfficialWebsiteConnector` — Direct website fetch with robots.txt compliance

**Connector rules:**
- Do NOT bypass authentication, paywalls, rate limits, robots.txt
- Use official APIs or legally accessible public information
- Each connector is independently replaceable
- Connector failures are isolated — one failing connector does not fail the job

### Document Model

```python
class Document(Base):
    __tablename__ = "documents"
    
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    job_id: Mapped[UUID] = mapped_column(ForeignKey("research_jobs.id"))
    source_id: Mapped[str] = mapped_column(String(255))  # Connector name
    
    url: Mapped[str] = mapped_column(Text, nullable=False)
    canonical_url: Mapped[str | None] = mapped_column(Text)
    title: Mapped[str | None] = mapped_column(Text)
    author: Mapped[str | None] = mapped_column(String(500))
    publisher: Mapped[str | None] = mapped_column(String(500))
    published_at: Mapped[datetime | None]
    retrieved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    language: Mapped[str] = mapped_column(String(10), default="en")
    
    content: Mapped[str] = mapped_column(Text)
    content_hash: Mapped[str] = mapped_column(String(64))  # SHA-256
    mime_type: Mapped[str] = mapped_column(String(100), default="text/html")
    
    # Deduplication
    is_duplicate_of: Mapped[UUID | None] = mapped_column(ForeignKey("documents.id"))
    dedup_reason: Mapped[str | None] = mapped_column(String(100))
    
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSON)
    embedding: Mapped[bytes | None] = mapped_column(pgvector.Vector(1536))
```

### Deduplication

Multi-layer deduplication in `documents/dedup.py`:

```python
class Deduplicator:
    async def dedup(self, documents: list[Document]) -> list[Document]:
        """Remove duplicates using multiple layers."""
        
        # Layer 1: Exact URL match
        docs = self.dedup_by_exact_url(documents)
        
        # Layer 2: Canonical URL normalization
        docs = self.dedup_by_canonical_url(docs)
        
        # Layer 3: Content hash (SHA-256)
        docs = self.dedup_by_content_hash(docs)
        
        # Layer 4: Text similarity (Jaccard on shingles)
        docs = self.dedup_by_text_similarity(docs, threshold=0.85)
        
        # Layer 5: Semantic similarity (pgvector cosine)
        docs = await self.dedup_by_semantic_similarity(docs, threshold=0.92)
        
        return docs
```

**Critical rule:** Two articles covering the same event are NOT necessarily duplicates. Do not collapse independent journalism merely because the topic is similar. Only mark as duplicate if content is substantively identical.

### Claim Extraction

```python
class ClaimStatus(str, Enum):
    VERIFIED = "verified"
    PROBABLY_TRUE = "probably_true"
    PARTIALLY_SUPPORTED = "partially_supported"
    CONTESTED = "contested"
    UNVERIFIED = "unverified"
    PROBABLY_FALSE = "probably_false"
    FALSE = "false"
    OUTDATED = "outdated"

class Claim(Base):
    __tablename__ = "claims"
    
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    job_id: Mapped[UUID] = mapped_column(ForeignKey("research_jobs.id"))
    document_id: Mapped[UUID] = mapped_column(ForeignKey("documents.id"))
    
    normalized_text: Mapped[str] = mapped_column(Text)
    subject: Mapped[str | None] = mapped_column(String(500))
    predicate: Mapped[str | None] = mapped_column(String(500))
    object: Mapped[str | None] = mapped_column(String(500))
    event_time: Mapped[datetime | None]
    
    extraction_confidence: Mapped[float] = mapped_column(Float)
    verification_status: Mapped[str] = mapped_column(String(50), default=ClaimStatus.UNVERIFIED)
    verification_reasoning: Mapped[str | None] = mapped_column(Text)
    
    # Embedding for semantic search
    embedding: Mapped[bytes | None] = mapped_column(pgvector.Vector(1536))
```

**Claim extraction rules:**
- Do NOT treat an article as one factual unit
- Extract individual claims with subject-predicate-object structure
- Preserve source document reference for every claim
- Extraction confidence reflects how clearly the source states the claim

### Provenance (Domain Logic)

```python
class LineageRelationship(str, Enum):
    DERIVED_FROM = "derived_from"
    CITES = "cites"
    QUOTES = "quotes"
    REPOSTS = "reposts"
    COPIES = "copies"
    SUMMARIZES = "summarizes"
    INDEPENDENTLY_REPORTS = "independently_reports"

class SourceLineageAnalyzer:
    """Domain logic for source independence and lineage analysis."""
    
    async def analyze_pair(
        self, doc_a: Document, doc_b: Document
    ) -> LineageResult:
        """Determine relationship between two documents.
        
        Checks:
        - Content overlap (text similarity)
        - Temporal proximity (publication times)
        - Citation patterns (does B cite A?)
        - Source history (have these sources interacted before?)
        - Language analysis (translated vs original)
        """
        ...
    
    async def analyze_independence(
        self, sources: list[Source]
    ) -> IndependenceAssessment:
        """Assess whether sources are genuinely independent.
        
        NOT just different domains. Considers:
        - Wire services (AP, Reuters → many outlets publish same story)
        - Syndication (newspaper syndicates)
        - Content farms (multiple sites, same owner)
        - Official sources vs reporting on official sources
        """
        ...
```

### Evidence Graph (Persistence)

```python
class GraphNodeType(str, Enum):
    CLAIM = "claim"
    DOCUMENT = "document"
    SOURCE = "source"
    ENTITY = "entity"
    EVENT = "event"
    AUTHOR = "author"

class GraphEdgeType(str, Enum):
    SUPPORTS = "supports"
    CONTRADICTS = "contradicts"
    DERIVED_FROM = "derived_from"
    CITES = "cites"
    MENTIONS = "mentions"
    AUTHORED_BY = "authored_by"

class EvidenceGraphStore:
    """Persistence and query layer for the evidence graph."""
    
    async def add_node(self, node_type: GraphNodeType, node_id: UUID, metadata: dict) -> None:
        """Add a node to the graph."""
        ...
    
    async def add_edge(
        self,
        source_id: UUID,
        target_id: UUID,
        edge_type: GraphEdgeType,
        metadata: dict,
    ) -> None:
        """Add a directed edge to the graph."""
        ...
    
    async def get_supporting_evidence(self, claim_id: UUID) -> list[EvidenceEdge]:
        """Get all documents supporting a claim."""
        ...
    
    async def get_contradicting_evidence(self, claim_id: UUID) -> list[EvidenceEdge]:
        """Get all documents contradicting a claim."""
        ...
    
    async def trace_lineage(self, claim_id: UUID) -> LineageChain:
        """Trace full lineage chain back to primary sources."""
        ...
    
    async def get_independent_sources(self, claim_id: UUID) -> list[Source]:
        """Get genuinely independent sources supporting a claim."""
        ...
```

---

## 6. Verification and Contradiction

### Verification Engine

```python
class VerificationResult(BaseModel):
    claim_id: UUID
    status: ClaimStatus
    confidence: float  # 0.0 - 1.0
    reasoning: str
    supporting_count: int
    contradicting_count: int
    independent_source_count: int
    primary_source_available: bool
    source_lineage_summary: str
    factors: ConfidenceFactors

class ConfidenceFactors(BaseModel):
    """Explainable confidence breakdown."""
    evidence_quality: float        # -1.0 to +1.0
    source_independence: float     # -1.0 to +1.0
    primary_evidence: float        # -1.0 to +1.0
    temporal_consistency: float    # -1.0 to +1.0
    corroboration: float           # -1.0 to +1.0
    contradiction_penalty: float   # -1.0 to +1.0
    provenance_uncertainty: float  # -1.0 to +1.0
    staleness_penalty: float       # -1.0 to +1.0

class VerificationEngine:
    async def verify_claim(
        self, claim: Claim, evidence_graph: EvidenceGraphStore
    ) -> VerificationResult:
        """Verify a single claim against current evidence graph."""
        ...
    
    async def iterative_verify(
        self,
        claims: list[Claim],
        evidence_graph: EvidenceGraphStore,
        contradiction_engine: ContradictionEngine,
        max_rounds: int = 3,
    ) -> list[VerificationResult]:
        """Run verification + contradiction in iterative rounds.
        
        Algorithm:
        1. Verify all claims
        2. Run contradiction detection
        3. If new contradictions found → update evidence graph → go to 1
        4. If no new contradictions or max_rounds reached → done
        """
        ...
```

### Contradiction Engine

```python
class Contradiction(BaseModel):
    claim_a_id: UUID
    claim_b_id: UUID
    contradiction_type: str  # "direct否定", "factual_mismatch", "temporal_conflict"
    severity: str  # "low" | "medium" | "high" | "critical"
    description: str

class ContradictionEngine:
    async def detect(
        self, claims: list[Claim], evidence_graph: EvidenceGraphStore
    ) -> list[Contradiction]:
        """Detect contradictions among claims.
        
        Methods:
        1. Semantic opposition detection (claim A implies not-claim B)
        2. Factual mismatch (different values for same attribute)
        3. Temporal conflict (contradictory timelines)
        4. Source credibility weighting (credible source contradicts less credible)
        """
        ...
    
    async def search_contradictions(
        self, claim: Claim, connectors: list[SourceConnector]
    ) -> list[Document]:
        """Actively search for evidence contradicting a specific claim."""
        ...
```

### Confidence Scoring

```python
class ConfidenceScorer:
    def score(self, verification_result: VerificationResult) -> ExplainableConfidence:
        """Calculate explainable confidence score.
        
        Formula:
        confidence = (
            evidence_quality
            + source_independence
            + primary_evidence
            + temporal_consistency
            + corroboration
            - contradiction_penalty
            - provenance_uncertainty
            - staleness_penalty
        ) / 8  # Normalize to 0-1
        
        Every score MUST expose contributing factors.
        """
        ...
```

**Confidence output example:**
```
Claim: "Putin met Xi on August 18"
Status: PROBABLY_TRUE
Confidence: 87%

Supporting factors:
  + Primary source available (official transcript)
  + 3 independent confirmations (Reuters, AP, TASS)
  + Consistent timestamps across sources

Weakening factors:
  - One credible contradictory source (BBC reports meeting was Aug 17)
  - Event occurred recently (2 days ago)
  - Source lineage shows 2 of 3 sources may share wire service origin
```

---

## 7. Failure Handling

### Retry Policy

```python
class RetryPolicy(BaseModel):
    max_retries: int = 3
    backoff_base_ms: int = 1000
    backoff_multiplier: float = 2.0
    max_backoff_ms: int = 30000
    retryable_errors: list[str] = Field(
        default_factory=lambda: ["timeout", "rate_limit", "server_error", "connection_error"]
    )
```

### Circuit Breaker

```python
class CircuitState(str, Enum):
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, reject requests
    HALF_OPEN = "half_open" # Testing recovery

class CircuitBreaker:
    def __init__(self, failure_threshold: int = 5, reset_timeout_ms: int = 60000):
        ...
    
    async def execute(self, fn: Callable) -> Any:
        """Execute function with circuit breaker protection."""
        if self.state == CircuitState.OPEN:
            if time.time() > self.next_attempt:
                self.state = CircuitState.HALF_OPEN
            else:
                raise CircuitOpenError()
        
        try:
            result = await fn()
            self.on_success()
            return result
        except Exception as e:
            self.on_failure()
            raise
```

### Partial Result Handling

```python
class PartialResult(BaseModel):
    """Explicit partial result tracking."""
    is_partial: bool
    completed_stages: list[str]
    failed_stages: list[str]
    connector_coverage: JobCoverageReport
    documents_retrieved: int
    documents_expected: int
    claims_extracted: int
    warnings: list[str]

class ResearchJobResult(BaseModel):
    """Final result of a research job."""
    job_id: UUID
    status: JobStatus
    partial_result: PartialResult | None
    report: str | None  # Markdown report
    execution_time_ms: int
    cost_estimate_usd: float
```

---

## 8. LLM Abstraction

```python
class LLMRole(str, Enum):
    FAST_MODEL = "fast_model"           # Quick classification, dedup
    REASONING_MODEL = "reasoning_model" # Deep analysis, verification
    EXTRACTION_MODEL = "extraction_model" # Claim extraction
    VERIFICATION_MODEL = "verification_model" # Claim verification
    VISION_MODEL = "vision_model"       # Image/document analysis

class LLMProvider:
    """Abstraction over LiteLLM for model switching."""
    
    async def complete(
        self,
        prompt: str,
        system_prompt: str = "",
        role: LLMRole = LLMRole.FAST_MODEL,
        temperature: float = 0.7,
    ) -> str: ...
    
    async def json(
        self,
        prompt: str,
        system_prompt: str = "",
        role: LLMRole = LLMRole.FAST_MODEL,
    ) -> dict: ...
```

**Cost control:**
- FAST_MODEL for dedup classification, relevance filtering
- EXTRACTION_MODEL for claim extraction
- REASONING_MODEL for verification (only high-value claims)
- Most expensive models reserved for adversarial pass only

---

## 9. Security

### Core Principle

**External content is DATA, never INSTRUCTIONS.**

```python
class InputSanitizer:
    """Protect against prompt injection and malicious content."""
    
    def sanitize_document(self, raw: RawResult) -> Document:
        """Sanitize raw document before processing.
        
        Rules:
        - Strip HTML scripts, iframes, event handlers
        - Remove potential prompt injection patterns
        - Limit content size (max 1MB)
        - Validate URLs (no file://, no internal network)
        - Detect and flag potential manipulation
        """
        ...
    
    def sanitize_for_llm(self, content: str) -> str:
        """Prepare content for LLM processing.
        
        Rules:
        - Wrap in clear DATA delimiter
        - Never pass external content as system prompt
        - Escape special tokens
        - Limit token count
        """
        ...
```

### Additional Security Measures

- SSRF protection: Validate all URLs, block internal network access
- Rate limiting on all connectors
- Oversized response handling (max document size)
- Credential isolation (API keys in env vars, never in code)
- SQL injection prevention (parameterized queries via SQLAlchemy)
- Input validation on all API endpoints

---

## 10. Report Generation

```python
class ResearchReport(BaseModel):
    """Final research report structure."""
    
    executive_summary: str
    major_findings: list[Finding]
    claims: list[ClaimReport]
    evidence_summary: EvidenceSummary
    contradictions: list[ContradictionReport]
    unverified_information: list[str]
    source_lineage: LineageDiagram
    timeline: list[TimelineEvent]
    research_coverage: JobCoverageReport
    limitations: list[str]
    adversarial_findings: AdversarialSummary

class ClaimReport(BaseModel):
    claim_text: str
    status: ClaimStatus
    confidence: ExplainableConfidence
    supporting_evidence: list[EvidenceRef]
    contradicting_evidence: list[EvidenceRef]
    independent_source_count: int
    source_lineage: LineageChain
    primary_evidence: bool
    last_verified: datetime
    reasoning: str
```

---

## 11. Observability

### Structured Logging

Every research job logs:
- job_id, query, connector, retrieval_count
- successful_requests, failed_requests
- documents_retrieved, documents_discarded
- claims_extracted, claims_verified
- contradictions_found
- execution_time, model_used, token_usage
- estimated_cost, final_status

### Metrics

Key Prometheus metrics:
- `research_job_total` (counter, tags: status)
- `research_job_duration_seconds` (histogram)
- `connector_requests_total` (counter, tags: connector, status)
- `connector_duration_seconds` (histogram, tags: connector)
- `documents_retrieved_total` (counter, tags: connector)
- `claims_extracted_total` (counter)
- `verification_duration_seconds` (histogram)
- `llm_calls_total` (counter, tags: model, role)
- `llm_tokens_total` (counter, tags: model, direction)
- `llm_cost_usd_total` (counter, tags: model)

---

## 12. Database Schema

### Tables

```sql
-- Research Jobs
CREATE TABLE research_jobs (
    id UUID PRIMARY KEY,
    query TEXT NOT NULL,
    normalized_query TEXT,
    status VARCHAR(50) DEFAULT 'pending',
    current_pass VARCHAR(50) DEFAULT 'discovery',
    time_range_start TIMESTAMPTZ,
    time_range_end TIMESTAMPTZ,
    languages JSONB,
    depth VARCHAR(50) DEFAULT 'standard',
    source_strategy VARCHAR(50) DEFAULT 'broad',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    last_error TEXT,
    total_documents INTEGER DEFAULT 0,
    retrieved_documents INTEGER DEFAULT 0,
    claims_extracted INTEGER DEFAULT 0,
    contradictions_found INTEGER DEFAULT 0,
    connector_statuses JSONB,
    report TEXT
);

-- Documents
CREATE TABLE documents (
    id UUID PRIMARY KEY,
    job_id UUID REFERENCES research_jobs(id),
    source_id VARCHAR(255),
    url TEXT NOT NULL,
    canonical_url TEXT,
    title TEXT,
    author VARCHAR(500),
    publisher VARCHAR(500),
    published_at TIMESTAMPTZ,
    retrieved_at TIMESTAMPTZ,
    language VARCHAR(10) DEFAULT 'en',
    content TEXT NOT NULL,
    content_hash VARCHAR(64),
    mime_type VARCHAR(100) DEFAULT 'text/html',
    is_duplicate_of UUID REFERENCES documents(id),
    dedup_reason VARCHAR(100),
    metadata JSONB,
    embedding vector(1536)
);

-- Claims
CREATE TABLE claims (
    id UUID PRIMARY KEY,
    job_id UUID REFERENCES research_jobs(id),
    document_id UUID REFERENCES documents(id),
    normalized_text TEXT NOT NULL,
    subject VARCHAR(500),
    predicate VARCHAR(500),
    object VARCHAR(500),
    event_time TIMESTAMPTZ,
    extraction_confidence FLOAT,
    verification_status VARCHAR(50) DEFAULT 'unverified',
    verification_reasoning TEXT,
    embedding vector(1536)
);

-- Evidence Graph Nodes
CREATE TABLE graph_nodes (
    id UUID PRIMARY KEY,
    node_type VARCHAR(50) NOT NULL,
    node_id UUID NOT NULL,
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Evidence Graph Edges
CREATE TABLE graph_edges (
    id UUID PRIMARY KEY,
    source_node_id UUID REFERENCES graph_nodes(id),
    target_node_id UUID REFERENCES graph_nodes(id),
    edge_type VARCHAR(50) NOT NULL,
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Source Lineages
CREATE TABLE source_lineages (
    id UUID PRIMARY KEY,
    document_a_id UUID REFERENCES documents(id),
    document_b_id UUID REFERENCES documents(id),
    relationship VARCHAR(50) NOT NULL,
    confidence FLOAT,
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Contradictions
CREATE TABLE contradictions (
    id UUID PRIMARY KEY,
    claim_a_id UUID REFERENCES claims(id),
    claim_b_id UUID REFERENCES claims(id),
    contradiction_type VARCHAR(100),
    severity VARCHAR(20),
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Retrieval Runs
CREATE TABLE retrieval_runs (
    id UUID PRIMARY KEY,
    job_id UUID REFERENCES research_jobs(id),
    connector_name VARCHAR(100),
    status VARCHAR(50),
    documents_retrieved INTEGER DEFAULT 0,
    error TEXT,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ
);

-- Verification Runs
CREATE TABLE verification_runs (
    id UUID PRIMARY KEY,
    job_id UUID REFERENCES research_jobs(id),
    round_number INTEGER,
    claims_verified INTEGER,
    contradictions_detected INTEGER,
    duration_ms INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### Indexes

```sql
CREATE INDEX idx_documents_job_id ON documents(job_id);
CREATE INDEX idx_documents_content_hash ON documents(content_hash);
CREATE INDEX idx_documents_canonical_url ON documents(canonical_url);
CREATE INDEX idx_documents_embedding ON documents USING ivfflat (embedding vector_cosine_ops);
CREATE INDEX idx_claims_job_id ON claims(job_id);
CREATE INDEX idx_claims_document_id ON claims(document_id);
CREATE INDEX idx_claims_embedding ON claims USING ivfflat (embedding vector_cosine_ops);
CREATE INDEX idx_claims_verification_status ON claims(verification_status);
CREATE INDEX idx_graph_nodes_node_type ON graph_nodes(node_type);
CREATE INDEX idx_graph_nodes_node_id ON graph_nodes(node_id);
CREATE INDEX idx_graph_edges_source ON graph_edges(source_node_id);
CREATE INDEX idx_graph_edges_target ON graph_edges(target_node_id);
CREATE INDEX idx_graph_edges_type ON graph_edges(edge_type);
CREATE INDEX idx_source_lineages_doc_a ON source_lineages(document_a_id);
CREATE INDEX idx_source_lineages_doc_b ON source_lineages(document_b_id);
CREATE INDEX idx_retrieval_runs_job_id ON retrieval_runs(job_id);
```

---

## 13. Testing Strategy

### Unit Tests

- Claim extraction (various document formats)
- Deduplication (URL, hash, semantic)
- Source normalization
- Lineage analysis
- Contradiction detection
- Confidence scoring
- Entity resolution
- Input sanitization (prompt injection attempts)

### Integration Tests

- Connector → Document pipeline
- Document → Claims pipeline
- Claims → Evidence pipeline
- Evidence → Verification pipeline
- Verification → Report pipeline
- Full ResearchJob lifecycle (mock connectors)

### Security Tests

- Prompt injection via document content
- Malicious HTML sanitization
- SSRF attempts (internal network URLs)
- Oversized content handling
- SQL injection attempts

### Synthetic Test Dataset

**Dataset A:** 100 websites copied from one original source
**Dataset B:** 5 genuinely independent sources

System must produce substantially different independence assessments.

---

## 14. Implementation Phases

### Phase 0: Foundation
- `core/` — Types, errors, Result, config, retry, circuit_breaker
- Database setup, migrations, Alembic config
- Project scaffolding (pyproject.toml, docker-compose)

### Phase 1: Research Job
- `research/` — ResearchJob model, lifecycle, orchestration
- Job queue (arq + Redis)
- Worker process

### Phase 2: First Connector
- `connectors/` — Connector interface
- WebSearchConnector implementation
- `documents/` — Document model, normalization

### Phase 3: Claims & Evidence
- `documents/dedup.py` — Deduplication
- `claims/` — Claim extraction
- `provenance/` — Source lineage logic
- `graph/` — Evidence graph persistence

### Phase 4: Verification
- `verification/` — VerificationEngine, ContradictionEngine
- `confidence/` — Confidence scoring
- Two-pass model implementation

### Phase 5: Reporting
- `reporting/` — Report generation
- Human inspection API

### Phase 6: Additional Connectors
- Reddit, RSS, YouTube, News connectors
- Only after core architecture is stable

### Phase 7: Production Hardening
- Observability (logging, metrics, tracing)
- Security hardening
- Load testing
- Documentation

---

## 15. Definition of Done — MVP

The MVP is complete when the user can enter:

```
Research the latest developments concerning [TOPIC].
```

and the system can:

1. Create a research plan
2. Search permitted sources
3. Retrieve documents
4. Normalize them
5. Deduplicate them
6. Extract claims
7. Track provenance
8. Build source lineage
9. Identify supporting evidence
10. Identify contradicting evidence
11. Verify major claims
12. Calculate explainable confidence
13. Generate an auditable report
14. Run adversarial verification
15. Allow human inspection of evidence

The system must fail transparently when evidence is insufficient.
