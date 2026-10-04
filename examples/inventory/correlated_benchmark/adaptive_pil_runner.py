"""Adaptive-PIL-initialized EOH; isolated additions leave earlier runs unchanged."""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from contextlib import contextmanager
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

from .api_client import BudgetedClient, ModelRequestError, atomic_json, MODEL
from .data import load_tapes, scenario_specs
from .protocol import DEFAULT_RUN as SHARED_RUN, PREVIOUS_RUN as CAPPED_RUN, file_sha256

DEFAULT_RUN = SHARED_RUN.parent / "20260916_adaptive_pil_seed"
LIMIT = 18.17
SOURCE_NAMES = ("adaptive_pil_runner.py", "adaptive_pil_seed.py", "adaptive_pil_worker.py")
PROTOCOL = {
    "protocol_id": "stationary-correlated-adaptive-pil-initialization-v1",
    "model": MODEL,
    "shared_budget_run_dir": str(SHARED_RUN),
    "shared_budget_limit_usd": LIMIT,
    "previous_committed_upper_usd": 1.82576175,
    "session_budget_usd": 20.0,
    "train_paths": 50, "validation_paths": 128, "test_paths": 1000,
    "training_horizon": 200, "burn_in": 500, "horizons": [50, 100, 200, 500],
    "evaluation_modes": {"steady": 500, "cold_start": 0},
    "primary_runs": 18,
    "evolution": {"operator": "m2", "population": 10, "generations": 10,
                  "repetitions": 3, "optimizer": "original SciPy L-BFGS-B",
                  "maxiter": 15, "eps": .1, "max_opt_params": None,
                  "initial_seed": "the scenario's frozen optimized Adaptive PIL",
                  "selection_parent": "best training policy"},
    "initialization": "exact outer five-parameter Adaptive PIL formula and the original frozen conditional projection bank",
    "seed_generation_zero": "original EOH may further optimize generation zero on train; compare final with the original frozen Adaptive PIL as well",
    "trusted_helpers": ["conditional_projected_inventory", "conditional_arrival_mean"],
    "search_freedom": "unbounded OPT_PARAM count; mutate the whole outer decision rule, add coefficients, or ignore helpers",
    "selection": "training only; retain the best training policy; no guarantee of test improvement",
    "holdout_gate": "all 18 policies frozen before new validation or test scoring",
    "comparators": ["conditional_pil", "forecast_adaptive_pil", "pil_cop_continuation",
                    "four-parameter base-stock initialization", "unrestricted base-stock initialization"],
    "data_source": str(CAPPED_RUN), "unrestricted_comparison_run": str(SHARED_RUN),
    "previous_holdout_seen": True,
    "interpretation": "exploratory initialization experiment on the existing benchmark; not a fresh unseen holdout",
}


def now():
    return datetime.now(timezone.utc).isoformat()


def source_hashes():
    folder = Path(__file__).parent
    names = (*SOURCE_NAMES, "evolution.py", "problem.py", "prompts.py", "fast_policy.py",
             "data.py", "environment.py", "baselines.py")
    return {name: file_sha256(folder / name) for name in names}


def verify_sources(root):
    expected = json.loads((Path(root) / "source_manifest.json").read_text())["sha256"]
    if source_hashes() != expected:
        raise ValueError("Warm-start training sources changed; do not resume silently")


def prepare(root):
    root = Path(root).resolve()
    root.mkdir(parents=True, exist_ok=True)
    protocol = root / "protocol.json"
    if protocol.exists():
        if json.loads(protocol.read_text())["configuration"] != PROTOCOL:
            raise ValueError("Warm-start protocol mismatch")
    else:
        atomic_json(protocol, {"created_utc": now(), "configuration": PROTOCOL})
    if (root / "input_manifest.json").exists():
        manifest = json.loads((root / "input_manifest.json").read_text())
        for relative, expected in manifest["sha256"].items():
            if file_sha256(root / relative) != expected:
                raise ValueError("Reused input changed: " + relative)
        return manifest
    copied = {}
    def copy(source):
        relative = source.relative_to(CAPPED_RUN)
        dest = root / relative
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, dest)
        copied[str(relative)] = file_sha256(source)
        if file_sha256(dest) != copied[str(relative)]:
            raise ValueError("Input copy mismatch")
    for source in sorted((CAPPED_RUN / "datasets").glob("*/*.npz")):
        copy(source)
    for name in ("dataset_manifest.json", "dataset_diagnostics.json", "DATASET.md"):
        copy(CAPPED_RUN / name)
    for spec in scenario_specs():
        folder = CAPPED_RUN / "baselines" / spec.scenario_id / "h200"
        for name in ("records.json", "completed.json"):
            copy(folder / name)
        for source in sorted((CAPPED_RUN / "evaluation" / spec.scenario_id).glob("baseline_h200_*/*")):
            if source.is_file():
                copy(source)
    manifest = {"created_utc": now(), "source_run": str(CAPPED_RUN), "sha256": copied,
                "old_evolved_policies_copied": False, "shared_budget_run_dir": str(SHARED_RUN)}
    atomic_json(root / "input_manifest.json", manifest)
    return manifest


