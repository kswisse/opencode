# WORKFLOW-09: Resource Allocation Flows

**Version**: 0.1
**Date**: 2026-07-28
**Author**: Workflow Architect
**Status**: Draft
**Implements**: Autonomous AI Workforce Platform — Token Budget, Cost Tracking, Priority Allocation, Deadline Enforcement, Budget Alerts

---

## Overview

Resource Allocation manages the finite resources (tokens, compute, budget) across agents, tasks, and projects. It ensures fair distribution, enforces budgets, tracks costs, and alerts operators before resources are exhausted. The system must balance competing demands while respecting company-level constraints.

---

## Actors

| Actor | Role in this workflow |
|---|---|
| Budget Manager | Manages company-level budget allocation |
| Token Allocator | Distributes token budgets to agents |
| Cost Tracker | Records and aggregates costs in real-time |
| Priority Scheduler | Allocates resources based on task priority |
| Deadline Enforcer | Monitors deadlines, escalates at-risk tasks |
| Alert System | Sends budget and deadline alerts |
| Event Bus | Publishes resource events |

---

## Prerequisites

- Company budget is configured
- Token pools are initialized
- Cost tracking tables are created
- Alert channels are configured

---

## Trigger

Resource allocation is triggered by:
1. Goal activation (initial budget allocation)
2. Agent creation (token allocation)
3. Task assignment (task-level budget)
4. Cost threshold breach (alert)
5. Deadline approaching (escalation)

---

## State Diagram

```
[BUDGET_SET] → [ALLOCATED] → [DISTRIBUTED] → [TRACKING]
                                  ↓
                            [THRESHOLD_BREACHED] → [ALERTED]
                                  ↓
                            [EXHAUSTED] → [PAUSED | THROTTLED]
```

---

## Workflow Tree

### STEP 1: Company Budget Setup
**Actor**: Budget Manager
**Action**: When company subscribes or updates plan, set budget limits
**Timeout**: 10s
**Input**: `{ company_id: uuid, budget: { monthly_usd: number, token_limit: number, alert_thresholds: object } }`
**Output on SUCCESS**: `{ company_id: uuid, budget_id: uuid, status: "active" }` → GO TO STEP 2
**Output on FAILURE**:
- `FAILURE(budget_error)`: Cannot set budget → retry x2 with 5s backoff

**Budget Schema**:
```json
{
  "budget_id": "uuid",
  "company_id": "uuid",
  "monthly": {
    "limit_usd": "number",
    "limit_tokens": "number",
    "current_usd": 0,
    "current_tokens": 0,
    "reset_date": "ISO8601 — first of next month"
  },
  "per_goal": {
    "max_usd": "number",
    "max_tokens": "number"
  },
  "per_agent": {
    "max_tokens_per_task": "number",
    "max_tokens_per_day": "number"
  },
  "alert_thresholds": {
    "warning_pct": 0.7,
    "critical_pct": 0.9,
    "hard_limit_pct": 1.0
  },
  "throttle_policy": {
    "enabled": true,
    "action": "enum(throttle|pause|reject)",
    "throttle_rate": 0.5
  }
}
```

---

### STEP 2: Goal Budget Allocation
**Actor**: Budget Manager
**Action**: When goal is activated, allocate budget from company pool to goal
**Timeout**: 10s
**Input**: `{ goal_id: uuid, company_id: uuid, estimated_cost_usd: number, estimated_tokens: number }`
**Output on SUCCESS**: `{ goal_id: uuid, allocated_usd: number, allocated_tokens: number }` → GO TO STEP 3
**Output on FAILURE**:
- `FAILURE(insufficient_budget)`: Company budget insufficient → return to Goal Decomposition with error
- `FAILURE(allocation_error)`: Cannot allocate → retry x2

**Allocation Logic**:
```
1. CHECK company has sufficient budget
2. CHECK per-goal limits not exceeded
3. RESERVE budget (soft allocation)
4. IF reservation would exceed monthly limit:
   RETURN insufficient_budget
5. UPDATE company budget (deduct reserved)
6. UPDATE goal budget (add reserved)
```

---

### STEP 3: Agent Token Allocation
**Actor**: Token Allocator
**Action**: When agent is created or assigned, allocate token budget
**Timeout**: 5s
**Input**: `{ agent_id: uuid, goal_id: uuid, task_count: number, estimated_tokens_per_task: number }`
**Output on SUCCESS**: `{ agent_id: uuid, token_budget: number, tokens_remaining: number }` → GO TO STEP 4
**Output on FAILURE**:
- `FAILURE(quota_exceeded)`: Goal or company quota exceeded → return to Agent Lifecycle
- `FAILURE(allocation_error)`: Cannot allocate → retry x2

