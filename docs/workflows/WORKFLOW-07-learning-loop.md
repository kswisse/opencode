# WORKFLOW-07: Learning Loop Flows

**Version**: 0.1
**Date**: 2026-07-28
**Author**: Workflow Architect
**Status**: Draft
**Implements**: Autonomous AI Workforce Platform — Post-Task Reflection, Self-Critique, A/B Testing, KPI Optimization, Skill Evolution, Knowledge Transfer

---

## Overview

The Learning Loop continuously improves agent performance through structured reflection, self-critique, A/B testing of prompts and strategies, KPI optimization, skill evolution, and cross-agent knowledge transfer. Learning happens asynchronously after task execution and is applied before future task execution.

---

## Actors

| Actor | Role in this workflow |
|---|---|
| Reflection Engine | Triggers and processes post-task reflections |
| Self-Critique Module | Evaluates agent performance against criteria |
| A/B Test Manager | Manages prompt and strategy experiments |
| KPI Optimizer | Tracks and optimizes key performance indicators |
| Skill Evolution Engine | Evolves agent capabilities over time |
| Knowledge Transfer Agent | Shares learnings between agents |
| Learning Store | Persists learning outcomes |
| Event Bus | Publishes learning events |

---

## Prerequisites

- Memory system operational (WORKFLOW-06)
- Performance evaluation data available (WORKFLOW-02)
- A/B testing infrastructure configured
- KPI baselines established

---

## Trigger

Learning loops are triggered by:
1. Task completion (post-task reflection)
2. Periodic review (daily/weekly KPI optimization)
3. Performance threshold breach (self-critique)
4. Agent capability gap detected (skill evolution)
5. Similar task pattern detected (knowledge transfer)

---

## State Diagram

```
[LEARNING_TRIGGERED] → [ANALYZING] → [ANALYZED] → [LEARNING] → [LEARNED] → [APPLIED]
                                ↓                   ↓              ↓
                         [NO_LEARNINGS]      [EXPERIMENTING]  [STORING]
                                                        ↓
                                                  [STORED]
```

---

## Workflow Tree

### STEP 1: Post-Task Reflection
**Actor**: Reflection Engine
**Action**: After task completion, trigger reflection to identify what worked, what didn't, and what could improve
**Timeout**: 60s (background)
**Input**: `{ agent_id: uuid, task_id: uuid, output: object, performance_score: number, metrics: object }`
**Output on SUCCESS**: `{ reflection_id: uuid, insights: object }` → GO TO STEP 2
**Output on FAILURE**:
- `FAILURE(reflection_error)`: Cannot generate reflection → skip (task still completed)
- `FAILURE(timeout)`: Reflection timeout → defer to background queue

**Reflection Process**:
```
1. COMPARE actual output to expected output
2. ANALYZE what approaches succeeded
3. ANALYZE what approaches failed or underperformed
4. IDENTIFY specific improvement opportunities:
   - Prompt engineering improvements
   - Tool selection changes
   - Strategy modifications
   - Resource allocation adjustments
5. GENERATE reflection summary
6. STORE reflection in memory
```

**Reflection Schema**:
```json
{
  "reflection_id": "uuid",
  "agent_id": "uuid",
  "task_id": "uuid",
  "performance_score": "number",
  "what_worked": [
    {
      "aspect": "string",
      "description": "string",
      "confidence": "number 0-1"
    }
  ],
  "what_failed": [
    {
      "aspect": "string",
      "description": "string",
      "root_cause": "string",
      "confidence": "number 0-1"
    }
  ],
  "improvement_opportunities": [
    {
      "area": "string",
      "suggestion": "string",
      "expected_impact": "enum(low|medium|high)",
      "implementation_effort": "enum(low|medium|high)"
    }
  ],
  "created_at": "ISO8601"
}
```

---

