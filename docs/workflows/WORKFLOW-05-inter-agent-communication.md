# WORKFLOW-05: Inter-Agent Communication Workflows

**Version**: 0.1
**Date**: 2026-07-28
**Author**: Workflow Architect
**Status**: Draft
**Implements**: Autonomous AI Workforce Platform — Agent Messaging, Broadcast, Pub/Sub, State Sync, Conflict Resolution

---

## Overview

Inter-Agent Communication enables agents to coordinate, share information, hand off work, and resolve conflicts. Communication happens at multiple scopes: direct (1:1), team (1:many within team), department (1:many within department), company-wide (broadcast), and cross-company (marketplace events).

---

## Actors

| Actor | Role in this workflow |
|---|---|
| Message Router | Routes messages between agents |
| Team Coordinator | Manages team-level communication |
| Department Coordinator | Manages department-level communication |
| Company Broadcaster | Handles company-wide broadcasts |
| Conflict Resolver | Mediates conflicting outputs or decisions |
| State Synchronizer | Keeps agent state consistent across the system |
| Event Bus | Pub/sub backbone for all communication |

---

## Prerequisites

- Agents are registered in the Agent Registry
- Communication channels are established
- Conflict resolution policies are configured
- Event Bus is operational

---

## Trigger

Communication is triggered by:
1. Agent completing a task and needing to hand off results
2. Agent needing information from another agent
3. Team/department coordination events
4. Conflict detection between agent outputs
5. State synchronization requirements

---

## State Diagram

```
[MESSAGE_CREATED] → [ROUTING] → [DELIVERED]
                       ↓
                 [QUEUED | FAILED]
                       ↓
                 [RETRYING] → [DELIVERED | DEAD_LETTER]
```

---

## Workflow Tree

### STEP 1: Message Creation
**Actor**: Sending Agent
**Action**: Agent creates a message with content, recipient, priority, and type
**Timeout**: 5s
**Input**: `{ sender_id: uuid, recipient: { type: enum, id: uuid }, content: object, message_type: enum, priority: enum }`
**Output on SUCCESS**: `{ message_id: uuid, status: "created" }` → GO TO STEP 2
**Output on FAILURE**:
- `FAILURE(sender_not_found)`: Sender agent doesn't exist → reject message
- `FAILURE(content_too_large)`: Message exceeds size limit → compress or summarize
- `FAILURE(rate_limited)`: Agent sending too fast → queue with backpressure

**Message Types**:
| Type | Description | Example |
|---|---|---|
| `task_handoff` | Results from completed task | "Here are the research results for project X" |
| `info_request` | Request for information | "What is the current budget status?" |
| `info_response` | Response to info request | "Budget is $340 remaining" |
| `coordination` | Coordination message | "I'm starting the content creation phase" |
| `alert` | Warning or alert | "Warning: deadline approaching in 2h" |
| `conflict` | Conflict declaration | "Your output conflicts with my analysis" |
| `state_update` | State synchronization | "I've moved to 'executing' status" |
| `handoff` | Work handoff | "Please take over this task" |

**Message Schema**:
```json
{
  "message_id": "uuid",
  "sender_id": "uuid",
  "recipient": {
    "type": "enum(agent|team|department|company|broadcast)",
    "id": "uuid | null (for broadcast)"
  },
  "content": {
    "subject": "string",
    "body": "string",
    "attachments": [{"type": "string", "data": "object", "size_bytes": "number"}],
    "context": {"task_id": "uuid", "dag_id": "uuid", "project_id": "uuid"}
  },
  "message_type": "enum",
  "priority": "enum(critical|high|medium|low)",
  "requires_response": "boolean",
  "response_timeout_seconds": "number",
  "created_at": "ISO8601"
}
```

---

