---
name: kw-eng-debug
description: Structured debugging session â€” reproduce, isolate, diagnose, and fix. Trigger with an error message or stack trace, "this works in staging but not prod", "something broke after the deploy", or when behavior diverges from expected and the cause isn't obvious.
argument-hint: "<error message or problem description>"
---

# /debug

> If you see unfamiliar placeholders or need to check which tools are connected, see [CONNECTORS.md](../../CONNECTORS.md).

Run a structured debugging session to find and fix issues systematically.

## Usage

```
/debug $ARGUMENTS
```

## How It Works

```
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚                       DEBUG                                        â”‚
â”œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¤
â”‚  Step 1: REPRODUCE                                                â”‚
â”‚  âœ“ Understand the expected vs. actual behavior                   â”‚
â”‚  âœ“ Identify exact reproduction steps                             â”‚
â”‚  âœ“ Determine scope (when did it start? who is affected?)        â”‚
â”‚                                                                    â”‚
â”‚  Step 2: ISOLATE                                                   â”‚
â”‚  âœ“ Narrow down the component, service, or code path             â”‚
â”‚  âœ“ Check recent changes (deploys, config changes, dependencies) â”‚
â”‚  âœ“ Review logs and error messages                                â”‚
â”‚                                                                    â”‚
â”‚  Step 3: DIAGNOSE                                                  â”‚
â”‚  âœ“ Form hypotheses and test them                                 â”‚
â”‚  âœ“ Trace the code path                                           â”‚
â”‚  âœ“ Identify root cause (not just symptoms)                      â”‚
â”‚                                                                    â”‚
â”‚  Step 4: FIX                                                       â”‚
â”‚  âœ“ Propose a fix with explanation                                â”‚
â”‚  âœ“ Consider side effects and edge cases                          â”‚
â”‚  âœ“ Suggest tests to prevent regression                           â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
```

## What I Need From You

Tell me about the problem. Any of these help:
- Error message or stack trace
- Steps to reproduce
- What changed recently
- Logs or screenshots
- Expected vs. actual behavior

## Output

```markdown
## Debug Report: [Issue Summary]

### Reproduction
- **Expected**: [What should happen]
- **Actual**: [What happens instead]
- **Steps**: [How to reproduce]

### Root Cause
[Explanation of why the bug occurs]

### Fix
[Code changes or configuration fixes needed]

### Prevention
- [Test to add]
- [Guard to put in place]
```

## If Connectors Available

If **~~monitoring** is connected:
- Pull logs, error rates, and metrics around the time of the issue
- Show recent deploys and config changes that may correlate

If **~~source control** is connected:
- Identify recent commits and PRs that touched affected code paths
- Check if the issue correlates with a specific change

If **~~project tracker** is connected:
- Search for related bug reports or known issues
- Create a ticket for the fix once identified

## Tips

1. **Share error messages exactly** â€” Don't paraphrase. The exact text matters.
2. **Mention what changed** â€” Recent deploys, dependency updates, and config changes are top suspects.
3. **Include context** â€” "This works in staging but not prod" or "Only affects large payloads" narrows things fast.
