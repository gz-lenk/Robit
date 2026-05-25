# Vitis Timing Analyzer

Optional timing-analysis wrapper for RTL synthesis on the default Xilinx Alveo V80 target at 400MHz.

The package contains:

- `vitis_timing_analyzer.py`: Python CLI wrapper.
- `vitis_timing_analyzer.tcl`: Vivado/Vitis Tcl worker.

The tool is registered in `code.py` as `vitis_timming_analyzer`, but it is disabled by default and no agent or teammate has permission to call it.

Dry run:

```powershell
python tools\vitis_timming_analyzer\vitis_timing_analyzer.py `
  --top my_top `
  --rtl rtl `
  --dry-run
```

Run when Vivado is available:

```powershell
python tools\vitis_timming_analyzer\vitis_timing_analyzer.py `
  --top my_top `
  --rtl rtl `
  --xdc constraints\top.xdc `
  --out-dir build\vitis_timing
```
