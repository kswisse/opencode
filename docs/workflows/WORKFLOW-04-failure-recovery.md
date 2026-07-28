# WORKFLOW-04: Failure Recovery Flows

**Version**: 0.1
**Date**: 2026-07-28
**Author**: Workflow Architect
**Status**: Draft
**Implements**: Autonomous AI Workforce Platform — Agent Failure, Task Timeout, Bad Output, Cascading Failures, Dead Letter Queue

---

## Overview

Failure Recovery handles everything that goes wrong: agent crashes, task timeouts, bad output detection, cascading failures across dependent tasks, dead letter queue processing, and agent resurrection. The goal is maximum automatic recovery with minimal human intervention.

---

## Actors

| Actor | Role in this workflow |
|---|---|
| Failure Detector | Monitors agent health, task progress, output quality |
| Recovery Orchestrator | Coordinates recovery actions across the system |
| Agent Resurrector | Restores failed agents from checkpoints |
| Dead Letter Processor | Handles permanently failed tasks |
| Circuit Breaker | Prevents cascading failures by isolating failing components |
| Alert System | Notifies operators of unrecoverable failures |
| Event Bus | Publishes failure and recovery events |

---

## Prerequisites

- Agent health monitoring is active
- Task output quality validators are configured
- Checkpoint system is operational (WORKFLOW-03)
- Alert channels are configured

---

## Trigger

Failure Recovery is triggered by:
1. Agent health check failure
2. Task timeout exceeded
3. Output quality score below threshold
4. Circuit breaker tripping
5. Dead letter queue entry

---

## State Diagram

```
[FAILURE_DETECTED] → [CLASSIFYING] → [CLASSIFIED]
                            ↓
                    [TRANSIENT | PERMANENT | CASCADING]
                            ↓
                    [RECOVERING] → [RECOVERED]
                            ↓
                    [RECOVERY_FAILED] → [ESCALATED]
                            ↓
                    [DEAD_LETTER] → [MANUAL_REVIEW]
```

---

## Workflow Tree

### STEP 1: Failure Detection
**Actor**: Failure Detector
**Action**: Detect failure from multiple signals
**Timeout**: Continuous monitoring
**Input**: Various signals (health check, timeout, quality score, error rate)
**Output**: `{ failure_id: uuid, failure_type: enum, severity: enum, source: object }` → GO TO STEP 2

**Detection Sources**:

| Signal | Detection Method | Threshold |
|---|---|---|
| Agent crash | Health check every 10s | 3 consecutive failures |
| Task timeout | Elapsed time > task.timeout | Single occurrence |
| Bad output | Quality score < 0.3 | Single occurrence |
| Token exhaustion | tokens_used >= token_budget | Single occurrence |
| Tool failure | Tool returns error | 2 consecutive failures |
| Cascading failure | >50% tasks in wave failing | Single occurrence |

**Observable states**:
- Customer sees: "An issue was detected, attempting recovery..."
- Operator sees: Failure alert with details
- Database: `failures` row inserted
- Logs: `[failure-detector] failure detected: type=agent_crash, agent_id=pqr`

---

### STEP 2: Failure Classification
**Actor**: Recovery Orchestrator
**Action**: Classify failure type, determine severity, select recovery strategy
**Timeout**: 10s
**Input**: `{ failure_id: uuid, failure_type: enum, source: object }`
**Output on SUCCESS**: `{ failure_id: uuid, classification: object, recovery_strategy: enum }` → GO TO STEP 3

**Classification Matrix**:

| Failure Type | Severity | Recovery Strategy | Retry? |
|---|---|---|---|
| Agent crash (transient) | Medium | Agent resurrection | Yes (2x) |
| Agent crash (permanent) | High | Agent replacement | Yes (1x) |
| Task timeout (first) | Low | Retry with same agent | Yes (2x) |
| Task timeout (repeated) | High | Retry with new agent | Yes (1x) |
| Bad output (quality) | Medium | Retry with adjusted params | Yes (3x) |
| Bad output (format) | Low | Retry with format correction | Yes (2x) |
| Token exhaustion | High | Pause task, request more budget | No |
| Tool failure (transient) | Low | Retry tool call | Yes (3x) |
| Tool failure (permanent) | Medium | Use alternative tool | No |
| Cascading failure | Critical | Circuit break + manual review | No |

