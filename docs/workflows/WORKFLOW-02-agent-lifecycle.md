# WORKFLOW-02: Agent Lifecycle Workflows

**Version**: 0.1
**Date**: 2026-07-28
**Author**: Workflow Architect
**Status**: Draft
**Implements**: Autonomous AI Workforce Platform — Agent Creation, Assignment, Execution, Evaluation, Destruction

---

## Overview

Agent Lifecycle manages the complete life of an AI worker: from template selection through creation, skill calibration, task assignment, performance tracking, reuse evaluation, and graceful destruction. The lifecycle is driven by Goal Decomposition outputs and Task Execution demands.

---

## Actors

| Actor | Role in this workflow |
|---|---|
| Agent Factory | Creates agent instances from templates |
| Agent Registry | Tracks all living agents, their states, capabilities |
| Skill Calibrator | Tunes agent prompts, tools, and parameters |
| Task Executor | Assigns agents to tasks, monitors execution |
| Performance Evaluator | Scores agent output quality post-task |
| Memory System | Persists agent learning and state |
| Resource Manager | Allocates tokens/budget to agents |
| Event Bus | Publishes agent lifecycle events |

---

## Prerequisites

- Agent templates exist in the template registry
- Company has available agent quota
- Skill Calibrator service is healthy
- Memory System is operational

---

## Trigger

Agent creation is triggered by:
1. Goal Activated event → CEO Agent determines agents needed
2. Task Assignment demand → existing agent pool insufficient
3. Operator manual creation via API

---

## State Diagram

```
[TEMPLATE_SELECTED] → [CREATING] → [CREATED] → [CALIBRATING] → [CALIBRATED]
        ↓                              ↓              ↓              ↓
   [SELECTION_FAILED]           [CREATION_FAILED] [CAL_ERROR]  [IDLE]
                                                                        ↓
                                                                    [ASSIGNED]
                                                                        ↓
                                                                  [EXECUTING]
                                                                        ↓
                                                                  [EVALUATING]
                                                                        ↓
                                                              [COMPLETED|FAILED]
                                                                        ↓
                                                                    [IDLE] (reuse)
                                                                        ↓
                                                                  [DESTROYING]
                                                                        ↓
                                                                    [DESTROYED]
```

---

## Workflow Tree

### STEP 1: Agent Need Detection
**Actor**: Agent Factory (triggered by GoalActivated event or TaskDemand event)
**Action**: Determine what type of agent is needed, check if existing idle agent can be reused
**Timeout**: 10s
**Input**: `{ required_capabilities: [...], company_id: uuid, task_context: object }`
**Output on SUCCESS**: `{ agent_id: uuid, action: "created" | "reused", template_used: string }` → GO TO STEP 2
**Output on FAILURE**:
- `FAILURE(quota_exceeded)`: Company at max agent count → return error to GoalDecomposition
- `FAILURE(no_template)`: No template matches required capabilities → return error, suggest custom creation
- `FAILURE(reuse_eval_error)`: Cannot determine if reuse is possible → default to creating new agent

**Observable states**:
- Customer sees: "Creating specialist agent for [task type]..."
- Operator sees: Agent factory processing, new agent appearing in agent list
- Database: `agents.status = 'creating'`, `agents.template = '...'`
- Logs: `[agent-factory] need detected for company_id=abc, capabilities=['research', 'writing']`

**Reuse Decision Logic**:
```
IF exists agent WHERE:
  agent.company_id = company_id
  agent.status = 'idle'
  agent.capabilities >= required_capabilities
  agent.last_active < 24h ago
  agent.performance_score >= 0.7
THEN
  reuse agent (skip to STEP 4)
ELSE
  create new agent (continue to STEP 2)
```

---

### STEP 2: Template Selection & Agent Instantiation
**Actor**: Agent Factory
**Action**: Select best matching template, instantiate agent with configuration
**Timeout**: 30s
**Input**: `{ template_id: uuid, company_id: uuid, task_context: object, overrides: object }`
**Output on SUCCESS**: `{ agent_id: uuid, status: "created", capabilities: [...] }` → GO TO STEP 3
**Output on FAILURE**:
- `FAILURE(template_not_found)`: Template doesn't exist → return 404 + list available templates
- `FAILURE(instantiation_error)`: Template has invalid configuration → return 400 + error details
- `FAILURE(resource_exhausted)`: Cannot allocate compute/memory for agent → retry x2 with 10s backoff → alert operator
- `FAILURE(timeout)`: Instantiation timeout → retry x1 with 15s backoff

**Observable states**:
- Customer sees: "Assembling your [role] agent..."
- Operator sees: New agent in "creating" state with template info
- Database: `agents` row inserted with status='created'
- Logs: `[agent-factory] instantiating agent_id=def from template=marketing-research`

