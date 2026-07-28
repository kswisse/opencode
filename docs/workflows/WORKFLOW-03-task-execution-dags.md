# WORKFLOW-03: Task Execution DAGs

**Version**: 0.1
**Date**: 2026-07-28
**Author**: Workflow Architect
**Status**: Draft
**Implements**: Autonomous AI Workforce Platform — DAG Construction, Scheduling, Execution, Verification

---

## Overview

Task Execution DAGs take planned task graphs and execute them: scheduling waves, dispatching agents, monitoring parallel execution, handling dependencies, creating checkpoints, and aggregating results. The DAG is the core execution model — it defines what runs when, what depends on what, and how results flow between tasks.

---

## Actors

| Actor | Role in this workflow |
|---|---|
| DAG Scheduler | Manages wave execution, dependency resolution |
| Task Dispatcher | Sends tasks to available agents |
| Agent Pool | Available agents ready for assignment |
| Checkpoint Manager | Persists intermediate results at checkpoints |
| Result Aggregator | Collects and merges outputs from parallel tasks |
| Conditional Evaluator | Resolves conditional branches based on task outputs |
| Event Bus | Publishes task lifecycle events |

---

## Prerequisites

- Task DAGs created by Goal Decomposition (WORKFLOW-01)
- Agents created and calibrated (WORKFLOW-02)
- Agent Pool has available agents
- Checkpoint storage is operational

---

## Trigger

Triggered by `GoalActivated` event. DAG Scheduler receives task DAGs and begins execution.

---

## State Diagram

```
[DAG_READY] → [WAVE_SCHEDULING] → [WAVE_RUNNING] → [WAVE_COMPLETE]
     ↓               ↓                    ↓               ↓
 [DAG_PAUSED]  [WAVE_PARTIAL]     [WAVE_FAILED]    [NEXT_WAVE | DAG_COMPLETE]
                                                  ↓
                                            [DAG_FAILED]
```

---

## Workflow Tree

### STEP 1: DAG Initialization
**Actor**: DAG Scheduler
**Action**: Load DAG, validate structure, identify first wave, initialize execution context
**Timeout**: 15s
**Input**: `{ dag_id: uuid, project_id: uuid, goal_id: uuid }`
**Output on SUCCESS**: `{ dag_id: uuid, status: "ready", first_wave: { wave_number, task_ids }, total_waves: number }` → GO TO STEP 2
**Output on FAILURE**:
- `FAILURE(dag_not_found)`: DAG doesn't exist → return error to Goal Decomposition
- `FAILURE(dag_invalid)`: Circular dependencies, missing nodes → return error with specific issues
- `FAILURE(context_error)`: Cannot initialize execution context → retry x2 with 5s backoff

**Observable states**:
- Customer sees: "Task plan loaded, preparing execution..."
- Operator sees: DAG in "ready" state, wave count displayed
- Database: `task_dags.status = 'ready'`, `task_dags.execution_started_at = now()`
- Logs: `[dag-scheduler] initializing dag_id=jkl, wave_count=7`

**DAG Validation Checks**:
1. All nodes have unique IDs
2. No circular dependencies (topological sort succeeds)
3. All edge references point to existing nodes
4. Each node has required fields (name, type, capabilities)
5. Critical path length < deadline

---

### STEP 2: Wave Scheduling
**Actor**: DAG Scheduler
**Action**: Identify tasks ready for execution (all dependencies met), group into parallel wave
**Timeout**: 10s
**Input**: `{ dag_id: uuid, completed_tasks: Set<uuid>, current_wave: number }`
**Output on SUCCESS**: `{ dag_id: uuid, wave: { wave_number, tasks: [{ task_id, agent_requirements }] }, parallelism: number }` → GO TO STEP 3
**Output on FAILURE**:
- `FAILURE(blocked)`: All remaining tasks have unmet dependencies → check for deadlock, alert operator
- `FAILURE(wave_empty)`: No tasks ready → DAG may be complete or stuck
- `FAILURE(agent_unavailable)`: No agents available for this wave → pause wave, wait for agent pool to refill

**Observable states**:
- Customer sees: "Preparing wave [N] of [total]..."
- Operator sees: Wave tasks listed with agent requirements
- Database: `task_dags.current_wave = wave_number`
- Logs: `[dag-scheduler] scheduling wave 3 of 7, task_count=4`