**Agent Token Allocation**:
```
agent_token_budget = MIN(
  goal.allocated_tokens / goal.agent_count,
  company.per_agent.max_tokens_per_day,
  goal.per_agent_limit
)

agent.tokens_remaining = agent_token_budget
```

---

### STEP 4: Task-Level Cost Tracking
**Actor**: Cost Tracker
**Action**: Track cost of each task execution in real-time
**Timeout**: Real-time
**Input**: `{ task_id: uuid, agent_id: uuid, tokens_used: number, cost_usd: number }`
**Output on SUCCESS**: `{ task_id: uuid, cumulative_tokens: number, cumulative_usd: number }` → GO TO STEP 5
**Output on FAILURE**:
- `FAILURE(tracking_error)`: Cannot record cost → log to audit trail, continue execution

**Cost Tracking Schema**:
```json
{
  "cost_entry_id": "uuid",
  "task_id": "uuid",
  "agent_id": "uuid",
  "goal_id": "uuid",
  "company_id": "uuid",
  "tokens": {
    "input": "number",
    "output": "number",
    "total": "number"
  },
  "cost_usd": "number",
  "model": "string",
  "timestamp": "ISO8601"
}
```

**Running Totals Updated**:
```
task.cumulative_tokens += tokens_used
task.cumulative_usd += cost_usd

agent.tokens_remaining -= tokens_used
agent.cumulative_usd += cost_usd

goal.tokens_remaining -= tokens_used
goal.cumulative_usd += cost_usd

company.monthly.current_tokens += tokens_used
company.monthly.current_usd += cost_usd
```

---

### STEP 5: Budget Threshold Monitoring
**Actor**: Alert System
**Action**: When cost approaches limits, send alerts
**Timeout**: Real-time
**Input**: `{ entity_type: enum(company|goal|agent), entity_id: uuid, current_usage: number, limit: number }`
**Output on SUCCESS**: `{ alert_sent: boolean, level: enum(warning|critical|hard_limit) }`

**Threshold Logic**:
```
usage_pct = current_usage / limit

IF usage_pct >= hard_limit_pct (1.0):
  TRIGGER hard_limit action (throttle/pause/reject)
  SEND critical alert
  
ELIF usage_pct >= critical_pct (0.9):
  SEND critical alert
  LOG for operator review
  
ELIF usage_pct >= warning_pct (0.7):
  SEND warning alert
  LOG for awareness
```

**Alert Types**:
| Level | Message | Action |
|---|---|---|
| Warning | "Company X has used 70% of monthly token budget" | Informational |
| Critical | "Goal Y has used 90% of allocated tokens" | Operator review |
| Hard Limit | "Agent Z has exceeded token budget, pausing" | Auto-throttle/pause |
| Deadline | "Goal Z is at risk of missing deadline in 24h" | Priority escalation |

---

### STEP 6: Priority-Based Allocation
**Actor**: Priority Scheduler
**Action**: When multiple tasks compete for limited resources, allocate based on priority
**Timeout**: 5s
**Input**: `{ competing_tasks: [{ task_id, priority, deadline, estimated_cost }] }`
**Output on SUCCESS**: `{ allocations: [{ task_id, allocated_tokens, allocated_usd }] }`

**Priority Allocation Algorithm**:
```
1. SORT tasks by priority (critical > high > medium > low)
2. FOR each task in priority order:
   IF task.priority == 'critical':
     ALLOCATE full requested amount (guaranteed)
   ELIF task.priority == 'high':
     ALLOCATE up to 80% of requested (if available)
   ELIF task.priority == 'medium':
     ALLOCATE up to 50% of requested (if available)
   ELIF task.priority == 'low':
     ALLOCATE remaining budget (if any)
     
3. IF total requested > available:
   CRITICAL tasks get first allocation
   HIGH tasks get second priority
   MEDIUM tasks get reduced allocation
   LOW tasks may be deferred
```

---

### STEP 7: Deadline Enforcement
**Actor**: Deadline Enforcer
**Action**: Monitor task and goal deadlines, escalate at-risk items
**Timeout**: Continuous monitoring
**Input**: `{ entity_type: enum(task|goal), entity_id: uuid, deadline: ISO8601, estimated_completion: ISO8601 }`
**Output on SUCCESS**: `{ entity_id: uuid, risk_level: enum(low|medium|high|critical) }`

**Deadline Risk Assessment**:
```
time_remaining = deadline - now()
estimated_remaining = estimated_completion - now()

IF estimated_remaining > time_remaining * 1.5:
  risk = 'critical' — likely to miss deadline
  ACTION: escalate to operator, increase priority, allocate more resources
  
ELIF estimated_remaining > time_remaining * 1.2:
  risk = 'high' — at risk
  ACTION: monitor closely, prepare contingency
  
ELIF estimated_remaining > time_remaining:
  risk = 'medium' — tight
  ACTION: optimize for speed
  
ELSE:
  risk = 'low' — on track
  ACTION: continue normal execution
```

