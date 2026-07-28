# WORKFLOW-08: Marketplace Workflows

**Version**: 0.1
**Date**: 2026-07-28
**Author**: Workflow Architect
**Status**: Draft
**Implements**: Autonomous AI Workforce Platform — Agent Template Publishing, Installation, Reviews, Versioning, Revenue Sharing

---

## Overview

The Marketplace enables companies to publish agent templates, discover and install templates from other companies, rate and review templates, manage versions, and handle revenue sharing. The marketplace is the economic engine of the platform ecosystem.

---

## Actors

| Actor | Role in this workflow |
|---|---|
| Publisher | Company publishing a template |
| Consumer | Company installing a template |
| Template Validator | Validates template quality and safety |
| Review System | Manages ratings and reviews |
| Version Manager | Handles template versioning |
| Revenue Engine | Manages payments and revenue sharing |
| Moderation System | Ensures template quality and compliance |
| Event Bus | Publishes marketplace events |

---

## Prerequisites

- Publisher company has approved templates
- Consumer company has active subscription
- Payment system is configured
- Moderation policies are defined

---

## Trigger

Marketplace actions are triggered by:
1. Publisher submits template for listing
2. Consumer searches for or installs template
3. Consumer leaves review
4. Publisher updates template version
5. Revenue threshold reached

---

## State Diagram

```
Template: [DRAFT] → [SUBMITTED] → [REVIEWING] → [APPROVED] → [LISTED]
                                    ↓                    ↓
                              [REJECTED]          [DELISTED]
                                                      ↓
                                                  [ARCHIVED]

Installation: [DISCOVERED] → [INSTALLING] → [INSTALLED] → [CONFIGURED]
                              ↓                  ↓
                        [INSTALL_FAILED]   [UPDATE_AVAILABLE]

Review: [SUBMITTED] → [PUBLISHED] → [VISIBLE]
                     ↓
               [REJECTED]
```

---

## Workflow Tree

### STEP 1: Template Submission
**Actor**: Publisher
**Action**: Publisher submits agent template for marketplace listing
**Timeout**: 30s
**Input**: `{ company_id: uuid, template: object, pricing: object }`
**Output on SUCCESS**: `{ template_id: uuid, status: "submitted", submission_id: uuid }` → GO TO STEP 2
**Output on FAILURE**:
- `FAILURE(validation_error)`: Template missing required fields → return 400 with specific issues
- `FAILURE(quota_exceeded)`: Publisher at max templates → return 429
- `FAILURE(duplicate)`: Template with same name/version exists → return 409

**Template Submission Schema**:
```json
{
  "template": {
    "name": "string — unique within publisher",
    "description": "string — what this agent does",
    "version": "string — semver format",
    "role": "string — e.g., 'research_analyst', 'content_writer'",
    "capabilities": ["string"],
    "base_model": "string",
    "system_prompt_template": "string",
    "tools": [{"name": "string", "config": "object", "required": "boolean"}],
    "parameters": {
      "temperature": "number",
      "max_tokens": "number",
      "timeout_seconds": "number"
    },
    "resource_profile": {
      "min_tokens_per_task": "number",
      "avg_tokens_per_task": "number"
    },
    "requirements": {
      "min_platform_version": "string",
      "required_integrations": ["string"],
      "required_tools": ["string"]
    },
    "tags": ["string"],
    "category": "string",
    "icon_url": "string",
    "screenshots": ["string — URLs"],
    "documentation_url": "string"
  },
  "pricing": {
    "model": "enum(free | per_install | per_task | subscription)",
    "price_usd": "number",
    "free_tier": {
      "included_tasks": "number",
      "included_tokens": "number"
    }
  }
}
```

---

### STEP 2: Template Validation
**Actor**: Template Validator
**Action**: Validate template quality, safety, and compliance
**Timeout**: 60s
**Input**: `{ template_id: uuid, template: object }`
**Output on SUCCESS**: `{ template_id: uuid, validation: { passed: true, warnings: [] } }` → GO TO STEP 3
**Output on FAILURE**:
- `FAILURE(security_issue)`: Template contains security risk → reject with details
- `FAILURE(quality_issue)`: Template doesn't meet quality standards → reject with suggestions
- `FAILURE(compliance_issue)`: Template violates policies → reject with policy references

