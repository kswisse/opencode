# WORKFLOW-01: Goal Decomposition Pipeline

**Version**: 0.1
**Date**: 2026-07-28
**Author**: Workflow Architect
**Status**: Draft
**Implements**: Autonomous AI Workforce Platform — Goal Intake & Decomposition

---

## Overview

A user provides a single high-level objective (e.g., "Earn $10,000/month with affiliate marketing"). The Goal Decomposition Pipeline transforms this into a structured Project containing prioritized Task DAGs. The pipeline is orchestrated by the CEO Agent (one per company) and involves intent parsing, project decomposition, dependency identification, priority assignment, and timeline estimation.

---

## Actors

| Actor | Role in this workflow |
|---|---|
| Company Operator | Provides the goal via API/UI |
| API Gateway | Validates and routes the goal submission |
| Goal Parser Service | Extracts structured intent from natural language |
| CEO Agent (per company) | Decomposes parsed goal into projects and tasks |
| Planner Agent | Generates task DAGs with dependencies |
| Timeline Estimator | Assigns time estimates to tasks |
| Resource Assessor | Evaluates resource (token/budget) requirements |
| Project Store (DB) | Persists goal, project, and task records |
| Event Bus | Publishes goal lifecycle events for downstream workflows |

---

## Prerequisites

- Company exists in the system with active subscription
- CEO Agent is instantiated for the company
- Goal Parser Service is healthy and reachable
- Event Bus is operational
- Database is available and schema is current

---

## Trigger

```
POST /api/v1/companies/{company_id}/goals
Content-Type: application/json
Authorization: Bearer {operator_token}

{
  "goal_text": "Earn $10,000/month with affiliate marketing",
  "priority": "high",
  "constraints": {
    "max_budget_usd": 500,
    "deadline_days": 90,
    "allowed_verticals": ["marketing", "engineering"]
  }
}
```

---

## State Diagram

```
[SUBMITTED] → [PARSING] → [PARSED] → [DECOMPOSING] → [DECOMPOSED]
    ↓              ↓            ↓              ↓              ↓
 [REJECTED]   [PARSE_ERROR] [REJECTED]  [DECOMP_ERROR] [PLANNING]
                                                                  ↓
                                                             [PLANNED]
                                                                  ↓
                                                           [APPROVED/REVIEW]
                                                                  ↓
                                                            [ACTIVE]
                                                                  ↓
                                                           [COMPLETED/FAILED]
```

---

## Workflow Tree

### STEP 1: Goal Submission & Validation
**Actor**: API Gateway
**Action**: Validate request schema, authenticate operator, check company quota
**Timeout**: 5s
**Input**: `{ goal_text: string, priority: enum, constraints: object }`
**Output on SUCCESS**: `{ goal_id: uuid, status: "submitted" }` → GO TO STEP 2
**Output on FAILURE**:
- `FAILURE(validation_error)`: Missing required fields → return 400 + specific error message, no cleanup
- `FAILURE(auth_error)`: Invalid/expired token → return 401, no cleanup
- `FAILURE(quota_exceeded)`: Company has too many active goals → return 429 + retry-after header
- `FAILURE(rate_limited)`: Too many submissions → return 429 + retry-after header

**Observable states**:
- Customer sees: "Goal submitted" confirmation
- Operator sees: Goal in "submitted" state in dashboard
- Database: `goals.status = 'submitted'`, `goals.created_at = now()`
- Logs: `[api-gateway] goal submission received company_id=abc goal_text="Earn..."`

---

### STEP 2: Goal Parsing
**Actor**: Goal Parser Service
**Action**: Extract structured intent from natural language goal
**Timeout**: 30s
**Input**: `{ goal_id: uuid, goal_text: string, constraints: object }`
**Output on SUCCESS**: `{ goal_id: uuid, parsed_intent: { objective, domain, measurable_outcomes, success_criteria, estimated_scope } }` → GO TO STEP 3
**Output on FAILURE**:
- `FAILURE(parse_error)`: Cannot extract meaningful intent → set goal.status = 'rejected', return goal_id + "Could not parse goal. Please rephrase." (NO cleanup needed)
- `FAILURE(timeout)`: Parser service unresponsive → retry x2 with 10s backoff → if still failing, set goal.status = 'parse_failed', alert operator
- `FAILURE(service_unavailable)`: Parser service down → same as timeout path

