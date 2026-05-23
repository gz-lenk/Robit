---
name: fpga-architecture
description: Use when turning FPGA requirements into a hardware architecture, module breakdown, interface plan, timing assumptions, and docs/design.md before RTL implementation.
---

# FPGA Architecture

Use this skill when acting as the architect for an FPGA development task. Your output should let the implementer write RTL without guessing and let the tester derive a verification plan.

## Architecture Workflow

1. Read `docs/requirements.md` first. If it is missing or ambiguous, ask the lead to route back to advisor.
2. Identify the top-level function, data movement, control flow, and performance constraints.
3. Decide whether the design is control-dominated, datapath-dominated, memory-bandwidth-limited, or interface-limited.
4. Define module boundaries and each module's responsibility.
5. Define all module interfaces, including valid/ready, enable, start/done, register, or memory protocols.
6. Choose pipeline, buffering, FSM, and backpressure strategy.
7. Write or update `docs/design.md`.

## Design Decisions To Make Explicit

- Clock and reset strategy.
- Top-level ports and submodule interfaces.
- Data width, signedness, fixed-point format, packing, and ordering.
- Latency and initiation interval targets.
- FIFO, RAM, ROM, or line-buffer requirements.
- FSM states and legal transitions.
- Error, overflow, stall, and reset behavior.
- Resource-sensitive blocks: DSPs, BRAMs, LUT RAM, distributed RAM, vendor IP.
- Assumptions handed to RTL and verification.

## Design Document Template

Use this structure for `docs/design.md`:

```markdown
# Design

## Inputs
- Requirements document:
- Open assumptions:

## Architecture Summary
- Selected architecture:
- Rationale:

## Module Breakdown
| Module | Responsibility | Key Interfaces |
| --- | --- | --- |

## Top-Level Interface
| Signal/Interface | Direction | Width | Timing/Protocol |
| --- | --- | --- | --- |

## Datapath
- Data format:
- Pipeline stages:
- Arithmetic behavior:

## Control
- FSM states:
- Start/stop behavior:
- Backpressure/stall behavior:

## Memory And Buffering
- Storage elements:
- Depth/width:
- Access pattern:

## Timing And Performance
- Clock assumptions:
- Latency:
- Throughput:
- Critical path risks:

## Verification Notes
- Required scenarios:
- Corner cases:
- Observable properties:

## Handoff To Implementer
- Files/modules to create:
- Assumptions:
```

## Quality Bar

A good architecture document names enough signals, modules, states, and timing behavior that RTL implementation is mostly mechanical. Do not hide uncertainty in prose; list open questions or assumptions explicitly.