**Validation Checks**:
```
1. SECURITY:
   - No hardcoded credentials
   - No malicious prompt injection patterns
   - Tool configs don't expose sensitive endpoints
   - No data exfiltration patterns
   
2. QUALITY:
   - System prompt is well-structured
   - Tools are properly configured
   - Parameters are within acceptable ranges
   - Documentation is complete
   
3. COMPLIANCE:
   - Doesn't violate platform policies
   - No prohibited content
   - Meets accessibility requirements
   - Proper attribution for borrowed components
```

---

### STEP 3: Moderation Review
**Actor**: Moderation System
**Action**: Human or AI review of template before listing
**Timeout**: 24h (human review SLA)
**Input**: `{ template_id: uuid, validation_results: object }`
**Output on SUCCESS**: `{ template_id: uuid, status: "approved", moderator_notes: string }` → GO TO STEP 4
**Output on FAILURE**:
- `FAILURE(rejected)`: Template doesn't meet standards → return to publisher with feedback
- `FAILURE(review_timeout)`: No reviewer available → escalate to senior moderator

---

### STEP 4: Template Listing
**Actor**: Marketplace System
**Action**: List approved template in marketplace catalog
**Timeout**: 15s
**Input**: `{ template_id: uuid, pricing: object }`
**Output on SUCCESS**: `{ template_id: uuid, status: "listed", listed_at: timestamp, marketplace_url: string }` → END
**Output on FAILURE**:
- `FAILURE(listing_error)`: Cannot create listing → retry x3 with 5s backoff

**Observable states**:
- Publisher sees: Template listed, visible in marketplace
- Consumer sees: Template appears in search results
- Database: `templates.status = 'listed'`, `templates.listed_at = now()`
- Logs: `[marketplace] template_id=abc listed, publisher=company_xyz`

**Listing Schema**:
```json
{
  "template_id": "uuid",
  "publisher": {
    "company_id": "uuid",
    "company_name": "string",
    "rating": "number",
    "templates_published": "number"
  },
  "template": {
    "name": "string",
    "description": "string",
    "version": "string",
    "role": "string",
    "capabilities": ["string"],
    "tags": ["string"],
    "category": "string",
    "icon_url": "string",
    "screenshots": ["string"]
  },
  "pricing": {
    "model": "string",
    "price_usd": "number"
  },
  "stats": {
    "installs": 0,
    "rating": 0,
    "review_count": 0
  },
  "listed_at": "ISO8601"
}
```

---

### STEP 5: Template Discovery & Installation
**Actor**: Consumer
**Action**: Consumer finds and installs template
**Timeout**: 30s
**Input**: `{ consumer_company_id: uuid, template_id: uuid, configuration: object }`
**Output on SUCCESS**: `{ installation_id: uuid, status: "installed", agent_template_id: uuid }` → GO TO STEP 6
**Output on FAILURE**:
- `FAILURE(payment_required)`: Template requires payment → initiate payment flow
- `FAILURE(incompatible)`: Template incompatible with platform version → return error with upgrade path
- `FAILURE(quota_exceeded)`: Consumer at max templates → return 429
- `FAILURE(install_error)`: Installation fails → retry x2 with 5s backoff

**Installation Process**:
```
1. CHECK consumer has access (subscription, quota)
2. CHECK payment (if paid template)
3. COPY template to consumer's namespace
4. CUSTOMIZE template with consumer's configuration
5. VALIDATE installation
6. REGISTER in consumer's agent registry
7. PUBLISH TemplateInstalled event
```

**Installation Schema**:
```json
{
  "installation_id": "uuid",
  "consumer_company_id": "uuid",
  "template_id": "uuid",
  "template_version": "string",
  "configuration": {
    "custom_prompt_additions": "string",
    "tool_overrides": "object",
    "parameter_overrides": "object",
    "integration_config": "object"
  },
  "installed_at": "ISO8601",
  "status": "enum(installed|configuring|active|error)"
}
```

