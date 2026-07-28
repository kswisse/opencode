# WORKFLOW-06: Memory Write/Read Flows

**Version**: 0.1
**Date**: 2026-07-28
**Author**: Workflow Architect
**Status**: Draft
**Implements**: Autonomous AI Workforce Platform — Episodic, Semantic, Vector, Project, Company, User Memory

---

## Overview

Memory is the system's long-term knowledge store. It captures what happened (episodic), what was learned (semantic), what is similar (vector), what belongs to a project (project memory), what belongs to a company (company memory), and what personalizes the user experience (user memory). Memory writes happen after tasks, after reflections, and during consolidation. Memory reads happen before every task execution.

---

## Actors

| Actor | Role in this workflow |
|---|---|
| Episodic Memory Writer | Records events and experiences |
| Semantic Memory Extractor | Extracts generalizable knowledge from experiences |
| Vector Memory Indexer | Indexes content for similarity search |
| Project Memory Manager | Manages project-scoped knowledge |
| Company Memory Aggregator | Aggregates knowledge across projects |
| User Memory Personalizer | Personalizes based on user preferences |
| Memory Consolidator | Merges, deduplicates, and compresses memory |
| Memory Reader | Retrieves relevant memory for task execution |

---

## Prerequisites

- Vector database is operational
- Memory schemas are defined
- Consolidation policies are configured
- Read/write permissions are set per company

---

## Trigger

Memory writes are triggered by:
1. Task completion (episodic)
2. Post-task reflection (semantic)
3. Conflict resolution (semantic)
4. Periodic consolidation (all types)
5. User feedback (user memory)

Memory reads are triggered by:
1. Agent task execution (pre-task context)
2. Goal decomposition (historical context)
3. Conflict resolution (precedent lookup)
4. Learning loop (pattern recognition)

---

## State Diagram

```
[EVENT] → [CAPTURED] → [PROCESSING] → [STORED]
                                    ↓
                              [CONSOLIDATING] → [CONSOLIDATED]
                                    ↓
                              [PRUNED | ARCHIVED]
```

---

## Workflow Tree

### STEP 1: Episodic Memory Write (After Task Completion)
**Actor**: Episodic Memory Writer
**Action**: Record what happened during task execution
**Timeout**: 10s
**Input**: `{ agent_id: uuid, task_id: uuid, event: { type, timestamp, input, output, metrics, errors } }`
**Output on SUCCESS**: `{ memory_id: uuid, type: "episodic", stored: true }` → GO TO STEP 2
**Output on FAILURE**:
- `FAILURE(write_error)`: Cannot write to memory store → retry x3 with 2s backoff → if all fail, log warning (memory loss acceptable for episodic)
- `FAILURE(quota_exceeded)`: Company memory quota full → trigger consolidation, then retry

**Episodic Memory Schema**:
```json
{
  "memory_id": "uuid",
  "type": "episodic",
  "company_id": "uuid",
  "agent_id": "uuid",
  "task_id": "uuid",
  "dag_id": "uuid",
  "project_id": "uuid",
  "event": {
    "type": "enum(task_started|task_completed|task_failed|conflict_resolved|agent_created|agent_destroyed)",
    "timestamp": "ISO8601",
    "input_summary": "string — compressed version of input",
    "output_summary": "string — compressed version of output",
    "metrics": {
      "tokens_used": "number",
      "time_seconds": "number",
      "cost_usd": "number",
      "quality_score": "number"
    },
    "errors": ["string"],
    "context": "object — relevant context for future reference"
  },
  "created_at": "ISO8601",
  "ttl_days": 90
}
```

---