**Wave Scheduling Algorithm**:
```
1. Find all tasks where ALL dependencies are in completed_tasks
2. Group tasks that can run in parallel (no inter-dependencies)
3. For each task, check if required capabilities exist in agent pool
4. IF insufficient agents → hold task for next wave or wait
5. Return wave with available tasks
```

---

### STEP 3: Task Dispatching
**Actor**: Task Dispatcher
**Action**: For each task in the wave, find or create appropriate agent, dispatch task
**Timeout**: 30s per task
**Input**: `{ dag_id: uuid, wave: { tasks: [...] }, agent_pool: [...] }`
**Output on SUCCESS**: `{ dag_id: uuid, wave_number: number, dispatched: [{ task_id, agent_id }], queued: [task_id] }` → GO TO STEP 4
**Output on FAILURE**:
- `FAILURE(dispatch_error)`: Specific task cannot be dispatched → skip task, mark as "skipped", continue with others
- `FAILURE(pool_exhausted)`: No agents for any task → pause wave, trigger agent creation
- `FAILURE(timeout)`: Dispatch timeout → retry individual task dispatch x2

**Observable states**:
- Customer sees: "Assigning agents to tasks..."
- Operator sees: Tasks showing "dispatching" → "assigned" state
- Database: `tasks.status = 'dispatching'`, `tasks.assigned_agent_id = agent_id`
- Logs: `[task-dispatcher] dispatching task_id=mno to agent_id=pqr`

---

### STEP 4: Parallel Execution Monitoring
**Actor**: DAG Scheduler
**Action**: Monitor all tasks in current wave simultaneously, handle completions and failures
**Timeout**: Max task timeout in wave + 30s buffer
**Input**: `{ dag_id: uuid, wave_number: number, tasks: [{ task_id, agent_id, timeout }] }`
**Output on SUCCESS**: `{ dag_id: uuid, wave_number: number, results: [{ task_id, status: "completed", output }] }` → GO TO STEP 6
**Output on FAILURE**:
- `FAILURE(partial_completion)`: Some tasks completed, some failed → proceed to STEP 5 for failure handling
- `FAILURE(wave_timeout)`: Wave exceeded max allowed time → force-terminate all running tasks
- `FAILURE(all_failed)`: All tasks in wave failed → DAG fails

**Observable states**:
- Customer sees: "Executing [N] tasks in parallel... [X]% complete"
- Operator sees: Per-task progress, agent health, token consumption
- Database: `tasks.status = 'executing'`, `task_logs` updated continuously
- Logs: `[dag-scheduler] wave 3 running, completed=2/4, failed=0`

**Monitoring Loop**:
```
EVERY 5s:
  FOR each task in wave:
    IF task.status == 'completed':
      collect result
    ELIF task.status == 'failed':
      log failure
    ELIF task.status == 'timeout':
      trigger timeout handling
    ELIF task.status == 'executing':
      check elapsed_time < timeout
      IF elapsed > timeout * 0.8:
        send warning to agent
      IF elapsed > timeout:
        trigger timeout handling
  
  IF all tasks terminal:
    break monitoring loop
```

---

### STEP 5: Partial Failure Handling
**Actor**: DAG Scheduler
**Action**: Handle failed tasks within a wave — retry, skip, or abort based on failure type and task criticality
**Timeout**: 30s
**Input**: `{ dag_id: uuid, wave_number: number, failed_tasks: [{ task_id, failure_type, error }] }`
**Output on SUCCESS**: `{ dag_id: uuid, recovered: [task_id], skipped: [task_id] }` → GO TO STEP 6
**Output on FAILURE**:
- `FAILURE(retry_exhausted)`: Task failed after max retries → mark as "permanently_failed"
- `FAILURE(critical_failure)`: Critical task failed, cannot continue → abort DAG

**Observable states**:
- Customer sees: "Some tasks encountered issues, retrying..."
- Operator sees: Failed tasks with retry counts, recovery actions
- Database: `tasks.status = 'retrying' | 'skipped' | 'permanently_failed'`
- Logs: `[dag-scheduler] handling failures in wave 3, retrying task_id=stu`