---

### STEP 6: Template Configuration
**Actor**: Consumer
**Action**: Consumer configures installed template for their specific needs
**Timeout**: None (manual)
**Input**: `{ installation_id: uuid, configuration: object }`
**Output on SUCCESS**: `{ installation_id: uuid, status: "configured", ready_for_use: true }` → END
**Output on FAILURE**:
- `FAILURE(config_error)`: Configuration invalid → return validation errors

---

### STEP 7: Review Submission
**Actor**: Consumer
**Action**: Consumer rates and reviews installed template
**Timeout**: 15s
**Input**: `{ installation_id: uuid, rating: number 1-5, review: string }`
**Output on SUCCESS**: `{ review_id: uuid, status: "published" }` → GO TO STEP 8
**Output on FAILURE**:
- `FAILURE(review_error)`: Cannot submit review → retry x2
- `FAILURE(already_reviewed)`: Consumer already reviewed this template → update existing review

**Review Schema**:
```json
{
  "review_id": "uuid",
  "template_id": "uuid",
  "installation_id": "uuid",
  "reviewer_company_id": "uuid",
  "rating": "number 1-5",
  "review": "string — max 1000 chars",
  "pros": ["string"],
  "cons": ["string"],
  "use_case": "string — how they use this template",
  "created_at": "ISO8601"
}
```

---

### STEP 8: Rating Aggregation
**Actor**: Review System
**Action**: After new review, recalculate template rating
**Timeout**: 10s
**Input**: `{ template_id: uuid, new_review: object }`
**Output on SUCCESS**: `{ template_id: uuid, new_rating: number, review_count: number }` → END

**Rating Calculation**:
```
weighted_rating = (existing_avg * existing_count + new_rating) / (existing_count + 1)

IF review_count >= 10:
  SHOW "verified" badge
IF review_count >= 50:
  SHOW "popular" badge
IF weighted_rating >= 4.5 AND review_count >= 20:
  SHOW "top_rated" badge
```

---

### STEP 9: Version Update
**Actor**: Publisher
**Action**: Publisher releases new version of template
**Timeout**: Same as STEP 1-4 (re-validation)
**Input**: `{ template_id: uuid, new_version: string, changelog: string, template: object }`
**Output on SUCCESS**: `{ template_id: uuid, version: string, status: "listed" }` → END
**Output on FAILURE**:
- `FAILURE(version_exists)`: Version already exists → return 409
- `FAILURE(validation_failed)`: New version fails validation → return error

**Version Update Process**:
```
1. VALIDATE new version > current version (semver)
2. RUN validation (same as STEP 2)
3. RUN moderation (same as STEP 3)
4. UPDATE listing with new version
5. NOTIFY existing installers of update available
6. PUBLISH TemplateUpdated event
```

---

### STEP 10: Revenue Sharing
**Actor**: Revenue Engine
**Action**: When revenue threshold reached, process payment to publisher
**Timeout**: 24h (payment processing)
**Input**: `{ publisher_company_id: uuid, period: { start: ISO8601, end: ISO8601 } }`
**Output on SUCCESS**: `{ payment_id: uuid, amount_usd: number, platform_fee: number, publisher_payout: number }` → END
**Output on FAILURE**:
- `FAILURE(payment_error)`: Payment processing fails → retry x3 with 24h backoff
- `FAILURE(insufficient)`: Amount below minimum payout → accumulate until threshold

**Revenue Share Model**:
```
platform_fee = revenue * 0.20 (20%)
publisher_payout = revenue * 0.80 (80%)

minimum_payout = $50
payment_frequency = monthly
payment_method = bank_transfer | platform_credit
```

**Revenue Schema**:
```json
{
  "payment_id": "uuid",
  "publisher_company_id": "uuid",
  "period": {
    "start": "ISO8601",
    "end": "ISO8601"
  },
  "revenue": {
    "total_installs": "number",
    "paid_installs": "number",
    "total_revenue_usd": "number",
    "breakdown": [
      {
        "installation_id": "uuid",
        "amount_usd": "number",
        "date": "ISO8601"
      }
    ]
  },
  "fees": {
    "platform_fee_usd": "number",
    "payment_processing_fee_usd": "number"
  },
  "payout": {
    "amount_usd": "number",
    "method": "string",
    "status": "enum(pending|processing|completed|failed)"
  }
}
```

