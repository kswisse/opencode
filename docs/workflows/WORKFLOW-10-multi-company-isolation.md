# WORKFLOW-10: Multi-Company Isolation Flows

**Version**: 0.1
**Date**: 2026-07-28
**Author**: Workflow Architect
**Status**: Draft
**Implements**: Autonomous AI Workforce Platform — Data Isolation, Agent Isolation, Resource Quotas, Cross-Company Marketplace

---

## Overview

Multi-Company Isolation ensures that each company's data, agents, resources, and operations are completely isolated from other companies. This is the security and compliance backbone of the multi-tenant platform. Isolation covers data storage, agent execution, memory, communication, and resource consumption.

---

## Actors

| Actor | Role in this workflow |
|---|---|
| Isolation Enforcer | Validates and enforces company boundaries |
| Data Isolator | Ensures data is stored and accessed per-company |
| Agent Isolator | Prevents cross-company agent interaction |
| Resource Quota Manager | Enforces per-company resource limits |
| Audit Logger | Records all cross-company boundary events |
| Security Monitor | Detects isolation violations |
| Event Bus | Company-scoped event channels |

---

## Prerequisites
- Company tenant records exist
- Data storage is configured with company scoping
- Agent registry enforces company boundaries
- Audit logging is enabled

---

## Trigger

Isolation is enforced at every workflow touchpoint. Specific triggers include:
1. Company creation (isolation setup)
2. Data access (boundary check)
3. Agent creation (scope enforcement)
4. Resource consumption (quota enforcement)
5. Marketplace interaction (cross-company access)
6. Suspicious activity detection

---

## State Diagram

```
[COMPANY_CREATED] → [ISOLATION_ACTIVE] → [MONITORING]
                          ↓
                    [VIOLATION_DETECTED] → [INVESTIGATING] → [RESOLVED | ESCALATED]
```

---

## Workflow Tree

### STEP 1: Company Isolation Setup
**Actor**: Isolation Enforcer
**Action**: When new company is created, establish isolation boundaries
**Timeout**: 30s
**Input**: `{ company_id: uuid, company_name: string, plan: object }`
**Output on SUCCESS**: `{ company_id: uuid, isolation: { data_scope, agent_scope, resource_scope, audit_scope } }` → END
**Output on FAILURE**:
- `FAILURE(setup_error)`: Cannot establish isolation → company creation fails, rollback

**Isolation Setup Process**:
```
1. CREATE company namespace in all data stores
2. CONFIGURE row-level security (RLS) policies
3. CREATE company-scoped agent registry
4. CONFIGURE resource quotas
5. SET UP audit logging channel
6. CONFIGURE event bus topics (company-scoped)
7. VALIDATE isolation boundaries
```

**Isolation Scopes**:
```json
{
  "data_scope": {
    "database": "company_{id}_schema",
    "vector_db": "company_{id}_index",
    "file_storage": "company/{id}/",
    "cache": "company:{id}:*",
    "logs": "company:{id}:*"
  },
  "agent_scope": {
    "registry": "company_{id}_agents",
    "execution": "company_{id}_namespace",
    "memory": "company_{id}_memory",
    "communication": "company_{id}_channel"
  },
  "resource_scope": {
    "token_pool": "company_{id}_tokens",
    "compute": "company_{id}_compute",
    "api_rate_limit": "company_{id}_rate"
  },
  "audit_scope": {
    "log_channel": "audit_{id}",
    "retention_days": 365,
    "alert_on_violation": true
  }
}
```

---

### STEP 2: Data Isolation Enforcement
**Actor**: Data Isolator
**Action**: Ensure all data operations are scoped to the correct company
**Timeout**: Real-time (every data operation)
**Input**: `{ company_id: uuid, operation: enum(read|write|delete), resource: string, query: object }`
**Output on SUCCESS**: `{ allowed: true, scoped_query: object }` → proceed with operation
**Output on FAILURE**:
- `FAILURE(access_violation)`: Attempted cross-company access → BLOCK operation, ALERT operator, LOG violation