**Failure Handling Decision Tree**:
```
IF task.criticality == 'critical':
  IF task.retry_count < task.max_retries:
    RETRY (with backoff)
  ELSE:
    ABORT DAG → cleanup all
ELIF task.failure_type == 'transient':
  IF task.retry_count < task.max_retries:
    RETRY
  ELSE:
    SKIP (if non-critical)
ELIF task.failure_type == 'permanent':
  SKIP (log reason, continue)
ELIF task.failure_type == 'timeout':
  IF task.retry_count < 1:
    RETRY with longer timeout
  ELSE:
    SKIP or ABORT based on criticality
```

---

### STEP 6: Checkpoint Creation
**Actor**: Checkpoint Manager
**Action**: After each wave completes, persist intermediate results for resumability
**Timeout**: 15s
**Input**: `{ dag_id: uuid, wave_number: number, results: [...], execution_state: object }`
**Output on SUCCESS**: `{ dag_id: uuid, checkpoint_id: uuid, wave_number: number }` → GO TO STEP 7
**Output on FAILURE**:
- `FAILURE(checkpoint_error)`: Cannot persist → retry x3 with 5s backoff → if all fail, log warning, continue (risk: cannot resume)
- `FAILURE(storage_full)`: Checkpoint storage exceeded → alert operator, continue without checkpoint

**Observable states**:
- Customer sees: No direct visibility (internal)
- Operator sees: Checkpoint created, wave results saved
- Database: `checkpoints` row inserted with full execution state
- Logs: `[checkpoint-mgr] checkpoint created for dag_id=jkl, wave=3`

**Checkpoint Schema**:
```json
{
  "checkpoint_id": "uuid",
  "dag_id": "uuid",
  "wave_number": "number",
  "completed_tasks": [{"task_id": "uuid", "output": "object", "agent_id": "uuid"}],
  "failed_tasks": [{"task_id": "uuid", "error": "string", "retry_count": "number"}],
  "skipped_tasks": ["uuid"],
  "execution_state": {
    "tokens_used_total": "number",
    "cost_usd_total": "number",
    "elapsed_seconds": "number"
  },
  "created_at": "ISO8601"
}
```

---

### STEP 7: Result Aggregation (for parallel tasks)
**Actor**: Result Aggregator
**Action**: Merge outputs from parallel tasks into a unified result for downstream tasks
**Timeout**: 30s
**Input**: `{ dag_id: uuid, wave_number: number, results: [{ task_id, output }], aggregation_config: object }`
**Output on SUCCESS**: `{ dag_id: uuid, aggregated_output: object }` → GO TO STEP 8
**Output on FAILURE**:
- `FAILURE(aggregation_error)`: Cannot merge outputs → retry with simplified merge → if fails, pass raw results downstream
- `FAILURE(timeout)`: Aggregation timeout → use last successful merge

**Observable states**:
- Customer sees: "Combining results from parallel tasks..."
- Operator sees: Aggregated output visible in task view
- Database: `task_outputs` updated with aggregated results
- Logs: `[result-aggregator] aggregating wave 3 outputs, task_count=4`

**Aggregation Strategies**:
```
IF all outputs are text:
  CONCATENATE with separators
ELIF all outputs are structured data:
  MERGE based on schema compatibility
ELIF outputs are code files:
  COMBINE with namespace resolution
ELIF outputs are conflicting:
  USE priority-based selection or request operator adjudication
ELSE:
  PASS raw results as array to next task
```

---

### STEP 8: Conditional Branch Evaluation
**Actor**: Conditional Evaluator
**Action**: Evaluate conditional edges in the DAG, determine which branches to activate
**Timeout**: 10s
**Input**: `{ dag_id: uuid, completed_tasks: [...], conditional_edges: [...] }`
**Output on SUCCESS**: `{ dag_id: uuid, activated_tasks: [task_id], deactivated_tasks: [task_id] }` → GO TO STEP 9
**Output on FAILURE**:
- `FAILURE(evaluation_error)`: Cannot evaluate condition → default to "all branches" (safe but wasteful)
- `FAILURE(ambiguous)`: Condition result unclear → activate all branches

**Observable states**:
- Customer sees: No direct visibility
- Operator sees: Branch decisions logged with reasoning
- Database: `task_dags.branch_decisions` logged
- Logs: `[conditional-eval] dag_id=jkl, activated 3/5 branches`

