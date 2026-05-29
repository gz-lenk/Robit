#!/usr/bin/env python3
"""
Run spec-to-RTL dataset prompts through code.py and verify generated RTL with
the official SystemVerilog testbenches.

The runner is intentionally external to code.py. It feeds each Prob*_prompt.txt
as stdin to the CLI agent, asks it to write TopModule.sv in a per-problem
workspace, then compiles the generated RTL with Prob*_ref.sv and Prob*_test.sv.
"""

from __future__ import annotations

import argparse
import csv
import re
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATASET = REPO_ROOT / "datasets" / "dataset_spec-to-rtl"
DEFAULT_OUT = REPO_ROOT / "workspace" / "eval" / "spec_to_rtl"


@dataclass
class Problem:
    name: str
    prompt: Path
    ref: Path
    testbench: Path


@dataclass
class Result:
    name: str
    status: str
    rtl: Path
    elapsed_s: float
    agent_log: Path
    sim_log: Path | None
    detail: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Evaluate code.py on datasets/dataset_spec-to-rtl.")
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET,
                        help="Dataset directory containing Prob*_prompt.txt.")
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT,
                        help="Evaluation output directory.")
    parser.add_argument("--problem", action="append", default=[],
                        help=("Problem name or prefix, e.g. Prob001_zero or "
                              "Prob001. Can be repeated."))
    parser.add_argument("--limit", type=int, default=None,
                        help="Maximum number of discovered problems to run.")
    parser.add_argument("--all", action="store_true",
                        help="Run all discovered problems.")
    parser.add_argument("--agent-timeout", type=int, default=300,
                        help="Seconds before killing one agent run.")
    parser.add_argument("--sim-timeout", type=int, default=60,
                        help="Seconds before killing one simulation.")
    parser.add_argument("--python", default=sys.executable,
                        help="Python executable for code.py.")
    parser.add_argument("--iverilog", default=shutil.which("iverilog") or "iverilog",
                        help="iverilog executable.")
    parser.add_argument("--vvp", default=shutil.which("vvp") or "vvp",
                        help="vvp executable.")
    parser.add_argument("--no-agent", action="store_true",
                        help="Skip agent generation and verify existing RTL files.")
    parser.add_argument("--no-sim", action="store_true",
                        help="Skip iverilog/vvp verification.")
    parser.add_argument("--clean", action="store_true",
                        help="Delete output directory before running.")
    return parser.parse_args()


def discover(dataset: Path) -> list[Problem]:
    problems = []
    for prompt in sorted(dataset.glob("Prob*_prompt.txt")):
        name = prompt.name.removesuffix("_prompt.txt")
        ref = dataset / f"{name}_ref.sv"
        testbench = dataset / f"{name}_test.sv"
        if ref.exists() and testbench.exists():
            problems.append(Problem(name, prompt, ref, testbench))
    return problems


def select_problems(problems: list[Problem], requested: list[str],
                    limit: int | None, run_all: bool) -> list[Problem]:
    if requested:
        selected = []
        for item in requested:
            matches = [p for p in problems
                       if p.name == item or p.name.startswith(item)]
            if not matches:
                raise ValueError(f"No problem matched {item}")
            selected.extend(matches)
        seen = set()
        unique = []
        for problem in selected:
            if problem.name not in seen:
                unique.append(problem)
                seen.add(problem.name)
        return unique[:limit] if limit else unique
    if run_all:
        return problems[:limit] if limit else problems
    return problems[:limit or 1]


def build_agent_prompt(prompt_path: Path, rtl_path: Path) -> str:
    rel_prompt = prompt_path.relative_to(REPO_ROOT / "workspace")
    rel_rtl = rtl_path.relative_to(REPO_ROOT / "workspace")
    return (
        "Read the HDLBits-style spec-to-RTL prompt from "
        f"`{rel_prompt.as_posix()}` and implement the DUT. "
        "Implement only the module named TopModule. Write synthesizable "
        "Verilog/SystemVerilog only. Do not include RefModule, tb, "
        "stimulus_gen, markdown fences, or prose in the RTL file. "
        "Do not delegate this benchmark task to teammates and do not create "
        "tasks; solve it directly in the main agent. "
        f"Save the final RTL to `{rel_rtl.as_posix()}` relative to the "
        "working directory. After writing the file, stop with a short summary."
    )


