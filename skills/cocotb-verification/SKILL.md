---
name: cocotb-verification
description: Use when creating cocotb testbenches, drivers, monitors, scoreboards, and simulation commands for FPGA RTL verification.
---

# Cocotb Verification

Use this skill when acting as the tester. Read requirements, design, and RTL before writing tests. Verification should focus on externally visible behavior and reusable testbench structure.

## Verification Workflow

1. Read `docs/requirements.md`, `docs/design.md`, and the RTL files.
2. Identify the DUT top module, clock/reset, ports, and protocol.
3. Create cocotb tests under `tests/`, `test/`, `sim/`, `verif/`, or `tb/`.
4. Build drivers and monitors for handshakes instead of poking every signal ad hoc.
5. Use a scoreboard or golden model for expected behavior.
6. Run simulation when tools are installed.
7. Report exact commands, pass/fail status, failures, and coverage gaps.

## Testbench Structure

Prefer this layout when no project convention exists:

```text
tests/
  test_<dut>.py
  Makefile
```

For cocotb tests:

- Generate clock and reset consistently.
- Encapsulate input transactions in helper functions or driver classes.
- Monitor outputs and compare against expected transactions.
- Include timeout protection so failed handshakes do not hang forever.
- Keep random tests reproducible by seeding the RNG.

## Minimum Test Set

- Reset behavior.
- One simple directed valid transaction.
- Back-to-back transactions.
- Stalls or backpressure if protocol supports it.
- Boundary values: zero, max, min, signed negative, overflow or saturation cases.
- Invalid or idle cycles if relevant.
- Randomized regression when a compact golden model exists.

## Cocotb Makefile Pattern

```makefile
TOPLEVEL_LANG ?= verilog
SIM ?= icarus

VERILOG_SOURCES += $(PWD)/../rtl/<dut>.sv
TOPLEVEL = <dut>
MODULE = test_<dut>

include $(shell cocotb-config --makefiles)/Makefile.sim
```

Adjust paths and simulator for the repository.

## Result Report

Send the lead:

- Test files created or edited.
- Simulator command used.
- Passing tests.
- Failing tests with the first useful error.
- Missing toolchain items, if simulation could not run.
- Coverage gaps and recommended next tests.