---

### STEP 8: Budget Pause/Throttle
**Actor**: Budget Manager
**Action**: When hard limit reached, pause or throttle execution
**Timeout**: 5s
**Input**: `{ entity_type: enum(company|goal|agent), entity_id: uuid, action: enum(throttle|pause) }`
**Output on SUCCESS**: `{ entity_id: uuid, status: "paused" | "throttled" }`

**Throttle vs Pause**:
```
THROTTLE:
  REDUCE agent execution rate by throttle_rate (e.g., 50%)
  TASKS continue but slower
  TOKEN consumption reduced
  
PAUSE:
  STOP all task execution for entity
  AGENTS released back to pool
  NO new tasks assigned until budget reset or operator override
```

**Pause Resume Conditions**:
```
1. Monthly budget resets (first of month)
2. Operator manually increases budget
3. Goal completes and releases unused budget
4. Emergency override by platform admin
```

---

### STEP 9: Cost Reporting
**Actor**: Cost Tracker (background)
**Action**: Generate cost reports for operator visibility
**Timeout**: 30s (background job)
**Input**: `{ company_id: uuid, period: enum(daily|weekly|monthly) }`
**Output on SUCCESS**: `{ report_id: uuid, summary: object }`

**Cost Report Schema**:
```json
{
  "report_id": "uuid",
  "company_id": uuid,
  "period": {
    "start": "ISO8601",
    "end": "ISO8601"
  },
  "summary": {
    "total_usd": "number",
    "total_tokens": "number",
    "by_goal": [
      {
        "goal_id": "uuid",
        "goal_name": "string",
        "usd": "number",
        "tokens": "number",
        "tasks_completed": "number",
        "cost_per_task": "number"
      }
    ],
    "by_agent_type": [
      {
        "role": "string",
        "usd": "number",
        "tokens": "number",
        "task_count": "number"
      }
    ],
    "by_model": [
      {
        "model": "string",
        "usd": "number",
        "tokens": "number"
      }
    ],
    "trend": {
      "vs_previous_period": "enum(up|stable|down)",
      "change_pct": "number"
    }
  }
}
```

---

## State Transitions

```
[BUDGET_SET] → [ALLOCATED] → [DISTRIBUTED] → [TRACKING]
[TRACKING] → [THRESHOLD_BREACHED] → [ALERTED] → [TRACKING]
[TRACKING] → [EXHAUSTED] → [PAUSED] → [RESUMED] → [TRACKING]
[TRACKING] → [EXHAUSTED] → [THROTTLED] → [TRACKING]
```

---

## Cleanup Inventory

| Resource | Created at step | Destroyed by | Destroy method |
|---|---|---|---|
| Budget records | Step 1 | Retention (1yr) | Archive after 1 year |
| Cost entries | Step 4 | Retention (90d) | Archive after 90 days |
| Cost reports | Step 9 | Retention (1yr) | Archive after 1 year |
| Alert records | Step 5 | Retention (30d) | Delete after 30 days |

---

## Test Cases

| Test | Trigger | Expected behavior |
|---|---|---|
| TC-01: Budget setup | Company subscription | Budget limits configured |
| TC-02: Goal allocation | Goal activated | Budget reserved from company pool |
| TC-03: Agent allocation | Agent created | Token budget assigned |
| TC-04: Cost tracking | Task execution | Costs recorded in real-time |
| TC-05: Warning alert | 70% usage | Warning alert sent |
| TC-06: Critical alert | 90% usage | Critical alert sent |
| TC-07: Hard limit | 100% usage | Execution paused/throttled |
| TC-08: Priority allocation | Competing tasks | Critical tasks get priority |
| TC-09: Deadline escalation | Deadline at risk | Priority increased, operator notified |
| TC-10: Budget reset | Monthly rollover | Budget resets, paused tasks resume |
| TC-11: Operator override | Manual budget increase | Execution resumes |
| TC-12: Cost report | Period end | Report generated with breakdown |

---

## Assumptions

| # | Assumption | Where verified | Risk if wrong |
|---|---|---|---|
| A1 | Token costs are predictable per model | Not verified | Budget estimates inaccurate |
| A2 | Monthly reset is sufficient for most use cases | Not verified | Companies need daily/hourly limits |
| A3 | Priority levels are respected by all agents | Not verified | Low-priority tasks starved |
| A4 | Cost tracking overhead is minimal | Not verified | Tracking itself consumes significant tokens |
| A5 | Alert channels are monitored | Not verified | Budget exhaustion goes unnoticed |

---

## Open Questions

- Should there be a "preemptible" task type that can be interrupted?
- How do we handle cost spikes from retry loops?
- Should companies be able to set per-agent token limits?
- How do we handle shared resources (e.g., a company-wide API quota)?