### STEP 2: Semantic Memory Extraction
**Actor**: Semantic Memory Extractor
**Action**: After episodic memory is stored, extract generalizable knowledge
**Timeout**: 30s
**Input**: `{ memory_id: uuid, episodic_memory: object, company_context: object }`
**Output on SUCCESS**: `{ knowledge_id: uuid, type: "semantic", knowledge: object }` → GO TO STEP 3
**Output on FAILURE**:
- `FAILURE(extraction_error)`: Cannot extract knowledge → skip (episodic memory preserved)
- `FAILURE(timeout)`: Extraction timeout → defer to background job

**Semantic Extraction Process**:
```
1. ANALYZE task input/output pair
2. IDENTIFY patterns that could apply to future tasks
3. EXTRACT generalizable knowledge:
   - "When doing X, approach Y works better than Z"
   - "For domain D, these tools are most effective"
   - "These prompts produce better results for task type T"
4. VALIDATE knowledge against existing knowledge (no contradictions)
5. STORE knowledge with confidence score
```

**Semantic Knowledge Schema**:
```json
{
  "knowledge_id": "uuid",
  "type": "semantic",
  "company_id": "uuid",
  "domain": "string",
  "knowledge_type": "enum(approach|tool_preference|prompt_pattern|pitfall|constraint)",
  "content": {
    "pattern": "string — the generalizable pattern",
    "context": "string — when this applies",
    "confidence": "number 0-1",
    "evidence_count": "number — how many episodes support this",
    "contradictions": "number — how many episodes contradict this"
  },
  "source_episodes": ["uuid — episodic memory IDs that generated this"],
  "created_at": "ISO8601",
  "last_updated": "ISO8601",
  "ttl_days": 365
}
```

---

### STEP 3: Vector Memory Indexing
**Actor**: Vector Memory Indexer
**Action**: Index episodic and semantic memory for similarity search
**Timeout**: 15s
**Input**: `{ memory_id: uuid, content: object, memory_type: enum }`
**Output on SUCCESS**: `{ memory_id: uuid, indexed: true, vector_id: string }` → END
**Output on FAILURE**:
- `FAILURE(index_error)`: Vector DB unavailable → retry x3 with 5s backoff → if all fail, memory stored but not searchable by similarity
- `FAILURE(embedding_error)`: Cannot generate embedding → use text-based search fallback

**Vector Indexing Process**:
```
1. GENERATE embedding from memory content
   - Use company-specific embedding model if available
   - Fall back to platform default model
2. STORE vector in vector database
   - Metadata: memory_id, type, company_id, domain, timestamp
3. VERIFY index is queryable
4. UPDATE memory record with vector_id
```

**Vector Memory Metadata**:
```json
{
  "vector_id": "string",
  "memory_id": "uuid",
  "company_id": "uuid",
  "memory_type": "enum(episodic|semantic|project|company)",
  "domain": "string",
  "tags": ["string"],
  "created_at": "ISO8601",
  "relevance_score": "number — updated on access"
}
```

---

### STEP 4: Project Memory Write
**Actor**: Project Memory Manager
**Action**: Store project-scoped knowledge that persists across project tasks
**Timeout**: 10s
**Input**: `{ project_id: uuid, company_id: uuid, knowledge: object }`
**Output on SUCCESS**: `{ project_memory_id: uuid, stored: true }` → END
**Output on FAILURE**:
- `FAILURE(write_error)`: Same as STEP 1 recovery

**Project Memory Schema**:
```json
{
  "project_memory_id": "uuid",
  "project_id": "uuid",
  "company_id": "uuid",
  "knowledge_type": "enum(architecture|decision|constraint|requirement|lesson_learned)",
  "content": {
    "topic": "string",
    "details": "string",
    "rationale": "string — why this decision was made",
    "alternatives_considered": ["string"],
    "related_documents": ["string — URLs or file references"]
  },
  "created_by_agent": "uuid",
  "created_at": "ISO8601",
  "last_accessed": "ISO8601"
}
```

---