def freeze_sources(root):
    root = Path(root).resolve()
    hashes = source_hashes()
    path = root / "source_manifest.json"
    if path.exists():
        verify_sources(root)
        return
    folder = root / "source_snapshot"
    folder.mkdir(exist_ok=True)
    for name in hashes:
        shutil.copy2(Path(__file__).with_name(name), folder / name)
    atomic_json(path, {"frozen_utc": now(), "sha256": hashes})


class SharedClient(BudgetedClient):
    def __init__(self, experiment_root):
        self.experiment_root = Path(experiment_root).resolve()
        super().__init__(SHARED_RUN, limit_usd=LIMIT, model=MODEL)

    def chat(self, *args, **kwargs):
        if (self.experiment_root / "PAUSE").exists():
            raise ModelRequestError("Warm-start experiment paused before request submission")
        return super().chat(*args, **kwargs)


@contextmanager
def adaptive_runtime(record):
    """Bind the existing EOH adapter in this experiment's private job process."""
    from . import evolution, problem, prompts
    from .adaptive_pil_worker import AdaptivePILWorker, prepare_policy
    from .adaptive_pil_seed import seed_code, seed_helpers_description

    class PILPrompts(prompts.GetPrompts):
        def get_task(self):
            return super().get_task() + (
                "The initial historical policy is the already optimized Adaptive PIL policy. "
                "You may change its full decision formula, add or remove tunable coefficients, "
                "use the observation arrays, or ignore the supplied forecast helpers.\n")

        def get_other_inf(self):
            base = super().get_other_inf().replace("helper functions,", "additional function definitions,")
            return base + ("The trusted forecast functions are already available; do not import or redefine them.\n"
                           + seed_helpers_description(record))

    class PILProblem(problem.TrainingProblem):
        def _get_worker(self):
            if self._worker is None:
                self._worker = AdaptivePILWorker(self.train_tapes, self.scenario, baseline_record=record,
                    burnin=self.burnin, horizon=self.horizon, timeout=max(1., self.evaluation_timeout - 5.),
                    max_opt_params=self.max_opt_params, python_executable=self.python_executable)
            return self._worker

    replacements = [(evolution, "TrainingProblem", PILProblem),
                    (evolution, "prepare_policy", prepare_policy),
                    (problem, "prepare_policy", prepare_policy),
                    (problem, "GetPrompts", PILPrompts)]
    previous = [(module, name, getattr(module, name)) for module, name, _ in replacements]
    try:
        for module, name, value in replacements:
            setattr(module, name, value)
        yield evolution, seed_code(record)
    finally:
        for module, name, value in reversed(previous):
            setattr(module, name, value)


