---
name: roofline-model
description: Use when estimating FPGA architecture performance limits from compute throughput, memory bandwidth, operational intensity, and resource constraints.
---

# Roofline Model

Use this skill when architecture choices depend on whether the FPGA design is compute-limited, memory-bandwidth-limited, or interface-limited.

## Inputs To Collect

- Operation count per output item or transaction.
- Bytes read and written per output item or transaction.
- Target clock frequency.
- Expected parallel lanes or processing elements.
- Memory/interface bandwidth: AXI, DDR, HBM, stream width, cycles per beat.
- Available resources: DSPs, BRAM/URAM, LUTs, routing, vendor IP limits.
- Required throughput and latency.

## Core Calculation

Use consistent units.

```text
operational_intensity = operations / byte
peak_compute = operations_per_cycle * clock_hz
peak_bandwidth = bytes_per_cycle * clock_hz
bandwidth_limited_perf = operational_intensity * peak_bandwidth
expected_perf = min(peak_compute, bandwidth_limited_perf)
```

Then compare `expected_perf` with the required performance.

## FPGA-Specific Checks

- DSP-bound: multipliers, MACs, floating-point operators, fixed-point width growth.
- Memory-bound: DDR/HBM bursts, alignment, bank conflicts, random access, stream stalls.
- Interface-bound: AXI width, valid/ready bubbles, packet framing, host bandwidth.
- Routing-bound: high fanout control, over-wide buses, too many parallel lanes.
- Latency-bound: pipeline depth, RAM latency, CDC, external memory round trips.

## Architecture Guidance

- If memory-bound, prefer reuse, tiling, caching, banking, wider bursts, or stream fusion.
- If compute-bound, prefer more parallel lanes, deeper pipelining, DSP mapping, or reduced precision.
- If interface-bound, simplify protocol, aggregate transfers, or add buffering.
- If resource-bound, reduce unrolling, share operators, or move work across cycles.

## Output Format

Add a concise section to `docs/design.md`:

```markdown
## Roofline Analysis
- Operations per item:
- Bytes per item:
- Operational intensity:
- Peak compute estimate:
- Peak bandwidth estimate:
- Limiting factor:
- Architecture consequence:
```

If inputs are missing, state assumptions clearly and mark the estimate as provisional.