### STEP 5: Company Memory Aggregation
**Actor**: Company Memory Aggregator
**Action**: Aggregate knowledge across projects into company-level memory
**Timeout**: 30s (background)
**Input**: `{ company_id: uuid, project_memories: [...], semantic_knowledge: [...] }`
**Output on SUCCESS**: `{ company_memory_id: uuid, aggregated: true }` → END
**Output on FAILURE**:
- `FAILURE(aggregation_error)`: Cannot aggregate → retry x2 with 10s backoff
- `FAILURE(conflict)`: Contradictory knowledge → flag for operator review

**Company Memory Schema**:
```json
{
  "company_memory_id": "uuid",
  "company_id": "uuid",
  "knowledge_type": "enum(policy|preference|capability|constraint|metric)",
  "content": {
    "topic": "string",
    "details": "string",
    "source_projects": ["uuid"],
    "confidence": "number 0-1",
    "last_validated": "ISO8601"
  },
  "created_at": "ISO8601",
  "last_updated": "ISO8601"
}
```

---

### STEP 6: User Memory Personalization
**Actor**: User Memory Personalizer
**Action**: Store user-specific preferences and personalize agent behavior
**Timeout**: 10s
**Input**: `{ user_id: uuid, company_id: uuid, preference: object }`
**Output on SUCCESS**: `{ user_memory_id: uuid, stored: true }` → END
**Output on FAILURE**:
- `FAILURE(write_error)`: Same as STEP 1 recovery

**User Memory Schema**:
```json
{
  "user_memory_id": "uuid",
  "user_id": "uuid",
  "company_id": "uuid",
  "preference_type": "enum(communication_style|report_format|priority|budget|deadline|tool_preference)",
  "content": {
    "preference": "string",
    "value": "any",
    "confidence": "number 0-1",
    "source": "enum(explicit|inferred|feedback)"
  },
  "created_at": "ISO8601",
  "last_updated": "ISO8601"
}
```

---

### STEP 7: Memory Read (Pre-Task Context)
**Actor**: Memory Reader
**Action**: Before agent executes task, retrieve relevant memory for context
**Timeout**: 15s
**Input**: `{ agent_id: uuid, task_id: uuid, task_description: string, company_id: uuid }`
**Output on SUCCESS**: `{ memory_context: { episodic: [...], semantic: [...], project: [...], company: [...] } }` → END (agent uses context)
**Output on FAILURE**:
- `FAILURE(read_error)`: Cannot read memory → proceed without memory context (degraded performance)
- `FAILURE(timeout)`: Read timeout → use cached context if available, else proceed empty

**Memory Retrieval Process**:
```
1. EXTRACT key concepts from task description
2. SEARCH vector memory for similar past episodes (top 5)
3. SEARCH semantic memory for applicable knowledge (top 10)
4. RETRIEVE project memory for current project (all recent)
5. RETRIEVE company memory for relevant policies (all active)
6. RETRIEVE user memory for operator preferences (all)
7. RANK by relevance and recency
8. COMPOSE memory context (max 4000 tokens)
9. RETURN to agent
```

**Memory Context Composition**:
```json
{
  "memory_context": {
    "similar_episodes": [
      {
        "episode_id": "uuid",
        "similarity_score": "number",
        "summary": "string",
        "outcome": "string",
        "lessons": ["string"]
      }
    ],
    "applicable_knowledge": [
      {
        "knowledge_id": "uuid",
        "pattern": "string",
        "confidence": "number",
        "source": "string"
      }
    ],
    "project_context": {
      "recent_decisions": ["string"],
      "current_constraints": ["string"],
      "architecture_notes": ["string"]
    },
    "company_policies": ["string"],
    "user_preferences": ["string"],
    "total_tokens_used": "number"
  }
}
```

---