### STEP 2: Self-Critique
**Actor**: Self-Critique Module
**Action**: Agent evaluates its own performance against predefined criteria
**Timeout**: 30s
**Input**: `{ agent_id: uuid, task_id: uuid, reflection: object, criteria: object }`
**Output on SUCCESS**: `{ critique_id: uuid, score: number, areas_for_improvement: [...] }` → GO TO STEP 3
**Output on FAILURE**:
- `FAILURE(critique_error)`: Cannot self-critique → use external evaluation
- `FAILURE(bias_detected)`: Self-critique may be biased → flag for external review

**Self-Critique Criteria**:
```json
{
  "criteria": {
    "accuracy": {
      "weight": 0.3,
      "description": "Is the output factually correct?"
    },
    "completeness": {
      "weight": 0.25,
      "description": "Does the output address all requirements?"
    },
    "efficiency": {
      "weight": 0.2,
      "description": "Was the task completed with minimal resources?"
    },
    "creativity": {
      "weight": 0.15,
      "description": "Does the output show novel approaches?"
    },
    "clarity": {
      "weight": 0.1,
      "description": "Is the output well-structured and clear?"
    }
  }
}
```

---

### STEP 3: A/B Testing Pipeline
**Actor**: A/B Test Manager
**Action**: When improvement opportunity is identified, create A/B test to validate improvement
**Timeout**: 30s
**Input**: `{ improvement: object, agent_id: uuid, task_type: string }`
**Output on SUCCESS**: `{ experiment_id: uuid, variant: "control" | "treatment", status: "running" }` → GO TO STEP 4
**Output on FAILURE**:
- `FAILURE(experiment_error)`: Cannot create experiment → apply improvement directly (skip validation)
- `FAILURE(quota_exceeded)`: Too many active experiments → queue for later

**A/B Testing Process**:
```
1. IDENTIFY testable improvement
   - Prompt modification
   - Strategy change
   - Tool substitution
   - Parameter adjustment
2. CREATE experiment:
   - Control: current approach
   - Treatment: improved approach
3. ASSIGN tasks to control/treatment (50/50 split)
4. COLLECT performance metrics
5. EVALUATE statistical significance
6. DECIDE: adopt treatment, keep control, or extend experiment
```

**Experiment Schema**:
```json
{
  "experiment_id": "uuid",
  "company_id": "uuid",
  "agent_id": "uuid",
  "task_type": "string",
  "hypothesis": "string",
  "control": {
    "prompt": "string",
    "strategy": "string",
    "parameters": "object"
  },
  "treatment": {
    "prompt": "string",
    "strategy": "string",
    "parameters": "object"
  },
  "metrics": {
    "primary": "string — e.g., 'quality_score'",
    "secondary": ["string — e.g., 'tokens_used', 'time_seconds'"]
  },
  "status": "enum(setup|running|evaluated|concluded)",
  "results": {
    "control": {"sample_size": "number", "mean": "number", "std_dev": "number"},
    "treatment": {"sample_size": "number", "mean": "number", "std_dev": "number"},
    "p_value": "number",
    "significant": "boolean",
    "winner": "enum(control|treatment|inconclusive)"
  },
  "created_at": "ISO8601",
  "concluded_at": "ISO8601"
}
```

---

### STEP 4: Experiment Monitoring
**Actor**: A/B Test Manager
**Action**: Monitor running experiments, collect data, evaluate results
**Timeout**: Background (until experiment concludes)
**Input**: `{ experiment_id: uuid }`
**Output on SUCCESS**: `{ experiment_id: uuid, status: "evaluated", results: object }` → GO TO STEP 5
**Output on FAILURE**:
- `FAILURE(insufficient_data)`: Not enough samples → extend experiment
- `FAILURE(experiment_error)`: Data collection fails → use available data

**Monitoring Logic**:
```
EVERY 1h:
  COLLECT metrics for control and treatment groups
  UPDATE running statistics
  CHECK if minimum sample size reached (n >= 30 per group)
  IF sample size reached:
    CALCULATE statistical significance (p < 0.05)
    IF significant:
      CONCLUDE experiment
    ELIF experiment_running > 7 days:
      CONCLUDE with available data (flag as underpowered)
```