def run_agent(args: argparse.Namespace, problem: Problem,
              case_dir: Path, rtl_path: Path) -> tuple[bool, Path, str, float]:
    prompt_path = case_dir / "prompt.txt"
    shutil.copy2(problem.prompt, prompt_path)
    prompt = build_agent_prompt(prompt_path, rtl_path)
    log_path = case_dir / "agent.log"
    stdin = prompt + "\nq\n"
    started = time.time()
    try:
        proc = subprocess.run(
            [args.python, str(REPO_ROOT / "code.py")],
            input=stdin,
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            timeout=args.agent_timeout,
        )
        elapsed = time.time() - started
        log_path.write_text(proc.stdout + proc.stderr, encoding="utf-8")
        if proc.returncode != 0:
            return False, log_path, f"agent exited {proc.returncode}", elapsed
        if not rtl_path.exists():
            return False, log_path, "agent did not create RTL file", elapsed
        return True, log_path, "agent generated RTL", elapsed
    except subprocess.TimeoutExpired as exc:
        elapsed = time.time() - started
        output = (exc.stdout or "") + (exc.stderr or "")
        log_path.write_text(str(output), encoding="utf-8")
        return False, log_path, "agent timeout", elapsed


def sanitize_generated_rtl(rtl_path: Path) -> None:
    text = rtl_path.read_text(encoding="utf-8", errors="replace")
    match = re.search(r"module\s+TopModule\b.*?endmodule", text, re.S)
    if match:
        rtl_path.write_text(match.group(0).strip() + "\n", encoding="utf-8")


def run_sim(args: argparse.Namespace, problem: Problem,
            case_dir: Path, rtl_path: Path) -> tuple[str, Path, str]:
    sim_dir = case_dir / "sim"
    sim_dir.mkdir(parents=True, exist_ok=True)
    dut = sim_dir / "TopModule.sv"
    ref = sim_dir / problem.ref.name
    tb = sim_dir / problem.testbench.name
    shutil.copy2(rtl_path, dut)
    shutil.copy2(problem.ref, ref)
    shutil.copy2(problem.testbench, tb)

    simv = sim_dir / "simv.out"
    compile_log = sim_dir / "compile.log"
    run_log = sim_dir / "run.log"
    if shutil.which(args.iverilog) is None and not Path(args.iverilog).exists():
        compile_log.write_text(f"iverilog not found: {args.iverilog}\n",
                               encoding="utf-8")
        return "SIM_TOOL_MISSING", compile_log, "iverilog not found"
    if shutil.which(args.vvp) is None and not Path(args.vvp).exists():
        run_log.write_text(f"vvp not found: {args.vvp}\n", encoding="utf-8")
        return "SIM_TOOL_MISSING", run_log, "vvp not found"
    cmd = [args.iverilog, "-g2012", "-Wall", "-o", str(simv),
           str(ref), str(dut), str(tb)]
    try:
        comp = subprocess.run(cmd, cwd=sim_dir, text=True,
                              capture_output=True, timeout=args.sim_timeout)
        compile_log.write_text(comp.stdout + comp.stderr, encoding="utf-8")
        if comp.returncode != 0:
            return "COMPILE_FAIL", compile_log, f"iverilog exited {comp.returncode}"
        run = subprocess.run([args.vvp, str(simv)], cwd=sim_dir, text=True,
                             capture_output=True, timeout=args.sim_timeout)
        run_log.write_text(run.stdout + run.stderr, encoding="utf-8")
        output = run.stdout + run.stderr
        if run.returncode != 0:
            return "SIM_FAIL", run_log, f"vvp exited {run.returncode}"
        if re.search(r"Mismatches:\s+0\s+in\s+", output):
            return "PASS", run_log, "0 mismatches"
        if "TIMEOUT" in output:
            return "SIM_FAIL", run_log, "simulation timeout"
        mismatch = re.search(r"Mismatches:\s+([0-9]+)\s+in\s+([0-9]+)", output)
        if mismatch:
            return "FAIL", run_log, mismatch.group(0)
        return "UNKNOWN", run_log, "no mismatch summary found"
    except subprocess.TimeoutExpired:
        run_log.write_text("simulation command timeout\n", encoding="utf-8")
        return "SIM_TIMEOUT", run_log, "simulation command timeout"


