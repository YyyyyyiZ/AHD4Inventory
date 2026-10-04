"""Complete the approved overnight experiment with durable phase checkpoints."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import fcntl
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import traceback

from .api_client import BudgetedClient, atomic_json
from .data import scenario_specs
from .orchestrator import fit_one
from .protocol import DEFAULT_RUN, PROTOCOL, file_sha256, snapshot_sources


def now():
    return datetime.now(timezone.utc).isoformat()


def run_night(run_dir, *, workers=4, include_refits=True):
    root = Path(run_dir).resolve()
    phase = "initialization"
    status = dict(status="running", started_utc=now(), pid=os.getpid(), workers=workers,
                  planned_primary_runs=18, planned_refit_runs=9 if include_refits else 0,
                  budget_usd=PROTOCOL["api_budget_usd"], phases=[])
    status_file = root / "night_status.json"
    lock_handle = (root / "night.lock").open("a+")
    try:
        fcntl.flock(lock_handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        raise RuntimeError("An overnight controller is already running") from None

    def run_phase(name, module, arguments):
        nonlocal phase
        phase = name
        status.update(current_phase=name, updated_utc=now())
        atomic_json(status_file, status)
        log = root / ("night_"+name+".log")
        started = time.monotonic()
        env = os.environ.copy()
        for k in list(env):
            if "API_KEY" in k.upper() or "TOKEN" in k.upper() or "SECRET" in k.upper():
                env.pop(k)
        env.update(OPENBLAS_NUM_THREADS="1", OMP_NUM_THREADS="1", NUMBA_NUM_THREADS="1",
                   VECLIB_MAXIMUM_THREADS="1", PYTHONUNBUFFERED="1")
        command = [sys.executable, "-m", module, *arguments, "--run-dir", str(root)]
        with log.open("a") as handle:
            outcome = subprocess.run(command, stdout=handle, stderr=subprocess.STDOUT, env=env)
        status["phases"].append(dict(phase=name, exit_code=outcome.returncode,
                                      elapsed_seconds=time.monotonic()-started, finished_utc=now()))
        atomic_json(status_file, status)
        if outcome.returncode:
            raise RuntimeError(f"Phase {name} failed; inspect {log.name}")

    try:
        for scenario in scenario_specs():
            if not (root / "baselines" / scenario.scenario_id / "h200/completed.json").exists():
                fit_one(root, scenario.scenario_id)
        run_phase("primary", "examples.inventory.correlated_benchmark.orchestrator",
                  ["primary", "--workers", str(workers)])
        if include_refits:
            run_phase("refit", "examples.inventory.correlated_benchmark.orchestrator",
                      ["refit", "--workers", str(workers)])
            for h in (50, 100, 500):
                if not (root / "baselines/exp_ar_pos08_fixed6" / f"h{h}/completed.json").exists():
                    fit_one(root, "exp_ar_pos08_fixed6", h)
        # Every final source is fixed before the first holdout policy evaluation.
        frozen = {}
        for pattern in ("training/*/self_evolve_h*_r*/completed.json", "training/*/self_evolve_h*_r*/policy.py",
                        "baselines/*/h*/records.json"):
            for path in sorted(root.glob(pattern)):
                frozen[str(path.relative_to(root))] = file_sha256(path)
        seal = root / "all_policies_freeze.json"
        if seal.exists() and json.loads(seal.read_text())["sha256"] != frozen:
            raise ValueError("Policy set differs from the prior holdout seal")
        if not seal.exists():
            atomic_json(seal, dict(frozen_utc=now(), sha256=frozen, selection="training only"))
        run_phase("validation", "examples.inventory.correlated_benchmark.evaluation", ["--split", "validation"])
        run_phase("test", "examples.inventory.correlated_benchmark.evaluation", ["--split", "test"])
        run_phase("report", "examples.inventory.correlated_benchmark.analysis_report",
                  ["--plot-runtime", "/tmp/baek-plot-runtime-20260916"])
        summary = json.loads((root / "analysis_summary.json").read_text())
        if not summary.get("complete"):
            raise RuntimeError("Numerical report did not pass completeness/provenance checks")
        expected_rows = 720 if include_refits else 480
        if summary["total_rows"] != expected_rows:
            raise RuntimeError(f"Expected {expected_rows} test windows, found {summary['total_rows']}")
        budget = BudgetedClient(root).summary()
        if budget["committed_upper_usd"] > budget["limit_usd"] + 1e-9:
            raise RuntimeError("Budget audit failed")
        snapshot_sources(root, "implementation_final_snapshot")
        completions = [json.loads(p.read_text()) for p in root.glob("training/*/self_evolve_h*_r*/completed.json")]
        status.update(status="complete", current_phase="complete", finished_utc=now(),
                      generated_final_policies=len(completions),
                      candidate_slots=sum(len(list(p.glob("candidates/*.json.gz"))) for p in root.glob("training/*/self_evolve_h*_r*")),
                      model_calls=sum(x["model_calls"] for x in completions),
                      report=str(root / "report.md"), budget=budget)
        atomic_json(root / "completion.json", status)
        atomic_json(status_file, status)
        return status
    except BaseException as exc:
        status.update(status="paused" if (root / "PAUSE").exists() else "needs_attention",
                      current_phase=phase, updated_utc=now(), error_type=type(exc).__name__, error=str(exc))
        atomic_json(status_file, status)
        raise
    finally:
        fcntl.flock(lock_handle.fileno(), fcntl.LOCK_UN)
        lock_handle.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", type=Path, default=DEFAULT_RUN)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--primary-only", action="store_true")
    args = parser.parse_args()
    print(json.dumps(run_night(args.run_dir, workers=args.workers, include_refits=not args.primary_only)), flush=True)