**Observable states**:
- Customer sees: "Analyzing your goal..." (if async) or waits for response
- Operator sees: Goal in "parsing" state
- Database: `goals.status = 'parsing'`, `goals.parse_started_at = now()`
- Logs: `[goal-parser] parsing goal_id=abc text="Earn $10k..."`

**Parsed Intent Schema**:
```json
{
  "objective": "string — the core thing to achieve",
  "domain": "string — primary business domain (marketing, engineering, etc.)",
  "sub_domains": ["string — related domains"],
  "measurable_outcomes": [
    {
      "metric": "string — e.g., 'monthly_revenue'",
      "target_value": "number",
      "unit": "string — e.g., 'USD'"
    }
  ],
  "success_criteria": ["string — how we know it's achieved"],
  "estimated_scope": "enum(small|medium|large|enterprise)",
  "complexity_score": "number 1-10",
  "required_capabilities": ["string — agent capability types needed"]
}
```

---

### STEP 3: Goal Review & Acceptance
**Actor**: CEO Agent
**Action**: CEO Agent reviews parsed intent, validates feasibility against company context, may ask clarifying questions
**Timeout**: 120s
**Input**: `{ goal_id: uuid, parsed_intent: object, company_context: object }`
**Output on SUCCESS**: `{ goal_id: uuid, status: "accepted", clarifications_needed: [] }` → GO TO STEP 4
**Output on FAILURE**:
- `FAILURE(rejected_by_ceo)`: CEO determines goal is infeasible → set goal.status = 'rejected', include CEO's reasoning in goal.rejection_reason
- `FAILURE(clarifications_needed)`: CEO needs more info → set goal.status = 'awaiting_clarification', return questions to operator
- `FAILURE(timeout)`: CEO Agent unresponsive → retry x1 with 30s backoff → escalate to human operator

**Observable states**:
- Customer sees: "Our AI is reviewing your goal..." then either acceptance or clarification questions
- Operator sees: Goal in "parsing" → "review" state, CEO notes visible
- Database: `goals.status = 'review'`, `goals.ceo_notes = '...'`
- Logs: `[ceo-agent] reviewing goal_id=abc, complexity_score=7`

---

### STEP 4: Project Decomposition
**Actor**: CEO Agent
**Action**: Break down goal into projects, each containing task groups
**Timeout**: 180s
**Input**: `{ goal_id: uuid, parsed_intent: object, company_resources: object }`
**Output on SUCCESS**: `{ goal_id: uuid, projects: [{ project_id, name, description, task_groups: [...] }] }` → GO TO STEP 5
**Output on FAILURE**:
- `FAILURE(decomposition_error)`: Cannot decompose goal into viable projects → set goal.status = 'decomp_failed', alert operator with CEO's reasoning
- `FAILURE(resource_insufficient)`: Company lacks resources for any viable decomposition → set goal.status = 'resource_insufficient', return to operator with requirements
- `FAILURE(timeout)`: Decomposition takes too long → retry x1 with 60s backoff → if still failing, alert operator

**Observable states**:
- Customer sees: "Breaking your goal into actionable projects..."
- Operator sees: Goal in "decomposing" state, project count and names appear as created
- Database: `goals.status = 'decomposing'`, `projects` rows being inserted
- Logs: `[ceo-agent] decomposing goal_id=abc into N projects`

**Decomposition Output Schema**:
```json
{
  "projects": [
    {
      "project_id": "uuid",
      "name": "string",
      "description": "string",
      "objective": "string — what this project achieves toward the goal",
      "priority": "enum(critical|high|medium|low)",
      "estimated_duration_days": "number",
      "estimated_cost_usd": "number",
      "required_capabilities": ["string"],
      "task_groups": [
        {
          "group_name": "string",
          "tasks": ["string — task descriptions"],
          "depends_on": ["string — other group_names"]
        }
      ]
    }
  ],
  "total_estimated_duration_days": "number",
  "total_estimated_cost_usd": "number",
  "recommended_sequencing": "string — parallel | sequential | mixed"
}
```

---

### STEP 5: Task DAG Construction
**Actor**: Planner Agent
**Action**: For each project, generate a detailed task DAG with explicit dependencies, parallelizable waves, and checkpoints
**Timeout**: 120s
**Input**: `{ goal_id: uuid, projects: [{ project_id, task_groups }] }`
**Output on SUCCESS**: `{ goal_id: uuid, task_dags: [{ project_id, dag: { nodes, edges, waves } }] }` → GO TO STEP 6
**Output on FAILURE**:
- `FAILURE(dag_error)`: Circular dependencies detected or invalid DAG → set project.status = 'dag_error', log error, retry with simplified decomposition
- `FAILURE(timeout)`: DAG construction timeout → retry x2 with 30s backoff → alert operator

