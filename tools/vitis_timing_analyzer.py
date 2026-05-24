#!/usr/bin/env python3
"""
Run out-of-context Vivado/Vitis synthesis and extract critical path logic levels
and high-fanout nets.

This script intentionally does not run unless invoked directly. It expects a
Vivado/Vitis installation that provides the `vivado` Tcl batch executable.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
TCL_SCRIPT = SCRIPT_DIR / "vitis_timing_analyzer.tcl"
DEFAULT_PART = "xcv80-lsva4737-2MHP-e-S"
DEFAULT_BOARD_PART = "xilinx.com:v80:part0:1.0"
DEFAULT_CLOCK_PERIOD_NS = 2.5


def split_csv(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run Vivado synthesis and summarize critical paths/fanout.")
    parser.add_argument("--top", required=True, help="Top RTL module name.")
    parser.add_argument("--rtl", nargs="+", required=True,
                        help="RTL files or directories to synthesize.")
    parser.add_argument("--part", default=DEFAULT_PART,
                        help=f"FPGA part. Default: {DEFAULT_PART} (Alveo V80).")
    parser.add_argument("--board-part", default=DEFAULT_BOARD_PART,
                        help=("Optional Vivado board_part. Default: "
                              f"{DEFAULT_BOARD_PART}. Use '' to disable."))
    parser.add_argument("--xdc", nargs="*", default=[],
                        help="Optional XDC constraints.")
    parser.add_argument("--out-dir", default="build/vitis_timing",
                        help="Output directory.")
    parser.add_argument("--jobs", type=int, default=max(os.cpu_count() or 1, 1),
                        help="Parallel Vivado jobs for implementation commands.")
    parser.add_argument("--strategies", default="default",
                        help=("Comma-separated synthesis strategies. "
                              "Use multiple values for parallel runs."))
    parser.add_argument("--vivado", default=shutil.which("vivado") or "vivado",
                        help="Vivado executable path.")
    parser.add_argument("--clock-period", type=float,
                        default=DEFAULT_CLOCK_PERIOD_NS,
                        help=("Clock period in ns when no XDC exists. "
                              f"Default: {DEFAULT_CLOCK_PERIOD_NS}ns (400MHz)."))
    parser.add_argument("--clock-port", default="clk",
                        help="Clock port for generated fallback clock.")
    parser.add_argument("--max-paths", type=int, default=20,
                        help="Number of timing paths to report.")
    parser.add_argument("--max-fanout", type=int, default=50,
                        help="Number of high-fanout nets to report.")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print planned commands without running Vivado.")
    return parser.parse_args()


def collect_rtl(paths: list[str]) -> list[Path]:
    suffixes = {".v", ".sv", ".vh", ".svh"}
    files: list[Path] = []
    for item in paths:
        path = Path(item).resolve()
        if path.is_dir():
            files.extend(p.resolve() for p in path.rglob("*")
                         if p.suffix.lower() in suffixes)
        elif path.is_file():
            files.append(path)
        else:
            raise FileNotFoundError(f"RTL path not found: {item}")
    return sorted(dict.fromkeys(files))


def run_one(args: argparse.Namespace, strategy: str, rtl_files: list[Path],
            xdc_files: list[Path]) -> dict:
    out_dir = Path(args.out_dir).resolve() / strategy
    out_dir.mkdir(parents=True, exist_ok=True)
    summary_json = out_dir / "summary.json"
    cmd = [
        args.vivado, "-mode", "batch", "-source", str(TCL_SCRIPT), "-tclargs",
        "--top", args.top,
        "--part", args.part,
        "--board_part", args.board_part,
        "--rtl", ";".join(str(p) for p in rtl_files),
        "--xdc", ";".join(str(p) for p in xdc_files),
        "--out_dir", str(out_dir),
        "--jobs", str(args.jobs),
        "--strategy", strategy,
        "--max_paths", str(args.max_paths),
        "--max_fanout", str(args.max_fanout),
        "--summary_json", str(summary_json),
    ]
    if args.clock_period is not None:
        cmd.extend(["--clock_period", str(args.clock_period),
                    "--clock_port", args.clock_port])

    if args.dry_run:
        return {"strategy": strategy, "command": cmd, "dry_run": True}

    proc = subprocess.run(cmd, cwd=Path.cwd(), text=True,
                          capture_output=True, timeout=None)
    result = {
        "strategy": strategy,
        "returncode": proc.returncode,
        "stdout_tail": proc.stdout[-4000:],
        "stderr_tail": proc.stderr[-4000:],
        "summary_json": str(summary_json),
    }
    if summary_json.exists():
        result["summary"] = json.loads(summary_json.read_text())
    return result


def rank_results(results: list[dict]) -> list[dict]:
    def score(item: dict) -> tuple[float, int]:
        summary = item.get("summary", {})
        wns = float(summary.get("wns", -999999))
        worst_level = int(summary.get("worst_logic_levels", 999999))
        return (-wns, worst_level)

    return sorted(results, key=score)


def write_combined_report(out_dir: Path, results: list[dict]) -> Path:
    report = out_dir / "combined_report.md"
    lines = ["# Vitis Timing Analysis", ""]
    for item in rank_results(results):
        strategy = item.get("strategy", "unknown")
        lines.append(f"## Strategy: {strategy}")
        if item.get("dry_run"):
            lines.append("")
            lines.append("Dry run command:")
            lines.append("```text")
            lines.append(" ".join(item["command"]))
            lines.append("```")
            lines.append("")
            continue
        summary = item.get("summary", {})
        lines.extend([
            "",
            f"- Return code: {item.get('returncode')}",
            f"- WNS: {summary.get('wns', 'unknown')}",
            f"- Worst path logic levels: {summary.get('worst_logic_levels', 'unknown')}",
            f"- Summary JSON: `{item.get('summary_json')}`",
            "",
            "### Critical Paths",
        ])
        for path in summary.get("critical_paths", [])[:10]:
            lines.append(
                f"- Slack {path.get('slack')}, levels {path.get('levels')}: "
                f"{path.get('startpoint')} -> {path.get('endpoint')}")
        lines.extend(["", "### High-Fanout Nets"])
        for net in summary.get("high_fanout_nets", [])[:20]:
            lines.append(f"- {net.get('name')}: fanout {net.get('fanout')}")
        lines.append("")
    report.write_text("\n".join(lines), encoding="utf-8")
    return report


def main() -> int:
    args = parse_args()
    rtl_files = collect_rtl(args.rtl)
    xdc_files = [Path(p).resolve() for p in args.xdc]
    missing_xdc = [str(p) for p in xdc_files if not p.exists()]
    if missing_xdc:
        raise FileNotFoundError(f"XDC path not found: {missing_xdc}")
    if not rtl_files:
        raise ValueError("No RTL files found")

    strategies = split_csv(args.strategies)
    out_dir = Path(args.out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    results = []
    max_workers = max(1, min(len(strategies), args.jobs))
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = [
            pool.submit(run_one, args, strategy, rtl_files, xdc_files)
            for strategy in strategies
        ]
        for future in as_completed(futures):
            results.append(future.result())

    (out_dir / "combined_results.json").write_text(
        json.dumps(results, indent=2), encoding="utf-8")
    report = write_combined_report(out_dir, results)
    print(f"Wrote {report}")
    return 0 if all(r.get("returncode", 0) == 0 for r in results) else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(2)
