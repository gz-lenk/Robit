---
name: team-handoff-protocol
description: Use by any FPGA teammate when sending status, blockers, plans, or finished work to the lead or another teammate.
---

# Team Handoff Protocol

Use this shared skill for concise messages between FPGA teammates and the lead.

## Message Types

Use one of these labels at the start of handoff messages:

- `PLAN`: proposed next steps before doing risky or broad work.
- `DONE`: completed work ready for the next teammate.
- `BLOCKED`: cannot proceed without input or a prior artifact.
- `ASSUMPTION`: continuing with a stated assumption.
- `REVIEW`: asking another teammate or lead to inspect an artifact.

## Handoff Template

```text
DONE: <short result>
Artifacts:
- <path>: <purpose>
Assumptions:
- <assumption or none>
Checks:
- <command/result or not run>
Next:
- <recommended next teammate/action>
```

## Blocker Template

```text
BLOCKED: <short blocker>
Need:
- <specific missing information or artifact>
Impact:
- <why this blocks the current stage>
Can proceed if:
- <safe assumption, if one exists>
```

## Quality Bar

- Name exact files.
- Name exact commands when checks ran.
- Keep messages short enough for the lead to route.
- Do not bury open questions in a long summary.