**Observable states**:
- Customer sees: "Creating task plan..."
- Operator sees: Task DAGs appearing in project view
- Database: `task_dags` rows being inserted, `tasks` rows being inserted
- Logs: `[planner-agent] constructing DAG for project_id=xyz, task_count=47`

**DAG Schema**:
```json
{
  "dag_id": "uuid",
  "project_id": "uuid",
  "nodes": [
    {
      "task_id": "uuid",
      "name": "string",
      "description": "string",
      "type": "enum(research|create|review|deploy|test|communicate)",
      "required_capabilities": ["string"],
      "estimated_duration_minutes": "number",
      "estimated_cost_tokens": "number",
      "checkpoint": "boolean — if true, results are persisted before proceeding",
      "retry_policy": { "max_retries": 3, "backoff_seconds": [5, 15, 60] }
    }
  ],
  "edges": [
    { "from": "task_id", "to": "task_id", "type": "enum(finish_to_start|data_dependency|conditional)" }
  ],
  "waves": [
    {
      "wave_number": "number",
      "task_ids": ["string — tasks that can run in parallel"],
      "depends_on_waves": ["number"]
    }
  ],
  "critical_path": ["string — ordered task_ids along critical path"]
}
```

---

### STEP 6: Priority & Timeline Assignment
**Actor**: Timeline Estimator + Resource Assessor
**Action**: Assign priorities, time estimates, and resource budgets to each task. Validate total against company constraints.
**Timeout**: 60s
**Input**: `{ goal_id: uuid, task_dags: [...], constraints: { max_budget_usd, deadline_days } }`
**Output on SUCCESS**: `{ goal_id: uuid, status: "planned", validated: true }` → GO TO STEP 7
**Output on FAILURE**:
- `FAILURE(budget_exceeded)`: Total estimated cost > max_budget_usd → set goal.status = 'budget_exceeded', return budget breakdown to operator
- `FAILURE(deadline_infeasible)`: Cannot complete within deadline → set goal.status = 'deadline_infeasible', return minimum timeline
- `FAILURE(timeout)`: Estimation timeout → use fallback heuristics, flag as "estimate_unverified"

**Observable states**:
- Customer sees: "Estimating timeline and resources..."
- Operator sees: Budget summary, timeline, and resource needs displayed
- Database: `goals.total_estimated_cost`, `goals.total_estimated_days`, `tasks.priority`, `tasks.estimated_tokens`
- Logs: `[resource-assessor] goal_id=abc total_est=$450, deadline_ok=true`

---

### STEP 7: Goal Approval & Activation
**Actor**: Company Operator (human) + System
**Action**: Present plan to operator for approval. On approval, activate goal and trigger Agent Layer workflows.
**Timeout**: None (waits for human)
**Input**: `{ goal_id: uuid, plan_summary: { projects, total_cost, total_days, risk_flags } }`
**Output on SUCCESS**: `{ goal_id: uuid, status: "active", activated_at: timestamp }` → GO TO STEP 8
**Output on FAILURE**:
- `FAILURE(rejected_by_operator)`: Operator declines plan → set goal.status = 'rejected_by_operator', return to STEP 4 with operator feedback
- `FAILURE(expired)`: Operator doesn't respond within SLA (e.g., 7 days) → send reminder, then archive goal after 14 days

**Observable states**:
- Customer sees: Plan summary with approve/reject buttons
- Operator sees: Full plan with cost breakdown, timeline, risk assessment
- Database: `goals.status = 'approved'` → `goals.status = 'active'`
- Logs: `[system] goal_id=abc approved by operator, activating`

---

### STEP 8: Downstream Workflow Trigger
**Actor**: Event Bus
**Action**: Publish events that trigger Agent Lifecycle, Task Execution, and Resource Allocation workflows
**Timeout**: 5s
**Input**: `{ goal_id: uuid, projects: [...], task_dags: [...] }`
**Output on SUCCESS**: Events published → workflow complete
**Output on FAILURE**:
- `FAILURE(event_publish_error)`: Event Bus unavailable → retry x3 with exponential backoff → if all fail, alert operator, goal remains active but downstream workflows delayed

