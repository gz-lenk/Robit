# Tools

## Vitis Timing Analyzer

`vitis_timing_analyzer.py` is an optional external tool for FPGA timing exploration. It does not run automatically and is not registered in `code.py` by default.

Default synthesis assumptions:

- Platform: Xilinx Alveo V80
- Part: `xcv80-lsva4737-2MHP-e-S`
- Board part: `xilinx.com:v80:part0:1.0`
- Clock target: 400MHz, expressed as a 2.5ns fallback clock period when no XDC is provided

The tool uses a Python wrapper plus a Vivado/Vitis Tcl worker:

- `vitis_timing_analyzer.py`: validates inputs, runs one or more synthesis strategies in parallel, and combines reports.
- `vitis_timing_analyzer.tcl`: runs synthesis/place/route, emits timing reports, extracts critical path logic levels, and lists high-fanout nets.

This split is preferred over a Tcl-only implementation because Python is better for CLI parsing, parallel strategy sweeps, output organization, and report post-processing, while Tcl stays focused on commands that must run inside Vivado.

Dry run:

```powershell
python tools\vitis_timing_analyzer.py `
  --top my_top `
  --rtl rtl `
  --dry-run
```

Run with Vivado available on `PATH`:

```powershell
python tools\vitis_timing_analyzer.py `
  --top my_top `
  --rtl rtl `
  --xdc constraints\top.xdc `
  --strategies default,Flow_PerfOptimized_high `
  --jobs 2 `
  --out-dir build\vitis_timing
```

Override defaults when needed:

```powershell
python tools\vitis_timing_analyzer.py `
  --top my_top `
  --rtl rtl `
  --part xcvu9p-flga2104-2L-e `
  --board-part "" `
  --clock-period 3.333
```

Agent integration:

- The tool is not currently exposed to the main agent or any teammate.
- When timing closure work is needed, register a wrapper in `code.py`, add the tool schema to `BUILTIN_TOOLS`, map it in `BUILTIN_HANDLERS`, and add the tool name to tester's policy.
- Keep it disabled by default because normal environments usually do not have Vivado/Vitis or V80 board files installed.

Main outputs:

- `combined_report.md`
- `combined_results.json`
- `<strategy>/summary.json`
- `<strategy>/timing_summary.rpt`
- `<strategy>/critical_paths.rpt`
- `<strategy>/high_fanout_nets.rpt`
- `<strategy>/routed.dcp`
