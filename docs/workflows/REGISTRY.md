# REGISTRY: Autonomous AI Workforce Platform

**Last Updated**: 2026-07-28
**Maintained by**: Workflow Architect

---

## View 1: By Workflow (Master List)

| # | Workflow | Spec File | Status | Trigger | Primary Actor | Last Reviewed |
|---|---|---|---|---|---|---|
| 01 | Goal Decomposition Pipeline | WORKFLOW-01-goal-decomposition.md | Draft | POST /goals | CEO Agent | 2026-07-28 |
| 02 | Agent Lifecycle | WORKFLOW-02-agent-lifecycle.md | Draft | GoalActivated event | Agent Factory | 2026-07-28 |
| 03 | Task Execution DAGs | WORKFLOW-03-task-execution-dags.md | Draft | GoalActivated event | DAG Scheduler | 2026-07-28 |
| 04 | Failure Recovery | WORKFLOW-04-failure-recovery.md | Draft | Agent/task failure signals | Recovery Orchestrator | 2026-07-28 |
| 05 | Inter-Agent Communication | WORKFLOW-05-inter-agent-communication.md | Draft | Agent message creation | Message Router | 2026-07-28 |
| 06 | Memory Read/Write | WORKFLOW-06-memory-read-write.md | Draft | Task completion / pre-task | Memory System | 2026-07-28 |
| 07 | Learning Loop | WORKFLOW-07-learning-loop.md | Draft | Task completion / periodic | Reflection Engine | 2026-07-28 |
| 08 | Marketplace | WORKFLOW-08-marketplace.md | Draft | Publisher submission / Consumer install | Marketplace System | 2026-07-28 |
| 09 | Resource Allocation | WORKFLOW-09-resource-allocation.md | Draft | Goal activation / Cost tracking | Budget Manager | 2026-07-28 |
| 10 | Multi-Company Isolation | WORKFLOW-10-multi-company-isolation.md | Draft | Every data/agent operation | Isolation Enforcer | 2026-07-28 |

**Status Legend**: `Approved` | `Review` | `Draft` | `Missing` | `Deprecated`

---

## View 2: By Component (Code → Workflows)

| Component | Workflows it Participates in |
|---|---|
| CEO Agent | 01-Goal Decomposition, 02-Agent Lifecycle |
| Goal Parser Service | 01-Goal Decomposition |
| Planner Agent | 01-Goal Decomposition, 03-Task Execution DAGs |
| Agent Factory | 02-Agent Lifecycle, 04-Failure Recovery |
| Agent Registry | 02-Agent Lifecycle, 05-Inter-Agent Communication, 10-Multi-Company Isolation |
| Skill Calibrator | 02-Agent Lifecycle |
| Task Executor | 02-Agent Lifecycle, 03-Task Execution DAGs |
| Performance Evaluator | 02-Agent Lifecycle, 07-Learning Loop |
| DAG Scheduler | 03-Task Execution DAGs |
| Task Dispatcher | 03-Task Execution DAGs |
| Checkpoint Manager | 03-Task Execution DAGs, 04-Failure Recovery |
| Result Aggregator | 03-Task Execution DAGs |
| Recovery Orchestrator | 04-Failure Recovery |
| Agent Resurrector | 04-Failure Recovery |
| Circuit Breaker | 04-Failure Recovery |
| Dead Letter Processor | 04-Failure Recovery |
| Message Router | 05-Inter-Agent Communication |
| Conflict Resolver | 05-Inter-Agent Communication, 07-Learning Loop |
| State Synchronizer | 05-Inter-Agent Communication |
| Memory System | 02-Agent Lifecycle, 06-Memory Read/Write, 07-Learning Loop |
| Vector Memory Indexer | 06-Memory Read/Write |
| Memory Consolidator | 06-Memory Read/Write |
| Reflection Engine | 07-Learning Loop |
| A/B Test Manager | 07-Learning Loop |
| KPI Optimizer | 07-Learning Loop |
| Skill Evolution Engine | 07-Learning Loop |
| Marketplace System | 08-Marketplace |
| Template Validator | 08-Marketplace |
| Revenue Engine | 08-Marketplace |
| Budget Manager | 09-Resource Allocation |
| Token Allocator | 09-Resource Allocation |
| Cost Tracker | 09-Resource Allocation |
| Deadline Enforcer | 09-Resource Allocation |
| Isolation Enforcer | 10-Multi-Company Isolation |
| Data Isolator | 10-Multi-Company Isolation |
| Security Monitor | 10-Multi-Company Isolation |
| Audit Logger | 10-Multi-Company Isolation |
| Event Bus | 01, 02, 03, 04, 05, 06, 07, 08, 09, 10 (all workflows) |
| Database | 01, 02, 03, 04, 05, 06, 07, 08, 09, 10 (all workflows) |