**Observable states**:
- Customer sees: "Goal activated! AI workforce is assembling..."
- Operator sees: Goal in "active" state, agents beginning to be created
- Database: `goals.status = 'active'`
- Logs: `[event-bus] published GoalActivated event for goal_id=abc`

**Events Published**:
```json
{
  "event_type": "GoalActivated",
  "payload": {
    "goal_id": "uuid",
    "company_id": "uuid",
    "projects": ["uuid — list of project_ids"],
    "task_dags": ["uuid — list of dag_ids"]
  },
  "timestamp": "ISO8601"
}
```

---

## ABORT_CLEANUP: Goal Failure Cleanup
**Triggered by**: Any step failure that creates partial state
**Actions** (in order):
1. Delete any tasks created for this goal (`DELETE FROM tasks WHERE goal_id = ?`)
2. Delete any task DAGs (`DELETE FROM task_dags WHERE goal_id = ?`)
3. Delete any projects (`DELETE FROM projects WHERE goal_id = ?`)
4. Set goal.status = 'failed', goal.error = last error message
5. Publish GoalFailed event for cleanup coordination
6. Notify operator via configured channel

**What customer sees**: Goal shown as "Failed" with error reason and option to retry
**What operator sees**: Goal in failed state with full error log and retry button

---

## State Transitions

```
[SUBMITTED] → (step 2 succeeds) → [PARSING]
[SUBMITTED] → (validation fails) → [REJECTED]
[PARSING] → (step 3 succeeds) → [PARSED]
[PARSING] → (parse fails) → [PARSE_ERROR] → [REJECTED]
[PARSED] → (step 4 succeeds) → [DECOMPOSING]
[PARSED] → (CEO rejects) → [REJECTED]
[DECOMPOSING] → (step 5 succeeds) → [DECOMPOSED]
[DECOMPOSING] → (decomp fails) → [DECOMP_ERROR] → [FAILED]
[DECOMPOSED] → (step 6 succeeds) → [PLANNING]
[PLANNING] → (step 7 succeeds) → [PLANNED]
[PLANNING] → (budget/deadline fail) → [PLANNING_FAILED] → [FAILED]
[PLANNED] → (operator approves) → [ACTIVE]
[PLANNED] → (operator rejects) → [REJECTED] → (restart) → [DECOMPOSING]
[PLANNED] → (7 days no response) → [EXPIRED] → [ARCHIVED]
[ACTIVE] → (all projects complete) → [COMPLETED]
[ACTIVE] → (unrecoverable failure) → [FAILED]
```

---

## Handoff Contracts

### API Gateway → Goal Parser Service
**Endpoint**: `POST /internal/goals/parse`
**Payload**:
```json
{
  "goal_id": "uuid",
  "goal_text": "string",
  "constraints": {
    "max_budget_usd": "number",
    "deadline_days": "number",
    "allowed_verticals": ["string"]
  },
  "company_context": {
    "company_id": "uuid",
    "industry": "string",
    "existing_capabilities": ["string"],
    "budget_remaining_usd": "number"
  }
}
```
**Success response**:
```json
{
  "ok": true,
  "parsed_intent": {
    "objective": "string",
    "domain": "string",
    "sub_domains": ["string"],
    "measurable_outcomes": [{"metric": "string", "target_value": "number", "unit": "string"}],
    "success_criteria": ["string"],
    "estimated_scope": "string",
    "complexity_score": "number",
    "required_capabilities": ["string"]
  }
}
```
**Failure response**:
```json
{
  "ok": false,
  "error": "string",
  "code": "PARSE_ERROR | TIMEOUT | SERVICE_UNAVAILABLE",
  "retryable": true
}
```
**Timeout**: 30s
**On FAILURE**: Retry x2 with 10s backoff, then escalate

---

### CEO Agent → Planner Agent
**Endpoint**: `POST /internal/planning/construct-dag`
**Payload**:
```json
{
  "project_id": "uuid",
  "task_groups": [
    {
      "group_name": "string",
      "tasks": ["string — task descriptions"],
      "depends_on": ["string — group names"]
    }
  ],
  "required_capabilities": ["string"],
  "company_capabilities": ["string — what agents exist"]
}
```
**Success response**:
```json
{
  "ok": true,
  "dag": {
    "dag_id": "uuid",
    "nodes": [{"task_id": "uuid", "name": "string", "type": "string", "dependencies": ["uuid"]}],
    "edges": [{"from": "uuid", "to": "uuid", "type": "string"}],
    "waves": [{"wave_number": "number", "task_ids": ["uuid"]}],
    "critical_path": ["uuid"]
  }
}
```
**Failure response**:
```json
{
  "ok": false,
  "error": "string",
  "code": "DAG_ERROR | CIRCULAR_DEPENDENCY | TIMEOUT",
  "retryable": true
}
```
**Timeout**: 120s