**Data Isolation Mechanisms**:
```
DATABASE:
  - Row-Level Security (RLS) on all tables
  - company_id column on every table
  - Queries automatically scoped via RLS policies
  - No raw SQL allowed (ORM only with company scope)

VECTOR_DB:
  - Company-specific collection/index
  - Metadata filter: company_id = current_company
  - No cross-company vector search

FILE_STORAGE:
  - Company-specific bucket/prefix
  - Path: /company/{id}/...
  - No symlink or path traversal

CACHE:
  - Company-prefixed keys: company:{id}:key
  - TTL-based expiration
  - No cross-company cache hits
```

**RLS Policy Example**:
```sql
CREATE POLICY company_isolation ON tasks
  USING (company_id = current_setting('app.current_company_id')::uuid);
```

---

### STEP 3: Agent Isolation Enforcement
**Actor**: Agent Isolator
**Action**: Prevent agents from different companies from communicating or sharing state
**Timeout**: Real-time (every agent operation)
**Input**: `{ agent_id: uuid, target: { type: enum(agent|team|department), id: uuid }, operation: string }`
**Output on SUCCESS**: `{ allowed: true }` → proceed with operation
**Output on FAILURE**:
- `FAILURE(isolation_violation)`: Cross-company agent interaction attempted → BLOCK, ALERT, LOG

**Agent Isolation Rules**:
```
1. AGENT REGISTRY:
   - Each agent belongs to exactly one company
   - Agent lookup scoped to company
   - No cross-company agent queries

2. COMMUNICATION:
   - Messages routed only within company
   - Broadcast scoped to company
   - No cross-company message channels

3. MEMORY:
   - Agent memory scoped to company
   - No cross-company memory queries
   - Vector search scoped to company

4. EXECUTION:
   - Agents execute in company namespace
   - No access to other companies' resources
   - File system scoped to company
```

**Agent Validation Check**:
```
FOR every agent operation:
  VERIFY agent.company_id == request.company_id
  VERIFY target.company_id == request.company_id (if applicable)
  IF mismatch:
    BLOCK operation
    LOG violation
    ALERT security monitor
```

---

### STEP 4: Resource Quota Enforcement
**Actor**: Resource Quota Manager
**Action**: Enforce per-company resource limits
**Timeout**: Real-time (every resource consumption)
**Input**: `{ company_id: uuid, resource_type: enum(tokens|compute|storage|api_calls), amount: number }`
**Output on SUCCESS**: `{ allowed: true, remaining: number }` → proceed with operation
**Output on FAILURE**:
- `FAILURE(quota_exceeded)`: Company at resource limit → BLOCK operation, ALERT operator

**Quota Enforcement Rules**:
```
TOKENS:
  IF company.tokens_remaining < requested:
    IF company.plan.allow_overage:
      ALLOW with overage warning
    ELSE:
      BLOCK with quota_exceeded error

COMPUTE:
  IF company.compute_seconds_remaining < estimated:
    BLOCK with queue (wait for quota reset)

STORAGE:
  IF company.storage_used >= company.storage_limit:
    BLOCK new writes, ALLOW reads
    ALERT operator

API_CALLS:
  IF company.api_calls_this_minute >= rate_limit:
    BLOCK with 429 Too Many Requests
    RETURN retry-after header
```

---

### STEP 5: Marketplace Cross-Company Access
**Actor**: Isolation Enforcer
**Action**: When company installs marketplace template, ensure isolation is maintained
**Timeout**: 30s
**Input**: `{ installer_company_id: uuid, template_id: uuid, publisher_company_id: uuid }`
**Output on SUCCESS**: `{ allowed: true, isolated_installation: true }` → proceed with installation
**Output on FAILURE**:
- `FAILURE(isolation_error)`: Cannot ensure isolation during installation → BLOCK installation

**Marketplace Isolation Process**:
```
1. COPY template to installer's namespace
2. STRIP any publisher-specific configurations
3. VALIDATE no cross-company references in template
4. INSTALL in isolated environment
5. MONITOR for cross-company access attempts
6. LOG installation for audit trail
```

