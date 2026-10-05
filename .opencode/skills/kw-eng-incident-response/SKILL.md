---
name: kw-eng-incident-response
description: Run an incident response workflow â€” triage, communicate, and write postmortem. Trigger with "we have an incident", "production is down", an alert that needs severity assessment, a status update mid-incident, or when writing a blameless postmortem after resolution.
argument-hint: "<incident description or alert>"
---

# /incident-response

> If you see unfamiliar placeholders or need to check which tools are connected, see [CONNECTORS.md](../../CONNECTORS.md).

Manage an incident from detection through postmortem.

## Usage

```
/incident-response $ARGUMENTS
```

## Modes

```
/incident-response new [description]     # Start a new incident
/incident-response update [status]       # Post a status update
/incident-response postmortem            # Generate postmortem from incident data
```

If no mode is specified, ask what phase the incident is in.

## How It Works

```
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚                    INCIDENT RESPONSE                               â”‚
â”œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¤
â”‚  Phase 1: TRIAGE                                                  â”‚
â”‚  âœ“ Assess severity (SEV1-4)                                     â”‚
â”‚  âœ“ Identify affected systems and users                          â”‚
â”‚  âœ“ Assign roles (IC, comms, responders)                         â”‚
â”‚                                                                    â”‚
â”‚  Phase 2: COMMUNICATE                                              â”‚
â”‚  âœ“ Draft internal status update                                  â”‚
â”‚  âœ“ Draft customer communication (if needed)                     â”‚
â”‚  âœ“ Set up war room and cadence                                   â”‚
â”‚                                                                    â”‚
â”‚  Phase 3: MITIGATE                                                 â”‚
â”‚  âœ“ Document mitigation steps taken                               â”‚
â”‚  âœ“ Track timeline of events                                      â”‚
â”‚  âœ“ Confirm resolution                                            â”‚
â”‚                                                                    â”‚
â”‚  Phase 4: POSTMORTEM                                               â”‚
â”‚  âœ“ Blameless postmortem document                                 â”‚
â”‚  âœ“ Timeline reconstruction                                       â”‚
â”‚  âœ“ Root cause analysis (5 whys)                                  â”‚
â”‚  âœ“ Action items with owners                                      â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
```

## Severity Classification

| Level | Criteria | Response Time |
|-------|----------|---------------|
| SEV1 | Service down, all users affected | Immediate, all-hands |
| SEV2 | Major feature degraded, many users affected | Within 15 min |
| SEV3 | Minor feature issue, some users affected | Within 1 hour |
| SEV4 | Cosmetic or low-impact issue | Next business day |

## Communication Guidance

Provide clear, factual updates at regular cadence. Include: what's happening, who's affected, what we're doing, when the next update is.

## Output â€” Status Update

```markdown
## Incident Update: [Title]
**Severity:** SEV[1-4] | **Status:** Investigating | Identified | Monitoring | Resolved
**Impact:** [Who/what is affected]
**Last Updated:** [Timestamp]

### Current Status
[What we know now]

### Actions Taken
- [Action 1]
- [Action 2]

### Next Steps
- [What's happening next and ETA]

### Timeline
| Time | Event |
|------|-------|
| [HH:MM] | [Event] |
```

## Output â€” Postmortem

```markdown
## Postmortem: [Incident Title]
**Date:** [Date] | **Duration:** [X hours] | **Severity:** SEV[X]
**Authors:** [Names] | **Status:** Draft

### Summary
[2-3 sentence plain-language summary]

### Impact
- [Users affected]
- [Duration of impact]
- [Business impact if quantifiable]

### Timeline
| Time (UTC) | Event |
|------------|-------|
| [HH:MM] | [Event] |

### Root Cause
[Detailed explanation of what caused the incident]

### 5 Whys
1. Why did [symptom]? â†’ [Because...]
2. Why did [cause 1]? â†’ [Because...]
3. Why did [cause 2]? â†’ [Because...]
4. Why did [cause 3]? â†’ [Because...]
5. Why did [cause 4]? â†’ [Root cause]

### What Went Well
- [Things that worked]

### What Went Poorly
- [Things that didn't work]

### Action Items
| Action | Owner | Priority | Due Date |
|--------|-------|----------|----------|
| [Action] | [Person] | P0/P1/P2 | [Date] |

### Lessons Learned
[Key takeaways for the team]
```

## If Connectors Available

If **~~monitoring** is connected:
- Pull alert details and metrics
- Show graphs of affected metrics

If **~~incident management** is connected:
- Create or update incident in PagerDuty/Opsgenie
- Page on-call responders

If **~~chat** is connected:
- Post status updates to incident channel
- Create war room channel

## Tips

1. **Start writing immediately** â€” Don't wait for complete information. Update as you learn more.
2. **Keep updates factual** â€” What we know, what we've done, what's next. No speculation.
3. **Postmortems are blameless** â€” Focus on systems and processes, not individuals.