---

### STEP 3: Transient Failure Recovery
**Actor**: Recovery Orchestrator
**Action**: For transient failures, retry the operation with backoff
**Timeout**: Task timeout * 3 (total retry budget)
**Input**: `{ failure_id: uuid, task_id: uuid, agent_id: uuid, retry_count: number }`
**Output on SUCCESS**: `{ failure_id: uuid, status: "recovered", recovered_by: "retry" }` → END
**Output on FAILURE**:
- `FAILURE(retry_exhausted)`: All retries used → escalate to STEP 4 (permanent failure)
- `FAILURE(retry_too_slow)`: Recovery would exceed deadline → escalate to STEP 4

**Observable states**:
- Customer sees: "Retrying [task]... (attempt [N] of [max])"
- Operator sees: Retry count incrementing, backoff timer
- Database: `tasks.retry_count = N`, `tasks.status = 'retrying'`
- Logs: `[recovery] retrying task_id=stu, attempt=2/3, backoff=15s`

**Retry Backoff Schedule**:
```
Attempt 1: immediate
Attempt 2: 5s
Attempt 3: 15s
Attempt 4: 60s
Attempt 5: 300s (max backoff)
```

---

### STEP 4: Permanent Failure Handling
**Actor**: Recovery Orchestrator
**Action**: For permanent failures, replace agent or skip task, update DAG
**Timeout**: 30s
**Input**: `{ failure_id: uuid, task_id: uuid, agent_id: uuid, failure_type: enum }`
**Output on SUCCESS**: `{ failure_id: uuid, status: "handled", action: "agent_replaced" | "task_skipped" }` → GO TO STEP 5
**Output on FAILURE**:
- `FAILURE(replacement_failed)`: Cannot create replacement agent → skip task, alert operator
- `FAILURE(skip_blocked)`: Task is critical, cannot skip → abort DAG

**Observable states**:
- Customer sees: "Agent replacement being prepared for [task]..."
- Operator sees: Agent marked as permanently failed, replacement being created
- Database: `agents.status = 'permanently_failed'`, new agent being created
- Logs: `[recovery] permanent failure for agent_id=pqr, creating replacement`

---

### STEP 5: Agent Resurrection
**Actor**: Agent Resurrector
**Action**: Restore failed agent from last checkpoint, preserving in-flight work
**Timeout**: 60s
**Input**: `{ agent_id: uuid, checkpoint_id: uuid, task_id: uuid }`
**Output on SUCCESS**: `{ agent_id: uuid, status: "resurrected", task_state: "restored" }` → return to execution
**Output on FAILURE**:
- `FAILURE(checkpoint_corrupt)`: Checkpoint unusable → create new agent, re-execute from last checkpoint
- `FAILURE(resurrection_timeout)`: Cannot restore in time → create new agent, re-execute

**Observable states**:
- Customer sees: "Restoring agent from checkpoint..."
- Operator sees: Agent being restored, checkpoint data visible
- Database: `agents.status = 'resurrecting'`, then `'executing'`
- Logs: `[resurrector] restoring agent_id=pqr from checkpoint_id=xyz`

**Resurrection Process**:
1. Load agent checkpoint (prompts, tools, state, in-progress data)
2. Restore agent execution context
3. Replay any events since checkpoint (event sourcing)
4. Resume task execution from checkpoint
5. Verify restored state matches expected state

---

### STEP 6: Cascading Failure Prevention
**Actor**: Circuit Breaker
**Action**: When failure rate exceeds threshold, trip circuit breaker to prevent cascade
**Timeout**: Continuous
**Input**: `{ component_id: uuid, failure_rate: number, threshold: number }`
**Output**: Circuit state change

**Circuit Breaker States**:
```
CLOSED (normal) → failure_rate > threshold → OPEN (blocking)
OPEN → timeout (30s) → HALF_OPEN (testing)
HALF_OPEN → success → CLOSED
HALF_OPEN → failure → OPEN
```

**Observable states**:
- Customer sees: "System stabilizing, some tasks paused..."
- Operator sees: Circuit breaker status, affected components
- Database: `circuit_breakers` state updated
- Logs: `[circuit-breaker] OPENED for component=agent-pool-abc, failure_rate=0.6`