**Template Isolation Rules**:
```
WHEN copying template:
  REMOVE publisher's API keys
  REMOVE publisher's specific endpoints
  RESET all company-specific configurations
  VALIDATE tool configs don't reference external companies
  ENSURE memory is scoped to installer
```

---

### STEP 6: Audit Logging
**Actor**: Audit Logger
**Action**: Record all security-relevant events for compliance and investigation
**Timeout**: Real-time
**Input**: `{ event_type: string, company_id: uuid, actor: object, details: object, severity: enum(info|warning|critical) }`
**Output on SUCCESS**: `{ audit_id: uuid, logged: true }`

**Audit Event Types**:
```
INFO:
  - Company created/deleted
  - Agent created/destroyed
  - Template installed
  - Budget changed
  
WARNING:
  - Unusual access pattern detected
  - High resource consumption
  - Repeated access violations
  
CRITICAL:
  - Cross-company access attempt (blocked)
  - Data isolation violation detected
  - Agent isolation breach
  - Quota override by admin
```

**Audit Log Schema**:
```json
{
  "audit_id": "uuid",
  "timestamp": "ISO8601",
  "event_type": "string",
  "company_id": "uuid",
  "actor": {
    "type": "enum(user|agent|system|admin)",
    "id": "uuid",
    "ip_address": "string",
    "user_agent": "string"
  },
  "details": {
    "resource": "string",
    "operation": "string",
    "result": "enum(allowed|blocked|violation)",
    "reason": "string",
    "additional_data": "object"
  },
  "severity": "enum(info|warning|critical)",
  "retention_days": 365
}
```

---

### STEP 7: Security Monitoring
**Actor**: Security Monitor
**Action**: Detect and respond to isolation violations
**Timeout**: Real-time
**Input**: `{ violation: { type, severity, company_id, details } }`
**Output on SUCCESS**: `{ response: { action_taken, alerts_sent } }`

**Violation Detection Rules**:
```
1. DATA ISOLATION:
   - Query returns data from different company
   - File access outside company scope
   - Cache hit from different company
   → RESPONSE: Block, alert, log, investigate

2. AGENT ISOLATION:
   - Agent communicates with cross-company agent
   - Agent accesses cross-company memory
   - Agent executes in cross-company namespace
   → RESPONSE: Terminate agent, alert, investigate

3. RESOURCE ISOLATION:
   - Company consumes resources beyond quota
   - Shared resource contention
   - Rate limit bypass attempt
   → RESPONSE: Throttle, alert, investigate

4. MARKETPLACE:
   - Template contains cross-company references
   - Installed template accesses publisher data
   - Template exfiltrates installer data
   → RESPONSE: Disable template, alert, investigate
```

**Response Actions by Severity**:
```
INFO:
  LOG event
  NO immediate action
  
WARNING:
  LOG event
  ALERT operator (email)
  INCREASE monitoring frequency
  
CRITICAL:
  LOG event
  ALERT operator (email + Slack + SMS)
  BLOCK violating operation
  TERMINATE affected agents
  PRESERVE evidence for investigation
  ESCALATE to platform security team
```

---

### STEP 8: Compliance Reporting
**Actor**: Audit Logger (background)
**Action**: Generate compliance reports for companies
**Timeout**: 60s (background job)
**Input**: `{ company_id: uuid, period: enum(monthly|quarterly|annual) }`
**Output on SUCCESS**: `{ report_id: uuid, compliance_status: object }`

**Compliance Report Schema**:
```json
{
  "report_id": "uuid",
  "company_id": "uuid",
  "period": {
    "start": "ISO8601",
    "end": "ISO8601"
  },
  "compliance_status": {
    "data_isolation": "enum(pass|fail|warning)",
    "agent_isolation": "enum(pass|fail|warning)",
    "resource_isolation": "enum(pass|fail|warning)",
    "audit_completeness": "enum(pass|fail)",
    "overall": "enum(compliant|non_compliant|needs_review)"
  },
  "violations": [
    {
      "type": "string",
      "severity": "string",
      "count": "number",
      "resolved": "number",
      "details": "string"
    }
  ],
  "recommendations": ["string"],
  "generated_at": "ISO8601"
}
```

