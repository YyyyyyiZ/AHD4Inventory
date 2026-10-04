"""Resumable training and baseline fitting; model-generated code sees train only."""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import traceback

from .api_client import BudgetedClient, atomic_json
from .data import load_tapes, scenario_specs
from .prepare_data import prepare
from .protocol import DEFAULT_RUN, PROTOCOL, freeze_protocol


def scenario_by_id(name):
    return next(s for s in scenario_specs() if s.scenario_id == name)


def train_one(run_dir, scenario_id, repeat, horizon=200, *, population=10, generations=10):
    from .evolution import run_evolution
    scenario = scenario_by_id(scenario_id)
    train = load_tapes(Path(run_dir) / "datasets" / scenario_id / "train.npz", scenario)
    policy_id = f"self_evolve_h{horizon}_r{repeat}"
    full_protocol = population == 10 and generations == 10
    output = Path(run_dir) / ("training" if full_protocol else "pilots") / scenario_id / policy_id
    output.mkdir(parents=True, exist_ok=True)
    if (output / "completed.json").exists():
        return json.loads((output / "completed.json").read_text())
    started = time.monotonic()
    atomic_json(output / "status.json", dict(status="running", scenario_id=scenario_id,
                policy_id=policy_id, started_utc=datetime.now(timezone.utc).isoformat(), pid=os.getpid()))
    result = run_evolution(scenario=scenario, train_tapes=train, output_dir=output,
                 client=BudgetedClient(run_dir, limit_usd=PROTOCOL["api_budget_usd"]),
                 population_size=population, generations=generations,
                 optimizer_maxiter=PROTOCOL["evolution"]["maxiter"],
                 max_opt_params=PROTOCOL["evolution"]["max_opt_params"],
                 burnin=PROTOCOL["burn_in"], horizon=horizon, repeat=repeat, resume=True,
                 model_name=PROTOCOL["model"], evaluation_timeout=180.0)
    result.update(scenario_id=scenario_id, policy_id=policy_id, family="self_evolve", repeat=repeat,
                  source_training_horizon=horizon, elapsed_seconds=time.monotonic()-started,
                  finished_utc=datetime.now(timezone.utc).isoformat(),
                  full_protocol=full_protocol)
    if result.get("status") not in {"complete", "completed"}:
        atomic_json(output / "status.json", result)
        raise RuntimeError("Evolution returned an incomplete run")
    atomic_json(output / "completed.json", result)
    atomic_json(output / "status.json", result)
    return result


def fit_one(run_dir, scenario_id, horizon=200, *, strong=True):
    from .baselines import fit_baselines
    scenario = scenario_by_id(scenario_id)
    train = load_tapes(Path(run_dir) / "datasets" / scenario_id / "train.npz", scenario)
    output = Path(run_dir) / "baselines" / scenario_id / f"h{horizon}"
    output.mkdir(parents=True, exist_ok=True)
    record_path = output / "records.json"
    records = json.loads(record_path.read_text()) if record_path.exists() else {}
    started = time.monotonic()
    def progress(*args, **kwargs):
        # The baseline module emits a record for each completed family.
        record = kwargs.get("record")
        name = kwargs.get("name")
        if len(args) == 1 and isinstance(args[0], dict):
            item = args[0]
            record = item.get("record")
            name = item.get("name")
        elif len(args) >= 2:
            name, record = args[:2]
        if record is not None and name is not None:
            records[name] = record
            atomic_json(record_path, records)
        atomic_json(output / "status.json", dict(status="running", last_family=name,
                    completed_families=list(records), elapsed_seconds=time.monotonic()-started))
    records = fit_baselines(train, scenario, horizon=horizon, burnin=PROTOCOL["burn_in"],
                            inner_paths=128, existing=records, progress=progress,
                            convergence=True, strong=strong)
    atomic_json(record_path, records)
    atomic_json(output / "completed.json", dict(status="complete", scenario_id=scenario_id,
                source_training_horizon=horizon, families=list(records),
                elapsed_seconds=time.monotonic()-started, finished_utc=datetime.now(timezone.utc).isoformat()))
    return records