**Conditional Edge Schema**:
```json
{
  "from_task_id": "uuid",
  "to_task_id": "uuid",
  "condition": {
    "type": "output_check | metric_check | operator_decision",
    "field": "string — path to value in output",
    "operator": "eq | gt | lt | contains | regex",
    "value": "any"
  }
}
```

---

### STEP 9: Wave Completion & Next Wave Check
**Actor**: DAG Scheduler
**Action**: After wave completes, check if more waves remain, or if DAG is complete
**Timeout**: 5s
**Input**: `{ dag_id: uuid, completed_waves: number, total_waves: number }`
**Output on SUCCESS**: `{ dag_id: uuid, status: "next_wave" | "dag_complete", next_wave: { wave_number, task_ids } }` → GO TO STEP 2 (if next_wave) or STEP 10 (if complete)
**Output on FAILURE**:
- `FAILURE(stuck)`: No tasks ready but DAG not complete → deadlock detected, alert operator

**Observable states**:
- Customer sees: "Wave [N] complete. Starting wave [N+1]..."
- Operator sees: Wave progress bar, DAG completion percentage
- Database: `task_dags.completed_waves = N`
- Logs: `[dag-scheduler] wave 3 complete, proceeding to wave 4`

---

### STEP 10: DAG Completion
**Actor**: DAG Scheduler
**Action**: All waves complete, aggregate final results, publish DAGCompleted event
**Timeout**: 30s
**Input**: `{ dag_id: uuid, all_results: [...] }`
**Output on SUCCESS**: `{ dag_id: uuid, status: "complete", final_output: object, metrics: {...} }` → WORKFLOW COMPLETE
**Output on FAILURE**:
- `FAILURE(final_aggregation_error)`: Cannot produce final output → save raw results, flag for manual review

**Observable states**:
- Customer sees: "All tasks complete! Processing final results..."
- Operator sees: DAG marked complete, final output available
- Database: `task_dags.status = 'complete'`, `task_dags.completed_at = now()`
- Logs: `[dag-scheduler] DAG jkl complete, total_tokens=45000, total_cost=$2.70`

**Events Published**:
```json
{
  "event_type": "DAGCompleted",
  "payload": {
    "dag_id": "uuid",
    "project_id": "uuid",
    "goal_id": "uuid",
    "final_output": "object",
    "metrics": {
      "total_tasks": "number",
      "completed_tasks": "number",
      "failed_tasks": "number",
      "total_tokens": "number",
      "total_cost_usd": "number",
      "elapsed_seconds": "number"
    }
  }
}
```

---

## ABORT_CLEANUP: DAG Failure
**Triggered by**: Critical task failure, deadline exceeded, operator abort
**Actions**:
1. Terminate all running tasks in current wave
2. Release all assigned agents back to pool (or destroy if task-specific)
3. Persist checkpoint with failure state
4. Set dag.status = 'failed'
5. Publish DAGFailed event
6. Notify operator

**What customer sees**: "Task plan failed at wave [N]. Some results have been saved."
**What operator sees**: DAG in failed state with failure details, option to resume from checkpoint

---

## State Transitions

```
[DAG_READY] → [WAVE_SCHEDULING] → [WAVE_RUNNING]
[WAVE_RUNNING] → [WAVE_COMPLETE] → [NEXT_WAVE] → [WAVE_SCHEDULING]
[WAVE_RUNNING] → [WAVE_PARTIAL] → [WAVE_COMPLETE] (after handling)
[WAVE_RUNNING] → [WAVE_FAILED] → [DAG_FAILED]
[WAVE_COMPLETE] → [DAG_COMPLETE] (if last wave)
[DAG_COMPLETE] → (terminal)
[DAG_FAILED] → (terminal, can resume from checkpoint)
```

---

## Handoff Contracts

### DAG Scheduler → Task Dispatcher
**Endpoint**: `POST /internal/tasks/dispatch`
**Payload**:
```json
{
  "dag_id": "uuid",
  "wave_number": "number",
  "tasks": [
    {
      "task_id": "uuid",
      "name": "string",
      "type": "string",
      "required_capabilities": ["string"],
      "input": "object",
      "timeout_seconds": "number",
      "retry_policy": {"max_retries": "number", "backoff_seconds": ["number"]}
    }
  ]
}
```
**Success response**:
```json
{
  "ok": true,
  "dispatched": [{"task_id": "uuid", "agent_id": "uuid"}],
  "queued": ["uuid"]
}
```
**Timeout**: 30s