### STEP 2: Message Routing
**Actor**: Message Router
**Action**: Determine routing based on recipient type and current system state
**Timeout**: 5s
**Input**: `{ message_id: uuid, recipient: object }`
**Output on SUCCESS**: `{ message_id: uuid, routed_to: "string", delivery_method: enum }` → GO TO STEP 3
**Output on FAILURE**:
- `FAILURE(recipient_not_found)`: Recipient doesn't exist → return to sender with error
- `FAILURE(recipient_busy)`: Recipient at max message capacity → queue with priority
- `FAILURE(recipient_offline)`: Recipient agent not running → queue for delivery when online
- `FAILURE(route_error)`: Routing logic fails → fallback to direct Event Bus delivery

**Routing Logic**:
```
IF recipient.type == 'agent':
  IF recipient.id in agent_registry AND agent.status != 'destroyed':
    ROUTE directly to agent's message queue
  ELSE:
    QUEUE for delivery when agent comes online
    
ELIF recipient.type == 'team':
  FIND all agents WHERE agent.team_id = recipient.id
  FOR each agent:
    COPY message, route to agent
    
ELIF recipient.type == 'department':
  FIND all teams WHERE team.department_id = recipient.id
  FOR each team:
    BROADCAST to team
    
ELIF recipient.type == 'company':
  FIND all agents WHERE agent.company_id = recipient.id
  BROADCAST to all (via Event Bus)
  
ELIF recipient.type == 'broadcast':
  BROADCAST to all agents in company
```

---

### STEP 3: Message Delivery
**Actor**: Message Router
**Action**: Deliver message to recipient's message queue or trigger callback
**Timeout**: 10s
**Input**: `{ message_id: uuid, recipient_id: uuid, delivery_method: enum }`
**Output on SUCCESS**: `{ message_id: uuid, status: "delivered", delivered_at: timestamp }` → GO TO STEP 4
**Output on FAILURE**:
- `FAILURE(delivery_failed)`: Queue unavailable → retry x3 with 5s backoff
- `FAILURE(queue_full)`: Recipient queue at capacity → drop lowest priority message, deliver new one
- `FAILURE(agent_unavailable)`: Agent not responding → queue, alert if critical

**Observable states**:
- Customer sees: No direct visibility (background)
- Operator sees: Message delivery status in communication logs
- Database: `messages.status = 'delivered'`
- Logs: `[message-router] delivered message_id=abc to agent_id=pqr`

---

### STEP 4: Message Processing
**Actor**: Receiving Agent
**Action**: Agent processes message, extracts relevant information, takes action if needed
**Timeout**: Message-specific (default 60s)
**Input**: `{ message_id: uuid, content: object, context: object }`
**Output on SUCCESS**: `{ message_id: uuid, status: "processed", response: object | null }` → END
**Output on FAILURE**:
- `FAILURE(process_error)`: Agent cannot process message → log error, return NACK
- `FAILURE(invalid_content)`: Message content malformed → return NACK with error
- `FAILURE(timeout)`: Processing timeout → return NACK, retry x1

**Processing Logic by Message Type**:
```
task_handoff:
  EXTRACT results
  INTEGRATE into current work context
  UPDATE task state if applicable
  
info_request:
  RETRIEVE requested information
  CREATE info_response message
  SEND response to sender
  
coordination:
  ACKNOWLEDGE receipt
  UPDATE coordination state
  ADJUST schedule if needed
  
alert:
  LOG alert
  TAKE appropriate action (pause, retry, escalate)
  
conflict:
  INITIATE conflict resolution (STEP 5)
```

---

### STEP 5: Conflict Resolution
**Actor**: Conflict Resolver
**Action**: When two or more agents produce conflicting outputs, mediate resolution
**Timeout**: 60s
**Input**: `{ conflict_id: uuid, conflicting_outputs: [{ agent_id, output, confidence }], context: object }`
**Output on SUCCESS**: `{ conflict_id: uuid, resolution: object, strategy: enum, winning_agent: uuid }` → END
**Output on FAILURE**:
- `FAILURE(unresolvable)`: Cannot automatically resolve → escalate to operator
- `FAILURE(timeout)`: Resolution timeout → use highest confidence output

