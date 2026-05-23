---
name: fpga-project-flow
description: Use by any FPGA teammate to understand the end-to-end workflow from requirements to architecture, RTL, cocotb verification, and handoff.
---

# FPGA Project Flow

Use this shared skill to keep the FPGA team moving in the right order.

## Stage Order

1. Advisor clarifies requirements and writes `docs/requirements.md`.
2. Architect reads requirements and writes `docs/design.md`.
3. Implementer reads requirements and design, then writes RTL.
4. Tester reads requirements, design, and RTL, then writes and runs cocotb tests.
5. Lead summarizes status, open questions, and next actions for the user.

## Handoff Rules

- Do not skip a previous stage if it contains blocking ambiguity.
- Do not silently invent missing widths, protocols, clocking, or arithmetic behavior.
- Prefer explicit assumptions over hidden guesses.
- Keep documents and generated files in the teammate's allowed writable roots.
- Send concise progress updates to lead when a stage is done or blocked.

## Common Artifacts

- `docs/requirements.md`: user-facing functional and integration requirements.
- `docs/design.md`: architecture, module boundaries, timing, and implementation guidance.
- `rtl/` or local convention: synthesizable RTL.
- `tests/` or local convention: cocotb testbench and simulation files.

## Blocked State

When blocked, send the lead:

- Blocking issue.
- Why it affects this stage.
- Specific question or artifact needed.
- Whether work can proceed with an explicit assumption.