**Circuit Breaker Actions**:
```
IF circuit.OPEN:
  BLOCK all new task dispatches to affected component
  PAUSE all running tasks in affected component
  ALERT operator
  WAIT for timeout
ELIF circuit.HALF_OPEN:
  ALLOW one test task through
  IF test succeeds → CLOSE circuit
  IF test fails → OPEN circuit, increase timeout
```

---

### STEP 7: Dead Letter Queue Processing
**Actor**: Dead Letter Processor
**Action**: Handle tasks that cannot be recovered automatically
**Timeout**: 30s
**Input**: `{ task_id: uuid, failure_history: [...], dag_id: uuid }`
**Output on SUCCESS**: `{ task_id: uuid, status: "processed", action: "manual_review" | "skipped" | "simplified" }`

**Dead Letter Processing Strategies**:
```
1. MANUAL_REVIEW:
   Task flagged for operator review
   Operator can: retry, modify, skip, or provide manual input
   
2. SIMPLIFIED_RETRY:
   Task decomposed into smaller sub-tasks
   Sub-tasks retried with simpler requirements
   
3. SKIP_WITH_FALLBACK:
   Task skipped, fallback output used (default/empty/partial)
   Downstream tasks adapt to missing input
   
4. PERMANENT_SKIP:
   Task permanently skipped
   DAG updated to remove dependency
```

**Observable states**:
- Customer sees: "Some tasks require manual review" (if manual_review)
- Operator sees: Dead letter queue with task details and recovery options
- Database: `dead_letter_queue` row inserted
- Logs: `[dead-letter] task_id=uvw added to DLQ, reason=all_retries_exhausted`

---

### STEP 8: Alert Escalation
**Actor**: Alert System
**Action**: Notify operators of unrecoverable failures, provide actionable information
**Timeout**: 5s
**Input**: `{ failure_id: uuid, severity: enum, details: object, suggested_actions: [...] }`
**Output**: Alert delivered

**Alert Levels**:
| Level | Trigger | Channel | Response SLA |
|---|---|---|---|
| Info | Transient failure, auto-recovered | Dashboard only | None |
| Warning | Repeated failures, approaching threshold | Dashboard + email | 4h |
| Error | Permanent failure, task skipped | Dashboard + email + Slack | 1h |
| Critical | Cascading failure, DAG abort | Dashboard + email + Slack + SMS | 15min |

**Alert Payload**:
```json
{
  "alert_id": "uuid",
  "level": "enum(info|warning|error|critical)",
  "title": "string — concise failure summary",
  "description": "string — detailed failure information",
  "affected_components": ["string"],
  "failure_history": [{"timestamp": "ISO8601", "event": "string"}],
  "suggested_actions": ["string — what the operator should do"],
  "runbook_url": "string — link to relevant documentation"
}
```

---

### STEP 9: Post-Recovery Learning
**Actor**: Memory System (background)
**Action**: After recovery, analyze failure patterns, update agent memory, improve future prevention
**Timeout**: Background process
**Input**: `{ failure_id: uuid, recovery_actions: [...], outcome: "recovered" | "failed" }`

**Learning Actions**:
1. Record failure pattern in company's failure knowledge base
2. Update agent memory with what went wrong
3. If same failure occurs 3+ times → suggest system-level fix
4. Update agent performance scores (penalize for causing failures)
5. If failure was tool-related → update tool reliability metrics

---

## State Transitions

```
[FAILURE_DETECTED] → [CLASSIFYING] → [CLASSIFIED]
[CLASSIFIED] → [TRANSIENT] → [RECOVERING] → [RECOVERED]
[CLASSIFIED] → [PERMANENT] → [RECOVERING] → [RECOVERED | RECOVERY_FAILED]
[CLASSIFIED] → [CASCADING] → [CIRCUIT_BREAK] → [MANUAL_REVIEW]
[RECOVERY_FAILED] → [ESCALATED] → [DEAD_LETTER] → [MANUAL_REVIEW]
[RECOVERED] → (end)
[MANUAL_REVIEW] → [RESOLVED | PERMANENTLY_FAILED]
```

---

## Handoff Contracts