---

### STEP 5: Learning Application
**Actor**: Learning Store
**Action**: Apply winning experiment variant to future task execution
**Timeout**: 10s
**Input**: `{ experiment_id: uuid, winner: "control" | "treatment", agent_id: uuid }`
**Output on SUCCESS**: `{ learning_id: uuid, applied: true }` → GO TO STEP 6
**Output on FAILURE**:
- `FAILURE(application_error)`: Cannot apply learning → store for manual application

**Application Process**:
```
IF winner == 'treatment':
  UPDATE agent's default prompt/strategy/parameters
  STORE learning in agent's semantic memory
  UPDATE agent's performance baseline
  NOTIFY operator of improvement
ELIF winner == 'control':
  STORE negative learning (this improvement didn't work)
  LOG for future reference
ELSE:
  FLAG as inconclusive, keep current approach
```

---

### STEP 6: KPI Optimization Loop
**Actor**: KPI Optimizer
**Action**: Periodically review company-wide KPIs, identify optimization opportunities
**Timeout**: 120s (daily background job)
**Input**: `{ company_id: uuid, period: enum(daily|weekly|monthly) }`
**Output on SUCCESS**: `{ optimization_id: uuid, recommendations: [...] }` → GO TO STEP 7
**Output on FAILURE**:
- `FAILURE(optimization_error)`: Cannot compute optimizations → skip until next cycle

**KPI Tracking**:
```json
{
  "kpis": {
    "task_completion_rate": {
      "current": "number",
      "target": "number",
      "trend": "enum(improving|stable|declining)"
    },
    "average_quality_score": {
      "current": "number",
      "target": "number",
      "trend": "enum"
    },
    "cost_per_task": {
      "current": "number",
      "target": "number",
      "trend": "enum"
    },
    "average_time_per_task": {
      "current": "number",
      "target": "number",
      "trend": "enum"
    },
    "agent_utilization": {
      "current": "number",
      "target": "number",
      "trend": "enum"
    },
    "failure_rate": {
      "current": "number",
      "target": "number",
      "trend": "enum"
    }
  }
}
```

**Optimization Recommendations**:
```
IF task_completion_rate < target:
  RECOMMEND: Review failure patterns, adjust retry policies
  
IF average_quality_score < target:
  RECOMMEND: Run A/B tests on prompts, increase reflection frequency
  
IF cost_per_task > target:
  RECOMMEND: Optimize token usage, use cheaper models for low-complexity tasks
  
IF agent_utilization < 0.5:
  RECOMMEND: Reduce agent count, consolidate tasks
  
IF failure_rate > 0.1:
  RECOMMEND: Review error patterns, improve agent training
```

---

### STEP 7: Skill Evolution
**Actor**: Skill Evolution Engine
**Action**: When agent consistently performs well in a domain, evolve their capabilities
**Timeout**: 30s
**Input**: `{ agent_id: uuid, domain: string, performance_history: [...] }`
**Output on SUCCESS**: `{ agent_id: uuid, evolved: true, new_capabilities: [...] }` → END
**Output on FAILURE**:
- `FAILURE(evolution_error)`: Cannot evolve → continue with current capabilities

**Skill Evolution Process**:
```
1. IDENTIFY domain where agent has >20 tasks with score >0.8
2. EXTRACT common patterns from successful tasks
3. CREATE new skill/capability definition
4. UPDATE agent's capability profile
5. STORE evolved skill for potential reuse in other agents
6. NOTIFY operator of capability upgrade
```

**Evolved Skill Schema**:
```json
{
  "skill_id": "uuid",
  "agent_id": "uuid",
  "domain": "string",
  "capability": "string",
  "description": "string",
  "prompt_patterns": ["string"],
  "tool_preferences": ["string"],
  "parameters": "object",
  "evidence_count": "number",
  "confidence": "number 0-1",
  "created_at": "ISO8601"
}
```