---

## View 3: By User Journey

### Company Operator Journeys

| What the operator experiences | Underlying workflow(s) | Entry point |
|---|---|---|
| Creates company account | 10-Multi-Company Isolation (setup) | POST /companies |
| Submits a goal ("Earn $10k/month") | 01-Goal Decomposition | POST /goals |
| Reviews and approves plan | 01-Goal Decomposition (approval) | UI approve button |
| Monitors agent execution | 02-Agent Lifecycle, 03-Task Execution | Dashboard |
| Handles failed tasks | 04-Failure Recovery | Dead letter queue UI |
| Reviews agent performance | 02-Agent Lifecycle (evaluation) | Agent dashboard |
| Manages budget | 09-Resource Allocation | Budget settings |
| Installs marketplace template | 08-Marketplace | Marketplace browse |
| Publishes template to marketplace | 08-Marketplace | Publisher portal |
| Reviews compliance report | 10-Multi-Company Isolation | Compliance dashboard |
| Configures agent preferences | 06-Memory Read/Write (user memory) | Settings |

### Platform Administrator Journeys

| What the admin does | Underlying workflow(s) | Entry point |
|---|---|---|
| Monitors all companies | 10-Multi-Company Isolation (monitoring) | Admin dashboard |
| Reviews security alerts | 10-Multi-Company Isolation (security) | Alert panel |
| Manages marketplace listings | 08-Marketplace (moderation) | Moderation queue |
| Processes revenue payouts | 08-Marketplace (revenue) | Finance dashboard |
| Tuning system-wide KPIs | 07-Learning Loop (KPI optimization) | Admin settings |
| Handling escalated failures | 04-Failure Recovery (escalation) | Escalation queue |

### System-to-System Journeys

| What happens automatically | Underlying workflow(s) | Trigger |
|---|---|---|
| Goal decomposed into projects | 01-Goal Decomposition | GoalActivated |
| Agents created for tasks | 02-Agent Lifecycle | GoalActivated |
| Tasks dispatched in waves | 03-Task Execution DAGs | DAG initialization |
| Failures detected and recovered | 04-Failure Recovery | Health check / timeout |
| Memory written after task | 06-Memory Read/Write | Task completion |
| Learning loop runs reflection | 07-Learning Loop | Task completion |
| Budget throttling applied | 09-Resource Allocation | Quota threshold |
| Isolation check on every operation | 10-Multi-Company Isolation | Every operation |
| Monthly billing processed | 08-Marketplace (revenue) | Monthly schedule |
| Compliance report generated | 10-Multi-Company Isolation | Monthly schedule |

---

## View 4: By State (State → Workflows)

| State | Entered by | Exited by | Workflows that can trigger exit |
|---|---|---|---|
| SUBMITTED | Goal submission | → PARSING, REJECTED | 01-Goal Decomposition |
| PARSING | Goal parsing | → PARSED, PARSE_ERROR | 01-Goal Decomposition |
| PARSED | Parse success | → DECOMPOSING | 01-Goal Decomposition |
| DECOMPOSING | CEO decomposition | → DECOMPOSED, DECOMP_ERROR | 01-Goal Decomposition |
| DECOMPOSED | Decomposition success | → PLANNING | 01-Goal Decomposition |
| PLANNING | Task DAG construction | → PLANNED, PLANNING_FAILED | 01-Goal Decomposition |
| PLANNED | Plan validation | → ACTIVE, REJECTED | 01-Goal Decomposition |
| ACTIVE | Operator approval | → COMPLETED, FAILED | 01-Goal Decomposition |
| CREATING | Agent instantiation | → CREATED, CREATION_FAILED | 02-Agent Lifecycle |
| CREATED | Agent creation | → CALIBRATING | 02-Agent Lifecycle |
| CALIBRATING | Skill calibration | → CALIBRATED, CAL_ERROR | 02-Agent Lifecycle |
| CALIBRATED | Calibration success | → IDLE | 02-Agent Lifecycle |
| IDLE | Agent ready | → ASSIGNED, DESTROYING | 02-Agent Lifecycle |
| ASSIGNED | Task assignment | → EXECUTING | 02-Agent Lifecycle, 03-Task Execution |
| EXECUTING | Task start | → EVALUATING, FAILED, TIMEOUT | 02-Agent Lifecycle, 03-Task Execution |
| EVALUATING | Task completion | → IDLE (reuse), DESTROYING | 02-Agent Lifecycle |
| DESTROYING | Destruction start | → DESTROYED | 02-Agent Lifecycle |
| DAG_READY | DAG initialization | → WAVE_SCHEDULING | 03-Task Execution |
| WAVE_SCHEDULING | Wave preparation | → WAVE_RUNNING | 03-Task Execution |
| WAVE_RUNNING | Wave execution | → WAVE_COMPLETE, WAVE_FAILED | 03-Task Execution |
| WAVE_COMPLETE | Wave success | → NEXT_WAVE, DAG_COMPLETE | 03-Task Execution |
| DAG_COMPLETE | All waves done | (terminal) | 03-Task Execution |
| DAG_FAILED | Unrecoverable failure | (terminal, resume from checkpoint) | 03-Task Execution |
| FAILURE_DETECTED | Failure signal | → CLASSIFYING | 04-Failure Recovery |
| RECOVERING | Recovery attempt | → RECOVERED, RECOVERY_FAILED | 04-Failure Recovery |
| DEAD_LETTER | Unrecoverable | → MANUAL_REVIEW | 04-Failure Recovery |
| LISTED | Template approved | → DELISTED | 08-Marketplace |
| INSTALLED | Consumer install | → CONFIGURED | 08-Marketplace |
| ALLOCATED | Budget set | → DISTRIBUTED, EXHAUSTED | 09-Resource Allocation |
| TRACKING | Active monitoring | → THRESHOLD_BREACHED, EXHAUSTED | 09-Resource Allocation |
| ISOLATION_ACTIVE | Company created | → MONITORING | 10-Multi-Company Isolation |
| MONITORING | Continuous | → VIOLATION_DETECTED | 10-Multi-Company Isolation |