### Failure Detector → Recovery Orchestrator
**Endpoint**: `POST /internal/recovery/classify`
**Payload**:
```json
{
  "failure_id": "uuid",
  "failure_type": "enum(agent_crash|timeout|bad_output|token_exhaustion|tool_error|cascading)",
  "source": {
    "type": "enum(agent|task|dag)",
    "id": "uuid",
    "context": "object"
  },
  "signals": {"health_checks_failed": "number", "error_messages": ["string"]}
}
```
**Success response**:
```json
{
  "ok": true,
  "classification": {
    "severity": "enum(low|medium|high|critical)",
    "is_transient": "boolean",
    "recovery_strategy": "enum(retry|replace|skip|circuit_break|manual)"
  }
}
```
**Timeout**: 10s

### Recovery Orchestrator → Agent Resurrector
**Endpoint**: `POST /internal/recovery/resurrect`
**Payload**:
```json
{
  "agent_id": "uuid",
  "checkpoint_id": "uuid",
  "task_id": "uuid",
  "restore_from": "enum(checkpoint|scratch)"
}
```
**Success response**:
```json
{
  "ok": true,
  "agent_id": "uuid",
  "status": "resurrected",
  "task_state_restored": "boolean"
}
```
**Timeout**: 60s

### Circuit Breaker → DAG Scheduler
**Event**: `CircuitBreakerTripped`
**Payload**:
```json
{
  "component_id": "uuid",
  "component_type": "string",
  "state": "enum(open|half_open|closed)",
  "affected_dags": ["uuid"],
  "blocked_tasks": ["uuid"],
  "retry_after_seconds": "number"
}
```

---

## Cleanup Inventory

| Resource | Created at step | Destroyed by | Destroy method |
|---|---|---|---|
| Failure records | Step 1 | Retention policy (30d) | `DELETE FROM failures WHERE created_at < now() - 30d` |
| Dead letter entries | Step 7 | Manual resolution | `DELETE FROM dead_letter_queue WHERE task_id = ?` |
| Circuit breaker state | Step 6 | Automatic (timeout) | State transitions |
| Recovery logs | Step 9 | Retention policy (90d) | `DELETE FROM recovery_logs WHERE created_at < now() - 90d` |

---

## Test Cases

| Test | Trigger | Expected behavior |
|---|---|---|
| TC-01: Agent crash recovery | Agent process dies | Agent resurrected from checkpoint, task resumes |
| TC-02: Task timeout retry | Agent exceeds timeout | Task retried with new agent |
| TC-03: Bad output retry | Quality score < 0.3 | Task retried with adjusted parameters |
| TC-04: Retry exhaustion | Task fails 3 times | Moved to dead letter queue |
| TC-05: Cascading failure | >50% tasks failing | Circuit breaker trips, execution paused |
| TC-06: Circuit breaker recovery | Component recovers | Circuit closes, execution resumes |
| TC-07: Dead letter manual review | Operator reviews DLQ task | Operator can retry, modify, or skip |
| TC-08: Token exhaustion | Agent runs out of tokens | Task paused, operator notified for budget increase |
| TC-09: Tool failure fallback | Primary tool unavailable | Alternative tool used |
| TC-10: Checkpoint corruption | Checkpoint unreadable | New agent created, re-execution from last good checkpoint |
| TC-11: Concurrent failures | Multiple agents fail simultaneously | Each handled independently, no cross-contamination |
| TC-12: Alert escalation | Critical failure unrecovered | SMS alert sent within 15min |

---

## Assumptions

| # | Assumption | Where verified | Risk if wrong |
|---|---|---|---|
| A1 | Checkpoint system provides consistent snapshots | Not verified | Resurrection restores inconsistent state |
| A2 | Circuit breaker thresholds are tunable per component | Not verified | One-size-fits-all thresholds may be wrong |
| A3 | Dead letter tasks can always be manually resolved | Not verified | Some failures may be truly unrecoverable |
| A4 | Alert channels are reliable and monitored | Not missed alerts |
| A5 | Post-recovery learning actually improves future performance | Not verified | Same failures repeat |

---

## Open Questions

- Should there be a "chaos engineering" mode to intentionally inject failures for testing?
- How do we handle failures that span multiple companies (shared infrastructure)?
- Should dead letter tasks have an expiration (auto-skip after X days)?
- How do we prioritize recovery when multiple failures occur simultaneously?