---

### STEP 8: Cross-Agent Knowledge Transfer
**Actor**: Knowledge Transfer Agent
**Action**: When one agent learns something valuable, transfer that knowledge to other agents
**Timeout**: 30s
**Input**: `{ source_agent_id: uuid, target_agents: [uuid], knowledge: object }`
**Output on SUCCESS**: `{ transfer_id: uuid, transferred_to: number }` → END
**Output on FAILURE**:
- `FAILURE(transfer_error)`: Cannot transfer → store in company memory for later retrieval

**Knowledge Transfer Process**:
```
1. IDENTIFY knowledge worth transferring:
   - High-confidence insights (score > 0.8)
   - Applicable to multiple task types
   - Not already known by target agents
2. ADAPT knowledge for target agents' context
3. INJECT into target agents' memory
4. VERIFY transfer was effective (test task)
5. UPDATE knowledge with transfer evidence
```

---

## State Transitions

```
[LEARNING_TRIGGERED] → [ANALYZING] → [ANALYZED]
[ANALYZED] → [LEARNING] → [LEARNED] → [APPLIED]
[ANALYZED] → [EXPERIMENTING] → [EVALUATED] → [APPLIED]
[ANALYZED] → [NO_LEARNINGS] (terminal)
```

---

## Cleanup Inventory

| Resource | Created at step | Destroyed by | Destroy method |
|---|---|---|---|
| Reflections | Step 1 | Retention (90d) | `DELETE FROM reflections WHERE created_at < now() - 90d` |
| Critiques | Step 2 | Retention (90d) | `DELETE FROM critiques WHERE created_at < now() - 90d` |
| Experiments | Step 3 | Retention (30d) | `DELETE FROM experiments WHERE created_at < now() - 30d` |
| Learned skills | Step 7 | Agent destruction | Archive for future agents |
| Transfer records | Step 8 | Retention (30d) | `DELETE FROM knowledge_transfers WHERE created_at < now() - 30d` |

---

## Test Cases

| Test | Trigger | Expected behavior |
|---|---|---|
| TC-01: Post-task reflection | Task completes with score > 0.7 | Reflection generated within 60s |
| TC-02: Self-critique | After reflection | Critique generated with improvement areas |
| TC-03: A/B test creation | Improvement opportunity identified | Experiment created, tasks split |
| TC-04: Experiment evaluation | Sufficient data collected | Statistical significance computed |
| TC-05: Learning application | Treatment wins | Agent updated with new approach |
| TC-06: KPI optimization | Daily/weekly schedule | Recommendations generated |
| TC-07: Skill evolution | >20 tasks with score > 0.8 | New capability added to agent |
| TC-08: Knowledge transfer | Valuable insight discovered | Knowledge shared with related agents |
| TC-09: Experiment failure | Insufficient data | Experiment extended or concluded as underpowered |
| TC-10: Learning conflict | New learning contradicts old | Conflict flagged for operator review |
| TC-11: Concurrent experiments | Multiple experiments running | Each isolated, no cross-contamination |
| TC-12: Learning decay | Old learning no longer valid | TTL-based expiration, re-validation |

---

## Assumptions

| # | Assumption | Where verified | Risk if wrong |
|---|---|---|---|
| A1 | Statistical significance is achievable with available task volume | Not verified | Experiments never conclude |
| A2 | Self-critique is sufficiently unbiased | Not verified | Agent over/under-estimates performance |
| A3 | Knowledge transfer is effective across different agent types | Not verified | Knowledge doesn't generalize |
| A4 | KPI baselines are meaningful | Not verified | Optimization targets are arbitrary |
| A5 | Learning application actually improves performance | Not verified | Circular or no improvement |

---

## Open Questions

- Should there be a "learning budget" to limit how much tokens are spent on reflection?
- How do we handle learning that becomes outdated (e.g., API changes)?
- Should operators be able to override or disable specific learnings?
- How do we prevent "overfitting" to specific task types?