---

## State Transitions

```
[COMPANY_CREATED] → [ISOLATION_ACTIVE] → [MONITORING]
[MONITORING] → [VIOLATION_DETECTED] → [INVESTIGATING]
[INVESTIGATING] → [RESOLVED] → [MONITORING]
[INVESTIGATING] → [ESCALATED] → [MONITORING]
[MONITORING] → [ISOLATION_ACTIVE] (continuous)
```

---

## Handoff Contracts

### Any Service → Isolation Enforcer
**Endpoint**: `POST /internal/isolation/check`
**Payload**:
```json
{
  "company_id": "uuid",
  "operation": "enum(read|write|delete|execute|communicate)",
  "resource": {
    "type": "enum(data|agent|memory|compute|storage)",
    "id": "uuid",
    "owner_company_id": "uuid"
  },
  "context": "object"
}
```
**Success response**:
```json
{
  "ok": true,
  "allowed": true,
  "scoped_query": "object — query with company scope applied"
}
```
**Failure response**:
```json
{
  "ok": false,
  "allowed": false,
  "error": "string",
  "code": "ISOLATION_VIOLATION | QUOTA_EXCEEDED",
  "violation_id": "uuid"
}
```
**Timeout**: 5s

### Security Monitor → Operator
**Alert Payload**:
```json
{
  "alert_id": "uuid",
  "level": "critical",
  "title": "Isolation Violation Detected",
  "company_id": "uuid",
  "violation_type": "string",
  "details": "string",
  "affected_resources": ["string"],
  "evidence": "object",
  "suggested_actions": ["string"],
  "runbook_url": "string"
}
```

---

## Cleanup Inventory

| Resource | Created at step | Destroyed by | Destroy method |
|---|---|---|---|
| Company namespace | Step 1 | Company deletion | Cascade delete all company data |
| Audit logs | Step 6 | Retention (1yr) | Archive then delete |
| Violation records | Step 7 | Retention (2yr) | Archive then delete |
| Compliance reports | Step 8 | Retention (7yr) | Archive |

---

## Test Cases

| Test | Trigger | Expected behavior |
|---|---|---|
| TC-01: Company creation | New company signup | Isolation boundaries established |
| TC-02: Data isolation | Cross-company query attempt | Blocked, violation logged |
| TC-03: Agent isolation | Cross-company agent communication | Blocked, agent terminated |
| TC-04: Resource quota | Company exceeds token limit | Operation blocked, operator alerted |
| TC-05: Marketplace install | Template installation | Template isolated in installer namespace |
| TC-06: Audit logging | Security event | Event logged with full context |
| TC-07: Security monitoring | Violation detected | Alert sent, investigation initiated |
| TC-08: Compliance report | Monthly report generated | Report shows compliance status |
| TC-09: Rate limiting | API rate exceeded | 429 returned with retry-after |
| TC-10: File isolation | Cross-company file access | Blocked, violation logged |
| TC-11: Cache isolation | Cross-company cache hit | Miss (no cross-company cache) |
| TC-12: Vector DB isolation | Cross-company similarity search | No results from other companies |

---

## Assumptions

| # | Assumption | Where verified | Risk if wrong |
|---|---|---|---|
| A1 | RLS policies are correctly configured | Not verified | Data leakage between companies |
| A2 | Agent namespace isolation is enforced at runtime | Not verified | Cross-company agent interaction |
| A3 | Audit logs are tamper-proof | Not verified | Violations can be hidden |
| A4 | Security monitoring has sufficient coverage | Not verified | Violations go undetected |
| A5 | Compliance reports are accurate | Not verified | False sense of security |

---

## Open Questions

- Should there be a "shared" namespace for cross-company collaboration?
- How do we handle companies that merge or split?
- Should there be an "isolation level" setting (strict vs flexible)?
- How do we handle regulatory requirements (GDPR, HIPAA) per company?