def primary_jobs():
    return [dict(kind="train", scenario_id=s.scenario_id, repeat=r, horizon=200)
            for r in range(1, 4) for s in scenario_specs()]


def refit_jobs():
    return [dict(kind="train", scenario_id="exp_ar_pos08_fixed6", repeat=r, horizon=h)
            for h in (50, 100, 500) for r in range(1, 4)]


def run_jobs(run_dir, jobs, workers=3):
    run_dir = Path(run_dir)
    logs = run_dir / "job_logs"
    logs.mkdir(parents=True, exist_ok=True)
    def dispatch(job):
        if (run_dir / "PAUSE").exists():
            return {**job, "status": "paused"}
        name = f"{job['kind']}_{job['scenario_id']}_h{job['horizon']}_r{job.get('repeat',0)}"
        cmd = [sys.executable, "-m", "examples.inventory.correlated_benchmark.orchestrator",
               job["kind"], "--run-dir", str(run_dir), "--scenario", job["scenario_id"],
               "--horizon", str(job["horizon"])]
        if job["kind"] == "train":
            cmd += ["--repeat", str(job["repeat"])]
        env = os.environ.copy()
        for k in list(env):
            if "API_KEY" in k.upper() or "TOKEN" in k.upper() or "SECRET" in k.upper():
                env.pop(k)
        env.update(OPENBLAS_NUM_THREADS="1", OMP_NUM_THREADS="1", NUMBA_NUM_THREADS="1",
                   VECLIB_MAXIMUM_THREADS="1", PYTHONUNBUFFERED="1")
        started = time.monotonic()
        with (logs / (name + ".log")).open("a") as handle:
            completed = subprocess.run(cmd, stdout=handle, stderr=subprocess.STDOUT, env=env)
        item = {**job, "exit_code": completed.returncode,
                "status": "complete" if completed.returncode == 0 else "failed",
                "elapsed_seconds": time.monotonic()-started, "log": str(logs / (name + ".log"))}
        atomic_json(logs / (name + ".json"), item)
        return item
    results = []
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(dispatch, job) for job in jobs]
        for future in as_completed(futures):
            result = future.result()
            results.append(result)
            print(json.dumps(result), flush=True)
    return results


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["prepare", "train", "baseline", "primary", "refit", "baseline_all"])
    parser.add_argument("--run-dir", type=Path, default=DEFAULT_RUN)
    parser.add_argument("--scenario")
    parser.add_argument("--repeat", type=int, default=1)
    parser.add_argument("--horizon", type=int, default=200)
    parser.add_argument("--workers", type=int, default=3)
    parser.add_argument("--population", type=int, default=10)
    parser.add_argument("--generations", type=int, default=10)
    args = parser.parse_args()
    freeze_protocol(args.run_dir)
    if args.command == "prepare":
        prepare(args.run_dir)
    elif args.command == "train":
        result = train_one(args.run_dir, args.scenario, args.repeat, args.horizon,
                           population=args.population, generations=args.generations)
        print(json.dumps(result), flush=True)
    elif args.command == "baseline":
        fit_one(args.run_dir, args.scenario, args.horizon)
    else:
        if args.command == "refit":
            from .evaluation import verify_primary_frozen
            verify_primary_frozen(args.run_dir)
        jobs = primary_jobs() if args.command == "primary" else refit_jobs() if args.command == "refit" else [
            dict(kind="baseline", scenario_id=s.scenario_id, horizon=args.horizon) for s in scenario_specs()]
        result = run_jobs(args.run_dir, jobs, args.workers)
        atomic_json(args.run_dir / (args.command + "_jobs.json"), result)
        if any(r["status"] != "complete" for r in result):
            raise SystemExit(1)


if __name__ == "__main__":
    main()