---

## Cross-Workflow Event Flow

```
User submits goal
  │
  ▼
[01-Goal Decomposition] ──GoalActivated──▶ [02-Agent Lifecycle]
  │                                          │
  │                                          ▼
  │                                     [03-Task Execution DAGs]
  │                                          │
  │                      ┌────────────────────┼────────────────────┐
  │                      ▼                    ▼                    ▼
  │               [Agent Executes]    [Memory Write]      [Cost Tracking]
  │                      │                    │                    │
  │                      ▼                    ▼                    ▼
  │               [04-Failure Recovery] [06-Memory Read/Write] [09-Resource Allocation]
  │                      │                    │                    │
  │                      │                    ▼                    │
  │                      │            [07-Learning Loop]          │
  │                      │                    │                    │
  │                      ▼                    ▼                    ▼
  │               [05-Inter-Agent Communication] ◄────────────────┘
  │
  ▼
[10-Multi-Company Isolation] ──enforced at every step──▶ ALL WORKFLOWS
```

---

## Workflow Dependencies

| Workflow | Depends On | Depended By |
|---|---|---|
| 01-Goal Decomposition | — | 02, 03, 09 |
| 02-Agent Lifecycle | 01 | 03, 04, 05 |
| 03-Task Execution DAGs | 01, 02 | 04, 05, 06 |
| 04-Failure Recovery | 02, 03 | 02 (resurrection) |
| 05-Inter-Agent Communication | 02, 03 | 04, 07 |
| 06-Memory Read/Write | 02, 03 | 07 |
| 07-Learning Loop | 02, 03, 06 | 02 (improvement) |
| 08-Marketplace | 02 | 09 |
| 09-Resource Allocation | 01, 02 | 03 (budget enforcement) |
| 10-Multi-Company Isolation | — | ALL (enforced at every step) |

---

## Critical Paths

1. **Goal → Execution**: 01 → 02 → 03 → Agent executes → 06 → 07
2. **Failure Recovery**: 03 → 04 → 02 (resurrection) → 03 (re-execute)
3. **Learning Loop**: 03 → 06 → 07 → 02 (improvement) → 03 (better execution)
4. **Marketplace Revenue**: 08 (install) → 02 (execution) → 08 (revenue share)
5. **Budget Enforcement**: 01 (allocation) → 09 (tracking) → 03 (throttle if needed)

---

## Gaps & Missing Workflows

| # | Gap | Severity | Notes |
|---|---|---|---|
| 1 | Company onboarding workflow | Medium | Company creation + isolation setup (partially in 10) |
| 2 | Subscription/billing workflow | Medium | Plan management, payment processing |
| 3 | User authentication workflow | High | Login, token management, session handling |
| 4 | Admin intervention workflow | Medium | When operators need to manually intervene in agent execution |
| 5 | Data export/GDPR workflow | High | Data portability and right to deletion |
| 6 | Disaster recovery workflow | High | Platform-level backup and restore |
| 7 | Agent-to-agent negotiation | Low | Agents negotiating task allocation autonomously |
