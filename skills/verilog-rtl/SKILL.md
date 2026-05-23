---
name: verilog-rtl
description: Use when implementing synthesizable Verilog/SystemVerilog RTL from FPGA requirements and architecture documents.
---

# Verilog RTL

Use this skill when acting as the implementer. Read `docs/requirements.md` and `docs/design.md` before writing RTL. If either document is missing required interface or behavior details, ask the lead to route back to advisor or architect.

## RTL Workflow

1. Identify the top module and submodules to create.
2. Confirm ports, widths, reset behavior, and handshake protocol from the design doc.
3. Implement one module at a time under `rtl/`, `src/`, `hdl/`, `verilog/`, or `ip/`.
4. Keep sequential and combinational logic clearly separated.
5. Add comments only for protocol, non-obvious arithmetic, and state machine intent.
6. Run available syntax/simulation checks when local tools exist.
7. Report created files, assumptions, and unverified behavior.

## Synthesizable RTL Rules

- Use `always_ff`/`always_comb` for SystemVerilog when the project supports it; otherwise use clear Verilog `always` blocks.
- Reset every state register with the documented reset polarity and sync/async behavior.
- Avoid latches: assign defaults in combinational blocks.
- Avoid testbench-only constructs in RTL: `#delay`, `initial` for functional behavior, `$display`, file I/O, randomization.
- Keep handshake semantics precise: data transfers only when both valid and ready are asserted.
- Use explicit widths for constants and arithmetic.
- Handle overflow, rounding, and saturation exactly as requirements state.
- Do not silently invent top-level ports or protocol behavior.

## File Organization

Prefer this structure unless the repository already has a convention:

```text
rtl/
  <top>.sv
  <submodule>.sv
docs/
  requirements.md
  design.md
tests/
  ...
```

## Implementation Handoff

When done, tell the lead:

- RTL files created or edited.
- Top module name.
- Important parameters.
- Assumptions made.
- Checks run and results.
- What tester should verify first.

## Review Checklist

- Ports match `docs/design.md`.
- Reset behavior matches requirements.
- No combinational feedback or unintended latch.
- All state transitions are defined.
- Backpressure behavior is explicit.
- Width growth and truncation are intentional.
- Code can be exercised by cocotb without hidden dependencies.