def evaluate_one(args: argparse.Namespace, problem: Problem) -> Result:
    case_dir = args.out_dir / problem.name
    case_dir.mkdir(parents=True, exist_ok=True)
    rtl_path = case_dir / "TopModule.sv"
    agent_log = case_dir / "agent.log"
    elapsed = 0.0

    if not args.no_agent:
        ok, agent_log, detail, elapsed = run_agent(args, problem, case_dir, rtl_path)
        if not ok:
            return Result(problem.name, "AGENT_FAIL", rtl_path, elapsed,
                          agent_log, None, detail)
    elif not rtl_path.exists():
        return Result(problem.name, "MISSING_RTL", rtl_path, elapsed,
                      agent_log, None, "existing RTL file not found")

    sanitize_generated_rtl(rtl_path)
    if args.no_sim:
        return Result(problem.name, "GENERATED", rtl_path, elapsed,
                      agent_log, None, "simulation skipped")

    status, sim_log, detail = run_sim(args, problem, case_dir, rtl_path)
    return Result(problem.name, status, rtl_path, elapsed,
                  agent_log, sim_log, detail)


def print_result(result: Result) -> None:
    sim_log = str(result.sim_log) if result.sim_log else "-"
    print(f"{result.name}: {result.status} ({result.detail})")
    print(f"  rtl: {result.rtl}")
    print(f"  agent_log: {result.agent_log}")
    print(f"  sim_log: {sim_log}")


def write_summary(out_dir: Path, results: list[Result]) -> None:
    csv_path = out_dir / "summary.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["problem", "status", "elapsed_s", "detail",
                         "rtl", "agent_log", "sim_log"])
        for result in results:
            writer.writerow([
                result.name, result.status, f"{result.elapsed_s:.2f}",
                result.detail, result.rtl, result.agent_log,
                result.sim_log or "",
            ])

    counts: dict[str, int] = {}
    for result in results:
        counts[result.status] = counts.get(result.status, 0) + 1
    lines = ["# Spec-to-RTL Evaluation", ""]
    lines.extend(f"- {status}: {count}" for status, count in sorted(counts.items()))
    lines.extend(["", "| Problem | Status | Detail |",
                  "| --- | --- | --- |"])
    for result in results:
        lines.append(f"| {result.name} | {result.status} | {result.detail} |")
    (out_dir / "summary.md").write_text("\n".join(lines) + "\n",
                                        encoding="utf-8")


def main() -> int:
    args = parse_args()
    args.dataset = args.dataset.resolve()
    args.out_dir = args.out_dir.resolve()
    if args.clean and args.out_dir.exists():
        shutil.rmtree(args.out_dir)
    args.out_dir.mkdir(parents=True, exist_ok=True)

    problems = select_problems(discover(args.dataset), args.problem,
                               args.limit, args.all)
    if not problems:
        raise SystemExit("No problems selected")

    if not args.no_sim:
        missing = [tool for tool in (args.iverilog, args.vvp)
                   if shutil.which(tool) is None and not Path(tool).exists()]
        if missing:
            print(f"Warning: simulator tools may be missing: {missing}",
                  file=sys.stderr)

    results = []
    for problem in problems:
        result = evaluate_one(args, problem)
        results.append(result)
        print_result(result)

    write_summary(args.out_dir, results)
    passed = sum(1 for result in results if result.status == "PASS")
    print(f"\nSummary: {passed}/{len(results)} PASS")
    print(f"Summary files: {args.out_dir / 'summary.md'} and summary.csv")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