**Template Schema**:
```json
{
  "template_id": "uuid",
  "name": "string",
  "role": "string — e.g., 'research_analyst', 'content_writer', 'code_reviewer'",
  "capabilities": ["string"],
  "base_model": "string",
  "system_prompt_template": "string",
  "tools": [{"name": "string", "config": "object"}],
  "default_params": {
    "temperature": "number",
    "max_tokens": "number",
    "timeout_seconds": "number"
  },
  "resource_profile": {
    "min_tokens_per_task": "number",
    "avg_tokens_per_task": "number",
    "max_concurrent_tasks": "number"
  }
}
```

---

### STEP 3: Skill Calibration
**Actor**: Skill Calibrator
**Action**: Fine-tune agent's prompts, tools, and parameters based on company context and task requirements
**Timeout**: 60s
**Input**: `{ agent_id: uuid, template: object, company_context: object, task_context: object }`
**Output on SUCCESS**: `{ agent_id: uuid, status: "calibrated", calibrated_config: object }` → GO TO STEP 4
**Output on FAILURE**:
- `FAILURE(calibration_error)`: Cannot optimize for this context → use template defaults, flag as "unoptimized"
- `FAILURE(timeout)`: Calibration timeout → use template defaults, flag as "unoptimized"
- `FAILURE(model_unavailable)`: Base model not accessible → retry x2 with 30s backoff → if still failing, mark agent as "unavailable"

**Observable states**:
- Customer sees: "Tuning your agent's expertise..."
- Operator sees: Agent in "calibrating" state
- Database: `agents.status = 'calibrating'`, `agents.calibration_started_at = now()`
- Logs: `[skill-calibrator] calibrating agent_id=def for domain='marketing'`

**Calibration Process**:
1. Analyze company's historical task outputs in this domain
2. Adjust system prompt to include company-specific conventions
3. Optimize tool selection based on available integrations
4. Set temperature/params based on task type (creative vs analytical)
5. Set token budget based on company's budget allocation

---

### STEP 4: Assignment to Task
**Actor**: Task Executor
**Action**: Assign calibrated agent to a task from the DAG
**Timeout**: 10s
**Input**: `{ agent_id: uuid, task_id: uuid, dag_id: uuid, priority: enum }`
**Output on SUCCESS**: `{ agent_id: uuid, task_id: uuid, status: "assigned", assigned_at: timestamp }` → GO TO STEP 5
**Output on FAILURE**:
- `FAILURE(agent_busy)`: Agent already at max concurrent tasks → return to pool, try next agent
- `FAILURE(task_not_found)`: Task already assigned or completed → skip, try next task
- `FAILURE(capability_mismatch)`: Agent capabilities don't match task requirements → return to pool
- `FAILURE(conflict)`: Agent already assigned to conflicting task → return to pool

**Observable states**:
- Customer sees: "Agent [name] is now working on [task]..."
- Operator sees: Agent status changes to "assigned", task shows assigned agent
- Database: `agents.status = 'assigned'`, `tasks.assigned_agent_id = agent_id`
- Logs: `[task-executor] assigned agent_id=def to task_id=ghi`

---

### STEP 5: Task Execution Monitoring
**Actor**: Task Executor + Agent
**Action**: Agent executes the assigned task, system monitors for timeout, quality, and errors
**Timeout**: Task-specific (from DAG, default 300s)
**Input**: `{ agent_id: uuid, task_id: uuid, task_input: object }`
**Output on SUCCESS**: `{ agent_id: uuid, task_id: uuid, status: "completed", output: object, metrics: {...} }` → GO TO STEP 6
**Output on FAILURE**:
- `FAILURE(task_timeout)`: Agent exceeded time limit → terminate execution, capture partial results, retry with backup agent
- `FAILURE(agent_crash)`: Agent process died → capture last state, retry with backup agent
- `FAILURE(bad_output)`: Output failed quality validation → retry with adjusted parameters (up to 3x)
- `FAILURE(resource_exhausted)`: Token budget depleted → pause execution, alert operator
- `FAILURE(tool_error)`: Required tool unavailable → retry x2 with fallback tool

**Observable states**:
- Customer sees: "Working on [task]... (X% complete)" if progress available
- Operator sees: Agent in "executing" state, task progress, token consumption
- Database: `agents.status = 'executing'`, `tasks.status = 'executing'`, `task_logs` entries
- Logs: `[agent-def] executing task_id=ghi, tokens_used=1250`