**Conflict Resolution Strategies**:
```
1. CONFIDENCE_BASED:
   IF one output has significantly higher confidence:
     USE that output
   ELSE:
     ESCALATE to next strategy
     
2. REPUTATION_BASED:
   USE output from agent with higher historical performance score
   IF tie:
     ESCALATE to next strategy
     
3. CONSENSUS:
   IF multiple agents agree:
     USE consensus output
   ELSE:
     ESCALATE to next strategy
     
4. RULE_BASED:
   APPLY company-specific conflict resolution rules
   IF no rules match:
     ESCALATE to operator
     
5. OPERATOR_ADJUDICATION:
   PRESENT all outputs to operator with analysis
   WAIT for operator decision
```

**Observable states**:
- Customer sees: "Resolving conflict between agents..."
- Operator sees: Conflict alert with all outputs and suggested resolution
- Database: `conflicts` row inserted, `conflict_resolutions` updated
- Logs: `[conflict-resolver] conflict detected between agents pqr and stu, strategy=confidence_based`

**Conflict Schema**:
```json
{
  "conflict_id": "uuid",
  "conflicting_agents": [
    {
      "agent_id": "uuid",
      "agent_name": "string",
      "output": "object",
      "confidence": "number 0-1",
      "reasoning": "string"
    }
  ],
  "context": {
    "task_id": "uuid",
    "dag_id": "uuid",
    "project_id": "uuid"
  },
  "resolution": {
    "strategy": "string",
    "winning_output": "object",
    "losing_agents_notified": ["uuid"],
    "reasoning": "string"
  },
  "created_at": "ISO8601",
  "resolved_at": "ISO8601"
}
```

---

### STEP 6: State Synchronization
**Actor**: State Synchronizer
**Action**: Keep agent state consistent across the system when state changes occur
**Timeout**: 10s
**Input**: `{ agent_id: uuid, state_change: { field: string, old_value: any, new_value: any } }`
**Output on SUCCESS**: `{ agent_id: uuid, synced: true, affected_subscribers: number }` → END
**Output on FAILURE**:
- `FAILURE(sync_error)`: Cannot propagate state change → retry x3 with 2s backoff
- `FAILURE(stale_data)`: State already changed → use latest state, log conflict

**State Synchronization Flow**:
```
1. Agent updates local state
2. State Synchronizer receives state change event
3. VALIDATE state transition is legal
4. PERSIST to database
5. PUBLISH state change to Event Bus
6. NOTIFY all subscribed agents of state change
7. VERIFY eventual consistency (async check)
```

**Synchronized Fields**:
| Field | Sync Scope | Latency Requirement |
|---|---|---|
| `status` | Company-wide | < 1s |
| `current_task` | Team | < 2s |
| `performance_score` | Company-wide | < 5s |
| `available_capabilities` | Company-wide | < 5s |
| `token_budget_remaining` | Company-wide | < 10s |

---

### STEP 7: Broadcast Communication
**Actor**: Company Broadcaster
**Action**: Send message to all agents in a company or department
**Timeout**: 30s
**Input**: `{ sender_id: uuid, scope: enum, content: object, priority: enum }`
**Output on SUCCESS**: `{ broadcast_id: uuid, delivered_count: number, total_count: number }` → END
**Output on FAILURE**:
- `FAILURE(partial_delivery)`: Some agents didn't receive → retry for failed agents
- `FAILURE(broadcast_timeout)`: Delivery taking too long → complete partial, log failures

**Observable states**:
- Customer sees: No direct visibility
- Operator sees: Broadcast in progress, delivery count
- Database: `broadcasts` row inserted
- Logs: `[broadcaster] broadcast_id=xyz, scope=company, delivered=47/50`

**Broadcast Types**:
```
COMPANY_WIDE:
  ALL agents in company receive
  Used for: policy changes, budget updates, emergency alerts
  
DEPARTMENT_WIDE:
  ALL agents in department receive
  Used for: department coordination, team announcements
  
TEAM_WIDE:
  ALL agents in team receive
  Used for: task coordination, team status updates
  
WAVE_ANNOUNCEMENT:
  ALL agents in current DAG wave receive
  Used for: wave start, wave complete, emergency stop
```