### Task Dispatcher → Agent Pool
**Endpoint**: `POST /internal/agents/assign`
**Payload**:
```json
{
  "task_id": "uuid",
  "required_capabilities": ["string"],
  "timeout_seconds": "number",
  "priority": "enum(critical|high|medium|low)"
}
```
**Success response**:
```json
{
  "ok": true,
  "agent_id": "uuid",
  "agent_name": "string",
  "estimated_ready_in_seconds": "number"
}
```
**Failure response**:
```json
{
  "ok": false,
  "error": "string",
  "code": "NO_AGENTS | QUOTA_EXCEEDED | TIMEOUT",
  "retryable": true
}
```
**Timeout**: 10s

### DAG Scheduler → Checkpoint Manager
**Endpoint**: `POST /internal/checkpoints/create`
**Payload**:
```json
{
  "dag_id": "uuid",
  "wave_number": "number",
  "completed_tasks": ["object"],
  "failed_tasks": ["object"],
  "execution_state": "object"
}
```
**Success response**:
```json
{
  "ok": true,
  "checkpoint_id": "uuid",
  "stored_bytes": "number"
}
```
**Timeout**: 15s

---

## Cleanup Inventory

| Resource | Created at step | Destroyed by | Destroy method |
|---|---|---|---|
| DAG execution state | Step 1 | ABORT_CLEANUP | Reset to 'ready' |
| Task assignments | Step 3 | ABORT_CLEANUP | Release agents |
| Task outputs | Step 4 | ABORT_CLEANUP | `DELETE FROM task_outputs WHERE dag_id = ?` |
| Checkpoints | Step 6 | Manual cleanup | `DELETE FROM checkpoints WHERE dag_id = ?` |
| Aggregated results | Step 7 | ABORT_CLEANUP | `DELETE FROM task_outputs WHERE dag_id = ? AND type = 'aggregated'` |

---

## Test Cases

| Test | Trigger | Expected behavior |
|---|---|---|
| TC-01: Happy path | Valid DAG, all agents available | All waves execute, DAG completes within budget |
| TC-02: Parallel execution | Wave with 5 independent tasks | All 5 execute simultaneously |
| TC-03: Dependency resolution | Task B depends on Task A | Task B waits until Task A completes |
| TC-04: Wave timeout | Agent exceeds wave time limit | Task terminated, retried with backup |
| TC-05: Partial failure | 1 of 4 tasks in wave fails | Failed task retried, others continue |
| TC-06: Critical failure | Critical task fails after retries | DAG aborted, cleanup executed |
| TC-07: Conditional branch | Condition evaluates to false | Branch skipped, execution continues |
| TC-08: Checkpoint resume | DAG fails at wave 5 | Resume from wave 5 checkpoint |
| TC-09: Agent unavailable | No agents for current wave | Wave paused, agent creation triggered |
| TC-10: Deadlock detection | Circular dependencies somehow present | Alert operator, halt execution |
| TC-11: Large DAG | 500+ tasks across 20 waves | Execution completes within resource limits |
| TC-12: Concurrent DAGs | Multiple DAGs running simultaneously | Each executed independently, resources shared |

---

## Assumptions

| # | Assumption | Where verified | Risk if wrong |
|---|---|---|---|
| A1 | DAGs have no circular dependencies at creation | Not verified — greenfield | Execution hangs |
| A2 | Agent pool can handle peak parallelism of largest wave | Not verified | Wave scheduling delays |
| A3 | Checkpoint storage is durable and fast | Not verified | Resume fails after crash |
| A4 | Task outputs are always serializable | Not verified | Aggregation fails |
| A5 | Conditional evaluation is deterministic | Not verified | Non-deterministic execution paths |

---

## Open Questions

- Should there be a maximum DAG depth or width limit?
- How do we handle tasks that produce very large outputs (GB-scale)?
- Should there be a "manual intervention" step for tasks requiring human review?
- How does the system handle DAGs that are modified while executing?