---

### STEP 11: Template Delisting
**Actor**: Moderation System or Publisher
**Action**: Remove template from marketplace (either by publisher request or moderation action)
**Timeout**: 15s
**Input**: `{ template_id: uuid, reason: string, initiated_by: enum(publisher|moderation) }`
**Output on SUCCESS**: `{ template_id: uuid, status: "delisted", delisted_at: timestamp }` → END
**Output on FAILURE**:
- `FAILURE(delist_error)`: Cannot delist → retry x3

**Delisting Rules**:
```
IF initiated_by == 'publisher':
  IMMEDIATE delisting
  EXISTING installations continue to work
  NO new installations allowed
  
IF initiated_by == 'moderation':
  WARNING to publisher (24h to fix)
  IF not fixed: IMMEDIATE delisting
  EXISTING installations: grace period (30d) then disabled
```

---

## State Transitions

```
Template:
[DRAFT] → [SUBMITTED] → [REVIEWING] → [APPROVED] → [LISTED]
[REVIEWING] → [REJECTED] (terminal, can resubmit)
[LISTED] → [DELISTED] → [ARCHIVED]

Installation:
[DISCOVERED] → [INSTALLING] → [INSTALLED] → [CONFIGURED]
[INSTALLING] → [INSTALL_FAILED] (terminal)
[INSTALLED] → [UPDATE_AVAILABLE] → [INSTALLING] (re-install)

Review:
[SUBMITTED] → [PUBLISHED]
[SUBMITTED] → [REJECTED]
```

---

## Cleanup Inventory

| Resource | Created at step | Destroyed by | Destroy method |
|---|---|---|---|
| Template records | Step 1 | Delisting | Archive |
| Installation records | Step 5 | Consumer uninstall | `DELETE FROM installations WHERE id = ?` |
| Reviews | Step 7 | Retention (3yr) | Archive after 3 years |
| Revenue records | Step 10 | Retention (7yr) | Archive after 7 years |

---

## Test Cases

| Test | Trigger | Expected behavior |
|---|---|---|
| TC-01: Template submission | Publisher submits | Template enters review pipeline |
| TC-02: Validation pass | Valid template | Template approved for moderation |
| TC-03: Validation fail | Security issue | Template rejected with details |
| TC-04: Moderation approve | Quality template | Template listed in marketplace |
| TC-05: Template install | Consumer installs | Template copied to consumer namespace |
| TC-06: Paid install | Consumer installs paid template | Payment processed, template installed |
| TC-07: Review submit | Consumer reviews | Rating updated, review published |
| TC-08: Version update | Publisher releases v2.0 | New version listed, installers notified |
| TC-09: Revenue payout | Monthly threshold reached | Payment processed to publisher |
| TC-10: Delisting (publisher) | Publisher removes template | Template delisted immediately |
| TC-11: Delisting (moderation) | Policy violation | Warning → 24h fix window → delist |
| TC-12: Concurrent installs | Multiple consumers install | Each installation isolated |

---

## Assumptions

| # | Assumption | Where verified | Risk if wrong |
|---|---|---|---|
| A1 | Template validation catches security issues | Not verified | Malicious templates listed |
| A2 | Revenue sharing model is acceptable to publishers | Not verified | Low publisher participation |
| A3 | Version semver is enforced | Not verified | Breaking changes pushed as patches |
| A4 | Moderation SLA (24h) is achievable | Not verified | Templates stuck in review |
| A5 | Installation isolation prevents cross-company data leaks | Not verified | Data breach between companies |

---

## Open Questions

- Should there be a "trial" period for paid templates?
- How do we handle template dependencies (template A requires template B)?
- Should there be a "certified" badge for platform-vetted templates?
- How do we handle disputes between publishers and consumers?
