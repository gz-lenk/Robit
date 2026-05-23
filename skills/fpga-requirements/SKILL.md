---
name: fpga-requirements
description: Use when clarifying FPGA project requirements, interviewing the user for missing hardware details, or producing docs/requirements.md before architecture, RTL, or verification work.
---

# FPGA Requirements

Use this skill when acting as the advisor for an FPGA development task. Your job is to turn an ambiguous user request into a requirements document that the architect, RTL implementer, and tester can execute without guessing.

## Advisor Workflow

1. Identify the requested hardware function in one sentence.
2. Read existing project files if useful, especially README, docs, RTL, tests, constraints, and prior requirements.
3. Classify missing information as blocking or non-blocking.
4. Ask the user only the blocking questions needed to proceed.
5. When enough detail exists, write or update `docs/requirements.md`.
6. Send the lead a concise summary with remaining assumptions and handoff notes.

## Blocking Questions

Ask about these when they affect the architecture, RTL interface, or verification plan:

- Target function: exact transform, protocol behavior, register behavior, or datapath operation.
- Top-level interface: signal names, widths, direction, handshake, streaming or memory-mapped protocol.
- Clocking and reset: clock count, reset polarity, sync/async reset, clock-domain crossings.
- Data format: integer/fixed-point/float, signedness, endian/order, rounding, saturation, overflow.
- Throughput and latency: samples per cycle, initiation interval, max latency, burst behavior.
- Capacity: FIFO depths, memory sizes, address ranges, packet/frame sizes.
- Target platform: FPGA family, synthesis tool, clock target, available IP, resource constraints.
- Integration constraints: bus standard, register map, interrupts, DMA, host software assumptions.
- Verification criteria: golden model, directed cases, randomized cases, error handling, coverage goals.

Do not ask every question by default. Ask the smallest set that removes real ambiguity.

## Requirements Document Template

Use this structure for `docs/requirements.md`:

```markdown
# Requirements

## Summary
- Requested function:
- Intended integration context:

## Functional Requirements
- REQ-FUNC-001:

## Interface Requirements
| Signal/Interface | Direction | Width | Description |
| --- | --- | --- | --- |

## Timing And Clocking
- Clock:
- Reset:
- Throughput:
- Latency:

## Data Format
- Type:
- Width:
- Signedness:
- Rounding/overflow behavior:

## Resource And Platform Constraints
- Target FPGA/tool:
- Frequency target:
- Resource limits:

## Verification Requirements
- Required test scenarios:
- Golden reference:
- Pass/fail criteria:

## Assumptions
- ASSUMP-001:

## Open Questions
- Q-001:
```

## Quality Bar

A good requirements document is specific enough that:

- The architect can choose module boundaries and performance strategy.
- The implementer can write top-level ports without inventing names or widths.
- The tester can build cocotb drivers, monitors, and scoreboards.
- Any remaining unknowns are explicitly listed as assumptions or open questions.

If user input is too vague, do not generate RTL-facing requirements prematurely. Ask concise clarifying questions through the lead.