---

### System → Event Bus
**Event**: `GoalActivated`
**Payload**:
```json
{
  "event_id": "uuid",
  "event_type": "GoalActivated",
  "version": "1.0",
  "company_id": "uuid",
  "goal_id": "uuid",
  "projects": [{"project_id": "uuid", "name": "string", "dag_id": "uuid"}],
  "total_estimated_cost_usd": "number",
  "total_estimated_days": "number",
  "timestamp": "ISO8601"
}
```
**Success response**: Event accepted (fire-and-forget, but with delivery guarantee)
**Failure response**: Publish timeout → retry x3 with exponential backoff

---

## Cleanup Inventory

| Resource | Created at step | Destroyed by | Destroy method |
|---|---|---|---|
| Goal record | Step 1 | ABORT_CLEANUP | `DELETE FROM goals WHERE goal_id = ?` |
| Parsed intent | Step 2 | ABORT_CLEANUP | Goal record cascade |
| Projects | Step 4 | ABORT_CLEANUP | `DELETE FROM projects WHERE goal_id = ?` |
| Task DAGs | Step 5 | ABORT_CLEANUP | `DELETE FROM task_dags WHERE goal_id = ?` |
| Tasks | Step 5 | ABORT_CLEANUP | `DELETE FROM tasks WHERE goal_id = ?` |
| Event subscriptions | Step 8 | ABORT_CLEANUP | Unsubscribe from Event Bus |

---

## Test Cases

| Test | Trigger | Expected behavior |
|---|---|---|
| TC-01: Happy path | Valid goal, all services healthy | Goal parsed, decomposed, planned, approved within 10min |
| TC-02: Parse failure | Ambiguous goal text ("do stuff") | Goal rejected with clear message |
| TC-03: CEO rejection | Infeasible goal ("become president tomorrow") | Goal rejected with CEO reasoning |
| TC-04: Budget exceeded | Goal requires $5000, budget is $500 | Goal marked budget_exceeded, alternatives suggested |
| TC-05: Deadline infeasible | 90-day goal needs 180 days minimum | Goal marked deadline_infeasible, minimum timeline returned |
| TC-06: Parser timeout | Goal Parser Service unresponsive | Retry x2, then mark parse_failed |
| TC-07: Planner timeout | Planner Agent unresponsive | Retry x2, then use fallback heuristics |
| TC-08: Operator rejection | Operator rejects plan | Return to decomposition with feedback |
| TC-09: No operator response | Operator doesn't approve within 7 days | Reminder sent, archived after 14 days |
| TC-10: Event Bus failure | Event Bus unavailable | Retry x3, alert operator, goal active but downstream delayed |
| TC-11: Partial cleanup | Goal fails after projects created | All projects, DAGs, tasks cleaned up |
| TC-12: Concurrent goals | Multiple goals submitted simultaneously | Each processed independently, quota enforced |

---

## Assumptions

| # | Assumption | Where verified | Risk if wrong |
|---|---|---|---|
| A1 | CEO Agent can receive and process company context | Not verified — greenfield | Decomposition lacks context, produces generic plans |
| A2 | Goal Parser Service has sufficient NLU capability | Not verified | Parsing quality degrades, more rejections |
| A3 | Planner Agent can handle DAGs up to 500 nodes | Not verified | Large goals fail decomposition |
| A4 | Event Bus provides at-least-once delivery | Not verified | Downstream workflows may miss events |
| A5 | Company context (industry, capabilities) is available at parse time | Not verified | Parser lacks context for better parsing |

---

## Open Questions

- Should the CEO Agent have a personality/configurable risk tolerance per company?
- What happens if a goal's projects span multiple companies in a consortium?
- Should there be a "goal versioning" mechanism when decomposition changes?
- How does the system handle goals that are time-sensitive (e.g., "respond to this news within 24 hours")?

---

## Spec vs Reality Audit Log

| Date | Finding | Action taken |
|---|---|---|
| 2026-07-28 | Initial spec created | — |