def train_one(root, sid, repeat, *, client=None, population=10, generations=10):
    root = Path(root).resolve()
    if repeat not in (1, 2, 3):
        raise ValueError("The experiment has three independent repeats")
    verify_sources(root)
    spec = next(spec for spec in scenario_specs() if spec.scenario_id == sid)
    tapes = load_tapes(root / "datasets" / sid / "train.npz", spec)
    record = json.loads((root / "baselines" / sid / "h200/records.json").read_text())["forecast_adaptive_pil"]
    policy_id = f"self_evolve_h200_r{repeat}"
    output = root / "training" / sid / policy_id
    output.mkdir(parents=True, exist_ok=True)
    completion_path = output / "completed.json"
    if completion_path.exists():
        return json.loads(completion_path.read_text())
    started = time.monotonic()
    atomic_json(output / "status.json", {"status": "running", "pid": os.getpid(), "started_utc": now()})
    with adaptive_runtime(record) as (evolution, code):
        definition = {"baseline_record_sha256": hashlib.sha256(json.dumps(record, sort_keys=True).encode()).hexdigest(),
                      "seed_code_sha256": hashlib.sha256(code.encode()).hexdigest(),
                      "training_tape_sha256": tapes["metadata"]["arrays_sha256"],
                      "source_sha256": source_hashes(), "population": population, "generations": generations,
                      "max_opt_params": None, "initial_baseline_train_cost_per_period": record["training"]["mean_cost_per_period"]}
        definition_path = output / "warmstart_definition.json"
        if definition_path.exists() and json.loads(definition_path.read_text()) != definition:
            raise ValueError("Warm-start identity changed")
        if not definition_path.exists():
            atomic_json(definition_path, definition)
        pool = output / "initial_pool.json"
        initial = [{"algorithm": "Frozen optimized Adaptive PIL with its original conditional projection.",
                    "code": code, "objective": None, "other_inf": None}]
        if pool.exists() and json.loads(pool.read_text()) != initial:
            raise ValueError("Adaptive PIL initial population changed")
        if not pool.exists():
            atomic_json(pool, initial)
        result = evolution.run_evolution(scenario=spec, train_tapes=tapes, output_dir=output,
            client=client or SharedClient(root), population_size=population, generations=generations,
            optimizer_maxiter=15, max_opt_params=None, burnin=500, horizon=200, repeat=repeat,
            resume=True, model_name=MODEL, evaluation_timeout=180.)
    result.update(scenario_id=sid, policy_id=policy_id, family="self_evolve", repeat=repeat,
                  source_training_horizon=200, initial_policy_family="forecast_adaptive_pil",
                  full_protocol=population == generations == 10, finished_utc=now(),
                  elapsed_seconds=time.monotonic()-started)
    if result["status"] not in {"complete", "completed"}:
        raise RuntimeError("Warm-start run did not complete")
    if result["best_train_cost"] / 200 > record["training"]["mean_cost_per_period"] + 1e-5:
        raise ValueError("Final training policy is worse than the included Adaptive PIL seed")
    atomic_json(completion_path, result)
    atomic_json(output / "status.json", result)
    return result


def jobs():
    return [(spec.scenario_id, repeat) for repeat in (1, 2, 3) for spec in scenario_specs()]


def verify_frozen(root, *, create=False):
    root = Path(root).resolve()
    verify_sources(root)
    hashes = {}
    for sid, repeat in jobs():
        folder = root / "training" / sid / f"self_evolve_h200_r{repeat}"
        p = folder / "completed.json"
        if not p.exists():
            raise RuntimeError("All 18 policies must finish before holdout evaluation")
        x = json.loads(p.read_text())
        if (x.get("status") not in {"complete", "completed"} or not x.get("full_protocol")
                or x.get("scenario_id") != sid or x.get("repeat") != repeat
                or x.get("source_training_horizon") != 200
                or Path(x["best_code_path"]).resolve() != (folder / "policy.py").resolve()
                or file_sha256(folder / "policy.py") != x["code_sha256"]):
            raise ValueError("Warm-start completion/source mismatch")
        for source in (p, folder / "policy.py", folder / "warmstart_definition.json"):
            hashes[str(source.relative_to(root))] = file_sha256(source)
        baseline = root / "baselines" / sid / "h200/records.json"
        hashes[str(baseline.relative_to(root))] = file_sha256(baseline)
    seal = root / "all_policies_freeze.json"
    if seal.exists():
        if json.loads(seal.read_text())["sha256"] != hashes:
            raise ValueError("Warm-start frozen policy set changed")
    elif create:
        atomic_json(seal, {"frozen_utc": now(), "sha256": hashes, "selection": "training only"})
    else:
        raise RuntimeError("Warm-start policy set is not sealed")


def evaluate(root, split):
    from .adaptive_pil_worker import AdaptivePILWorker
    from .evaluation import WINDOWS, write_windows, _existing
    root = Path(root).resolve()
    if split not in {"validation", "test"}:
        raise ValueError("Invalid holdout split")
    verify_frozen(root)
    for spec in scenario_specs():
        tapes = load_tapes(root / "datasets" / spec.scenario_id / f"{split}.npz", spec)
        record = json.loads((root / "baselines" / spec.scenario_id / "h200/records.json").read_text())["forecast_adaptive_pil"]
        with AdaptivePILWorker(tapes, spec, baseline_record=record, burnin=500, horizon=500,
                               timeout=180., max_opt_params=None) as worker:
            for repeat in (1, 2, 3):
                policy_id = f"self_evolve_h200_r{repeat}"
                folder = root / "training" / spec.scenario_id / policy_id
                completion = json.loads((folder / "completed.json").read_text())
                tape_hash, code_hash = tapes["metadata"]["arrays_sha256"], completion["code_sha256"]
                if _existing(root, spec.scenario_id, policy_id, split, code_hash, None, tape_hash) is not None:
                    continue
                started = time.monotonic()
                answer = worker.evaluate_windows((folder / "policy.py").read_text(), WINDOWS)
                write_windows(root, spec, policy_id, split, answer["windows"], family="self_evolve",
                    repeat=repeat, source_training_horizon=200, dataset_arrays_sha256=tape_hash,
                    code_sha256=code_hash, full_protocol=True, evaluation_seconds=time.monotonic()-started)