---

## State Transitions

```
[MESSAGE_CREATED] → [ROUTING] → [DELIVERED] → [PROCESSED]
[ROUTING] → [QUEUED] → [DELIVERED] → [PROCESSED]
[ROUTING] → [FAILED] → [RETRYING] → [DELIVERED | DEAD_LETTER]
[PROCESSED] → (if conflict) → [CONFLICT] → [RESOLVED]
```

---

## Handoff Contracts

### Agent → Message Router
**Endpoint**: `POST /internal/messages/send`
**Payload**: `{ message object per Message Schema }`
**Success response**: `{ ok: true, message_id: "uuid" }`
**Timeout**: 5s

### Message Router → Agent
**Endpoint**: `POST /internal/messages/receive`
**Payload**: `{ message object per Message Schema }`
**Success response**: `{ ok: true, status: "received" }`
**Timeout**: 60s

### Conflict Resolver → Operator
**Endpoint**: `POST /api/v1/conflicts/{conflict_id}/resolve`
**Payload**:
```json
{
  "conflict_id": "uuid",
  "conflicting_outputs": [{"agent_id": "uuid", "output": "object", "confidence": "number"}],
  "suggested_resolution": "object",
  "options": ["accept_suggested", "manual_select", "skip"]
}
```
**Success response**: `{ ok: true, resolution: "object" }`
**Timeout**: None (waits for operator)

---

## Cleanup Inventory

| Resource | Created at step | Destroyed by | Destroy method |
|---|---|---|---|
| Messages | Step 1 | Retention policy (7d) | `DELETE FROM messages WHERE created_at < now() - 7d` |
| Message queues | Step 2 | Agent destruction | `DELETE FROM message_queues WHERE agent_id = ?` |
| Conflict records | Step 5 | Retention policy (30d) | `DELETE FROM conflicts WHERE created_at < now() - 30d` |
| Broadcast records | Step 7 | Retention policy (24h) | `DELETE FROM broadcasts WHERE created_at < now() - 24h` |

---

## Test Cases

| Test | Trigger | Expected behavior |
|---|---|---|
| TC-01: Direct message | Agent sends to specific agent | Message delivered within 5s |
| TC-02: Team broadcast | Message to team of 5 agents | All 5 agents receive within 10s |
| TC-03: Company broadcast | Company-wide message | All agents receive within 30s |
| TC-04: Offline recipient | Message to non-running agent | Message queued, delivered when agent starts |
| TC-05: Conflict detection | Two agents produce conflicting outputs | Conflict detected, resolution initiated |
| TC-06: Conflict auto-resolve | One output has higher confidence | Automatic resolution, losing agent notified |
| TC-07: Conflict escalation | No clear winner | Escalated to operator |
| TC-08: State sync | Agent status changes | All subscribers notified within 1s |
| TC-09: Message queue full | Recipient at capacity | Lowest priority message dropped |
| TC-10: Broadcast failure | Partial delivery | Retries for failed agents |
| TC-11: Large message | Message > 1MB | Compressed or summarized |
| TC-12: Concurrent conflicts | Multiple conflicts simultaneously | Each resolved independently |

---

## Assumptions

| # | Assumption | Where verified | Risk if wrong |
|---|---|---|---|
| A1 | Event Bus provides ordered delivery within a topic | Not verified | Out-of-order messages |
| A2 | Agent message queues are durable | Not verified | Messages lost on crash |
| A3 | Conflict resolution strategies are configurable per company | Not verified | One-size-fits-all doesn't work |
| A4 | State synchronization is eventually consistent | Not verified | Stale data used in decisions |
| A5 | Broadcast delivery is best-effort | Not verified | Critical messages missed |

---

## Open Questions

- Should agents be able to ignore or deprioritize messages?
- How do we handle message ordering within a conversation thread?
- Should there be a "message audit trail" for compliance?
- How do we handle cross-company communication (e.g., marketplace interactions)?