**Execution Monitoring Sub-Process**:
```
EVERY 30s:
  CHECK agent.health == alive
  CHECK agent.tokens_used < agent.token_budget
  CHECK elapsed_time < task.timeout
  CHECK output.quality_score (if partial output available)
  IF any check fails → trigger failure path
```

---

### STEP 6: Performance Evaluation
**Actor**: Performance Evaluator
**Action**: Score agent output quality, compare to expectations, update agent performance record
**Timeout**: 30s
**Input**: `{ agent_id: uuid, task_id: uuid, output: object, expected_output: object, task_metrics: object }`
**Output on SUCCESS**: `{ agent_id: uuid, task_id: uuid, performance_score: number, feedback: object }` → GO TO STEP 7
**Output on FAILURE**:
- `FAILURE(eval_error)`: Cannot evaluate output quality → default score of 0.5, flag for manual review
- `FAILURE(timeout)`: Evaluation timeout → use last known score, flag as "unverified"

**Observable states**:
- Customer sees: "Evaluating results..."
- Operator sees: Performance score updating in real-time
- Database: `agents.performance_score = updated_score`, `task_evaluations` row inserted
- Logs: `[perf-evaluator] agent_id=def scored 0.87 on task_id=ghi`

**Performance Score Formula**:
```
score = (quality_weight * quality_score)
      + (speed_weight * speed_score)
      + (cost_weight * cost_score)
      + (completeness_weight * completeness_score)

where:
  quality_score = f(output_meets_requirements, accuracy, relevance)
  speed_score = f(actual_time / estimated_time)
  cost_score = f(estimated_tokens / actual_tokens)
  completeness_score = f(output_completeness, missing_elements)
```

---

### STEP 7: Reuse vs Destruction Decision
**Actor**: Agent Registry
**Action**: Based on performance, decide whether to keep agent alive for reuse or destroy
**Timeout**: 5s
**Input**: `{ agent_id: uuid, performance_score: number, task_type: string, company_agent_count: number }`
**Output on SUCCESS**: `{ agent_id: uuid, decision: "reuse" | "destroy", reason: string }`
**Output on FAILURE**:
- `FAILURE(decision_error)`: Cannot determine → default to "idle_for_24h" then auto-destroy

**Observable states**:
- Customer sees: No direct visibility
- Operator sees: Agent status changes to "idle" or "destroying"
- Database: `agents.status = 'idle' | 'destroying'`
- Logs: `[agent-registry] agent_id=def decision=reuse, score=0.87, idle_ttl=24h`

**Reuse Decision Logic**:
```
IF performance_score >= 0.8
  AND company_agent_count < company_max_agents * 0.9
  AND task_type is likely to recur
THEN
  decision = "reuse" (idle TTL = 24h)
ELSE IF performance_score >= 0.5
  AND company_agent_count < company_max_agents * 0.7
THEN
  decision = "reuse" (idle TTL = 1h)
ELSE
  decision = "destroy"
```

---

### STEP 8: Graceful Destruction (if decision = destroy)
**Actor**: Agent Factory
**Action**: Save agent's learning to memory, release resources, remove from registry
**Timeout**: 30s
**Input**: `{ agent_id: uuid, final_performance: object, learning_data: object }`
**Output on SUCCESS**: `{ agent_id: uuid, status: "destroyed" }` → WORKFLOW COMPLETE
**Output on FAILURE**:
- `FAILURE(memory_write_error)`: Cannot save learning → retry x3 → if all fail, log warning, destroy anyway (learning lost)
- `FAILURE(destruction_error)`: Cannot release resources → retry x2 → alert operator for manual cleanup

**Observable states**:
- Customer sees: "Agent completed work and is being cleaned up..."
- Operator sees: Agent in "destroying" → "destroyed" state
- Database: `agents.status = 'destroyed'`, `agent_memories` row inserted
- Logs: `[agent-factory] destroying agent_id=def, saving learning data`

**Destruction Checklist**:
1. Extract learning data (prompts that worked, tools that succeeded, patterns)
2. Write to agent memory (for future agent creation)
3. Release token allocation back to company pool
4. Release compute resources
5. Remove from active agent registry
6. Archive agent record (keep history, mark as destroyed)

---

## State Transitions

```
[TEMPLATE_SELECTED] → [CREATING] → [CREATED] → [CALIBRATING] → [CALIBRATED]
[CREATING] → [CREATION_FAILED] (terminal for this instance)
[CREATED] → [CREATION_FAILED] (if resources unavailable)
[CALIBRATING] → [CALIBRATED] → [IDLE]
[CALIBRATING] → [CAL_ERROR] → [IDLE] (with defaults)
[IDLE] → [ASSIGNED] → [EXECUTING]
[EXECUTING] → [EVALUATING] → [IDLE] (reuse)
[EXECUTING] → [FAILED] → [DESTROYING] → [DESTROYED]
[EXECUTING] → [TIMEOUT] → [FAILED]
[IDLE] → (24h no assignment) → [DESTROYING] → [DESTROYED]
[IDLE] → (1h no assignment, low score) → [DESTROYING] → [DESTROYED]
```