def run(root, workers=2):
    root = Path(root).resolve()
    verify_sources(root)
    lock = (root / "night.lock").open("a+")
    fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    state = {"status": "running", "pid": os.getpid(), "started_utc": now(), "workers": workers,
             "planned_runs": 18, "current_phase": "training", "shared_budget_run_dir": str(SHARED_RUN)}
    def status(**fields):
        state.update(fields, updated_utc=now()); atomic_json(root / "night_status.json", state)
    env = os.environ.copy()
    for key in list(env):
        if any(marker in key.upper() for marker in ("API_KEY", "TOKEN", "SECRET")):
            env.pop(key)
    env.update(OPENBLAS_NUM_THREADS="1", OMP_NUM_THREADS="1", NUMBA_NUM_THREADS="1",
               VECLIB_MAXIMUM_THREADS="1", PYTHONUNBUFFERED="1")
    def dispatch(job):
        sid, repeat = job
        if (root / "PAUSE").exists() or (SHARED_RUN / "PAUSE").exists():
            return {"scenario_id": sid, "repeat": repeat, "status": "paused"}
        folder = root / "job_logs"; folder.mkdir(exist_ok=True)
        command = [sys.executable, "-m", "examples.inventory.correlated_benchmark.adaptive_pil_runner",
                   "train", "--run-dir", str(root), "--scenario", sid, "--repeat", str(repeat)]
        with (folder / f"{sid}_r{repeat}.log").open("a") as log:
            outcome = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, env=env)
        item = {"scenario_id": sid, "repeat": repeat, "exit_code": outcome.returncode,
                "status": "complete" if outcome.returncode == 0 else "failed"}
        atomic_json(folder / f"{sid}_r{repeat}.json", item)
        return item
    try:
        status()
        results = []
        with ThreadPoolExecutor(max_workers=workers) as pool:
            for future in as_completed([pool.submit(dispatch, job) for job in jobs()]):
                item = future.result(); results.append(item)
                atomic_json(root / "training_jobs.json", results)
                print(json.dumps(item), flush=True)
        if any(item["status"] != "complete" for item in results):
            raise RuntimeError("One or more warm-start training jobs need attention")
        verify_frozen(root, create=True)
        for split in ("validation", "test"):
            status(current_phase=split); evaluate(root, split)
        status(current_phase="report")
        command = [sys.executable, "-m", "examples.inventory.correlated_benchmark.adaptive_pil_report",
                   "--run-dir", str(root), "--capped-run", str(CAPPED_RUN), "--unrestricted-run", str(SHARED_RUN)]
        with (root / "report.log").open("a") as log:
            outcome = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, env=env)
        if outcome.returncode:
            raise RuntimeError("Warm-start report failed")
        report_summary = json.loads((root / "adaptive_pil_summary.json").read_text())
        if not report_summary.get("completed_primary"):
            raise RuntimeError("Warm-start report has incomplete primary coverage")
        status(status="complete", current_phase="complete", completed_runs=18, finished_utc=now())
        atomic_json(root / "completion.json", state)
    except BaseException as exc:
        status(status="paused" if (root / "PAUSE").exists() or (SHARED_RUN / "PAUSE").exists() else "needs_attention",
               error_type=type(exc).__name__, error=str(exc))
        raise
    finally:
        fcntl.flock(lock.fileno(), fcntl.LOCK_UN); lock.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("prepare", "train", "run", "evaluate"))
    parser.add_argument("--run-dir", type=Path, default=DEFAULT_RUN)
    parser.add_argument("--scenario")
    parser.add_argument("--repeat", type=int, default=1)
    parser.add_argument("--workers", type=int, default=2)
    parser.add_argument("--split", choices=("validation", "test"), default="test")
    args = parser.parse_args()
    if args.command == "prepare":
        prepare(args.run_dir); freeze_sources(args.run_dir)
    elif args.command == "train":
        print(json.dumps(train_one(args.run_dir, args.scenario, args.repeat)), flush=True)
    elif args.command == "evaluate":
        evaluate(args.run_dir, args.split)
    else:
        run(args.run_dir, args.workers)


if __name__ == "__main__":
    main()