### STEP 8: Memory Consolidation (Background)
**Actor**: Memory Consolidator
**Action**: Periodically merge, deduplicate, and compress memory to maintain quality and stay within quotas
**Timeout**: 300s (background job)
**Input**: `{ company_id: uuid, consolidation_type: enum(dedup|merge|prune|archive) }`
**Output on SUCCESS**: `{ company_id: uuid, consolidated: true, stats: { removed, merged, compressed } }` → END
**Output on FAILURE**:
- `FAILURE(consolidation_error)`: Cannot consolidate → retry x1, else skip until next cycle

**Consolidation Process**:
```
DEDUP:
  FIND memory entries with >90% similarity
  KEEP the newer/higher-quality entry
  MERGE evidence counts
  DELETE duplicates

MERGE:
  FIND semantic knowledge with overlapping patterns
  COMBINE into single knowledge entry
  INCREASE confidence (more evidence)
  UPDATE source_episodes list

PRUNE:
  FIND episodic memory older than TTL
  IF evidence_count == 0:
    ARCHIVE (move to cold storage)
  ELSE:
    KEEP (still has value)

ARCHIVE:
  MOVE old memory to cold storage
  KEEP summary in hot storage
  UPDATE access patterns
```

---

## State Transitions

```
[EVENT] → [CAPTURED] → [PROCESSING] → [STORED]
[STORED] → [INDEXING] → [INDEXED]
[STORED] → [EXTRACTING] → [EXTRACTED]
[STORED] → (older than TTL) → [CONSOLIDATING] → [CONSOLIDATED | ARCHIVED | PRUNED]
```

---

## Cleanup Inventory

| Resource | Created at step | Destroyed by | Destroy method |
|---|---|---|---|
| Episodic memories | Step 1 | Consolidation (TTL) | Archive or delete |
| Semantic knowledge | Step 2 | Consolidation (TTL) | Merge or archive |
| Vector embeddings | Step 3 | Consolidation | Delete from vector DB |
| Project memories | Step 4 | Project completion | Archive after 90d |
| Company memories | Step 5 | Manual (operator) | `DELETE FROM company_memory WHERE id = ?` |
| User memories | Step 6 | User deletion | Cascade delete |

---

## Test Cases

| Test | Trigger | Expected behavior |
|---|---|---|
| TC-01: Episodic write | Task completes | Memory stored within 10s |
| TC-02: Semantic extraction | After episodic write | Knowledge extracted within 30s |
| TC-03: Vector indexing | After memory write | Searchable within 15s |
| TC-04: Memory read | Before task execution | Relevant context retrieved within 15s |
| TC-05: Memory quota full | Company at memory limit | Consolidation triggered, space freed |
| TC-06: Dedup | Two similar memories | Older deduplicated, evidence merged |
| TC-07: Merge | Overlapping knowledge | Combined into single entry |
| TC-08: Prune | Memory older than TTL | Archived or deleted |
| TC-09: Read without memory | Memory service unavailable | Task proceeds with degraded context |
| TC-10: Write failure | Memory store unavailable | Retry x3, log warning |
| TC-11: Vector search | Similarity query | Returns top 5 most similar episodes |
| TC-12: Cross-project aggregation | Multiple projects | Company memory updated with cross-project insights |

---

## Assumptions

| # | Assumption | Where verified | Risk if wrong |
|---|---|---|---|
| A1 | Vector DB can handle 1M+ vectors per company | Not verified | Performance degrades at scale |
| A2 | Embedding quality is sufficient for similarity search | Not verified | Irrelevant memory retrieved |
| A3 | Memory TTLs are appropriate (90d episodic, 365d semantic) | Not verified | Too much/too little retained |
| A4 | 4000 token context limit is sufficient | Not verified | Important memory cut off |
| A5 | Consolidation can run without impacting read/write performance | Not verified | System slowdown during consolidation |

---

## Open Questions

- Should memory be encrypted at rest per company?
- How do we handle memory that becomes outdated (e.g., a tool is deprecated)?
- Should there be a "memory audit" capability for compliance?
- How do we handle memory conflicts between companies in a marketplace?