---

## Handoff Contracts

### Goal Decomposition → Agent Factory
**Event**: `GoalActivated`
**Payload**:
```json
{
  "goal_id": "uuid",
  "company_id": "uuid",
  "projects": [{"project_id": "uuid", "required_capabilities": ["string"]}],
  "total_agent_estimate": "number"
}
```

### Agent Factory → Skill Calibrator
**Endpoint**: `POST /internal/agents/calibrate`
**Payload**:
```json
{
  "agent_id": "uuid",
  "template": {"base_model": "string", "system_prompt_template": "string", "tools": ["object"]},
  "company_context": {"industry": "string", "conventions": ["string"]},
  "task_context": {"domain": "string", "complexity": "number"}
}
```
**Success response**:
```json
{
  "ok": true,
  "calibrated_config": {
    "system_prompt": "string",
    "tools": ["object"],
    "params": {"temperature": "number", "max_tokens": "number"}
  }
}
```
**Timeout**: 60s

### Task Executor → Performance Evaluator
**Endpoint**: `POST /internal/evaluation/evaluate`
**Payload**:
```json
{
  "agent_id": "uuid",
  "task_id": "uuid",
  "output": "object — the task output",
  "expected": "object — what was expected",
  "metrics": {"tokens_used": "number", "time_seconds": "number", "cost_usd": "number"}
}
```
**Success response**:
```json
{
  "ok": true,
  "performance_score": "number 0-1",
  "breakdown": {"quality": "number", "speed": "number", "cost": "number", "completeness": "number"},
  "feedback": "string — human-readable feedback"
}
```
**Timeout**: 30s

---

## Cleanup Inventory

| Resource | Created at step | Destroyed by | Destroy method |
|---|---|---|---|
| Agent record | Step 2 | STEP 8 (destruction) | `DELETE FROM agents WHERE agent_id = ?` |
| Agent config | Step 3 | STEP 8 | Cascade delete |
| Token allocation | Step 4 | STEP 8 | Release to pool |
| Task assignment | Step 4 | STEP 8 | `UPDATE tasks SET assigned_agent_id = NULL` |
| Agent memory | Step 8 | Never (persisted) | Kept for future agents |

---

## Test Cases

| Test | Trigger | Expected behavior |
|---|---|---|
| TC-01: Happy path creation | GoalActivated event | Agent created, calibrated, assigned, completed, destroyed within 5min |
| TC-02: Agent reuse | Idle agent with matching capabilities | Existing agent reused, no new creation |
| TC-03: Quota exceeded | Company at max agents | Error returned, no creation attempt |
| TC-04: Template not found | No template for required capabilities | Error with available templates list |
| TC-05: Calibration failure | Skill Calibrator unresponsive | Agent created with defaults, flagged unoptimized |
| TC-06: Task timeout | Agent exceeds time limit | Agent terminated, task retried with backup |
| TC-07: Bad output | Output fails quality check | Agent retries with adjusted params (up to 3x) |
| TC-08: Agent crash | Agent process dies | Task reassigned, crash logged |
| TC-09: High performer | Score >= 0.8 | Agent kept alive for 24h reuse |
| TC-10: Low performer | Score < 0.5 | Agent destroyed after task |
| TC-11: Memory write failure | Cannot save learning | Warning logged, agent destroyed anyway |
| TC-12: Concurrent assignment | Two tasks assigned simultaneously | Agent accepts only first, second queued |

---

## Assumptions

| # | Assumption | Where verified | Risk if wrong |
|---|---|---|---|
| A1 | Agent templates exist for common roles | Not verified — greenfield | First use requires template creation |
| A2 | Skill Calibrator can adjust prompts effectively | Not verified | Calibration adds no value, wasted tokens |
| A3 | Performance scoring correlates with actual quality | Not verified | Good agents destroyed, bad agents kept |
| A4 | 24h idle TTL is appropriate for reuse window | Not verified | Agents destroyed too soon or kept too long |
| A5 | Agent memory can be effectively transferred to new agents | Not verified | Learning loss on destruction |

---

## Open Questions

- Should agents have personality/persona that persists across reuses?
- How do we handle agents that are "good enough" but not great?
- Should there be a "promotion" mechanism for consistently high performers?
- How does agent destruction work when the agent is mid-task?
