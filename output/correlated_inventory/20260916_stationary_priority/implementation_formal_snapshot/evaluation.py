"""Frozen-policy evaluation with a single trajectory for all horizon prefixes."""
from __future__ import annotations

import argparse
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import time
import uuid

import numpy as np

from .api_client import atomic_json
from .data import load_tapes, scenario_specs
from .protocol import DEFAULT_RUN, HORIZONS, PROTOCOL, file_sha256

WINDOWS = [(b, h) for b in (500, 0) for h in HORIZONS]
METRICS = ("total_cost", "holding_cost", "lost_sales_cost", "lost_units", "demand_units", "sales_units", "order_units")


def from_trace(trace, scenario, windows=WINDOWS):
    answers = []
    for burnin, horizon in windows:
        cut = trace[:, burnin:burnin+horizon]
        if cut.shape[1] != horizon:
            raise ValueError("Incomplete evaluation trajectory")
        holding = scenario.holding_cost * cut[:, :, 8].sum(axis=1)
        lost = cut[:, :, 7].sum(axis=1)
        penalty = scenario.lost_sales_cost * lost
        answers.append(dict(burnin=burnin, horizon=horizon,
            total_cost=holding+penalty, holding_cost=holding, lost_sales_cost=penalty,
            lost_units=lost, demand_units=cut[:, :, 5].sum(axis=1),
            sales_units=cut[:, :, 6].sum(axis=1), order_units=cut[:, :, 4].sum(axis=1)))
    return answers


def write_windows(run_dir, scenario, policy_id, split, windows, *, family, repeat,
                  source_training_horizon, dataset_arrays_sha256, code_sha256=None,
                  record_sha256=None, full_protocol=True, evaluation_seconds=None):
    run_dir = Path(run_dir).resolve()
    folder = run_dir / "evaluation" / scenario.scenario_id / policy_id
    folder.mkdir(parents=True, exist_ok=True)
    target = folder / (split + ".npz")
    arrays, records = {}, []
    for window in windows:
        b, h = int(window["burnin"]), int(window["horizon"])
        mode = "steady" if b else "cold_start"
        prefix = f"{mode}_h{h}"
        numerical = {key: np.asarray(window[key], dtype=np.float64) for key in METRICS}
        shapes = {a.shape for a in numerical.values()}
        if len(shapes) != 1 or any(a.ndim != 1 or not np.isfinite(a).all() or (a < 0).any() for a in numerical.values()):
            raise ValueError("Invalid frozen-policy path metrics")
        if not np.allclose(numerical["demand_units"], numerical["sales_units"]+numerical["lost_units"], rtol=1e-11, atol=1e-8):
            raise ValueError("Demand accounting mismatch")
        if not np.allclose(numerical["total_cost"], numerical["holding_cost"]+numerical["lost_sales_cost"], rtol=1e-11, atol=1e-8):
            raise ValueError("Cost accounting mismatch")
        arrays.update({prefix+"_"+key: array for key, array in numerical.items()})
        records.append(dict(scenario_id=scenario.scenario_id, policy_id=policy_id, family=family,
            repeat=repeat, split=split, mode=mode, horizon=h, burnin=b,
            source_training_horizon=source_training_horizon,
            costs_path=str(target.relative_to(run_dir)), array_prefix=prefix,
            dataset_arrays_sha256=dataset_arrays_sha256, code_sha256=code_sha256,
            record_sha256=record_sha256, full_protocol=full_protocol,
            n_paths=len(numerical["total_cost"]),
            mean_cost_per_period=float(numerical["total_cost"].mean()/h),
            holding_per_period=float(numerical["holding_cost"].mean()/h),
            lost_units_per_period=float(numerical["lost_units"].mean()/h),
            fill_rate=float(numerical["sales_units"].sum()/numerical["demand_units"].sum()),
            orders_per_period=float(numerical["order_units"].mean()/h),
            evaluation_seconds=evaluation_seconds,
            pipeline_info="known quoted arrival dates; overtaking allowed"))
    temporary = target.with_name(target.name+"."+uuid.uuid4().hex+".tmp")
    with temporary.open("wb") as handle:
        np.savez_compressed(handle, **arrays)
    temporary.replace(target)
    digest = file_sha256(target)
    for record in records:
        record["costs_file_sha256"] = digest
    atomic_json(folder / (split+".json"), records)
    return records


def _existing(run_dir, scenario_id, policy_id, split, code_hash, record_hash, tape_hash):
    target = Path(run_dir) / "evaluation" / scenario_id / policy_id / (split+".json")
    if not target.exists():
        return None
    records = json.loads(target.read_text())
    if (not isinstance(records, list) or len(records) != len(WINDOWS)
            or {(row.get("burnin"), row.get("horizon")) for row in records} != set(WINDOWS)):
        raise ValueError("Existing evaluation must contain all eight unique windows")
    for row in records:
        if row.get("scenario_id") != scenario_id or row.get("policy_id") != policy_id or row.get("split") != split:
            raise ValueError("Existing evaluation identity mismatch")
        if row["code_sha256"] != code_hash or row["record_sha256"] != record_hash or row["dataset_arrays_sha256"] != tape_hash:
            raise ValueError("Attempt to overwrite evaluation of a different frozen policy/tape")
        if file_sha256(Path(run_dir) / row["costs_path"]) != row["costs_file_sha256"]:
            raise ValueError("Evaluation array file was modified")
    return records


def evaluate_scenario(run_dir, scenario_id, *, split="test", include_refits=True):
    from .baselines import evaluate_baseline
    from .fast_policy import FastPolicyWorker
    run_dir = Path(run_dir).resolve()
    if split not in {"validation", "test"}:
        raise ValueError("Frozen-policy evaluation only accepts validation or test")
    if split == "test":
        verify_primary_frozen(run_dir)
    scenario = next(s for s in scenario_specs() if s.scenario_id == scenario_id)
    tapes = load_tapes(run_dir / "datasets" / scenario_id / (split+".npz"), scenario)
    tape_hash = tapes["metadata"]["arrays_sha256"]
    output_records = []
    baseline_paths = sorted((run_dir / "baselines" / scenario_id).glob("h*/records.json"))
    for path in baseline_paths:
        source_h = int(path.parent.name[1:])
        if not include_refits and source_h != 200:
            continue
        for name, record in json.loads(path.read_text()).items():
            if "theta" not in record:
                raise ValueError("Incomplete fitted baseline")
            record_hash = hashlib.sha256(json.dumps(record, sort_keys=True).encode()).hexdigest()
            policy_id = f"baseline_h{source_h}_{name}"
            already = _existing(run_dir, scenario_id, policy_id, split, None, record_hash, tape_hash)
            if already is not None:
                output_records.extend(already)
                continue
            started = time.monotonic()
            result = evaluate_baseline(record, tapes, scenario, horizon=500, burnin=500, return_trace=True)
            windows = from_trace(result["trace"], scenario)
            del result
            rows = write_windows(run_dir, scenario, policy_id, split, windows, family=name, repeat=None,
                       source_training_horizon=source_h, dataset_arrays_sha256=tape_hash,
                       record_sha256=record_hash, evaluation_seconds=time.monotonic()-started)
            output_records.extend(rows)
    completions = sorted((run_dir / "training" / scenario_id).glob("self_evolve_h*_r*/completed.json"))
    with FastPolicyWorker(tapes, scenario, burnin=500, horizon=500, timeout=180) as worker:
        for path in completions:
            completion = json.loads(path.read_text())
            if completion.get("status") not in {"complete", "completed"}:
                continue
            source_h = completion["source_training_horizon"]
            if not include_refits and source_h != 200:
                continue
            code_path = Path(completion["best_code_path"])
            if not code_path.is_absolute():
                code_path = path.parent / code_path
            code_path = code_path.resolve()
            code = code_path.read_text()
            code_hash = hashlib.sha256(code.encode()).hexdigest()
            if code_hash != completion["code_sha256"]:
                raise ValueError("Frozen policy hash changed")
            policy_id = completion["policy_id"]
            already = _existing(run_dir, scenario_id, policy_id, split, code_hash, None, tape_hash)
            if already is not None:
                output_records.extend(already)
                continue
            started = time.monotonic()
            answer = worker.evaluate_windows(code, WINDOWS)
            rows = write_windows(run_dir, scenario, policy_id, split, answer["windows"], family="self_evolve",
                       repeat=completion["repeat"], source_training_horizon=source_h,
                       dataset_arrays_sha256=tape_hash, code_sha256=code_hash,
                       full_protocol=completion["full_protocol"], evaluation_seconds=time.monotonic()-started)
            output_records.extend(rows)
    return output_records


def verify_primary_frozen(run_dir):
    """Seal all intended primary runs before any holdout policy scoring starts."""
    from .orchestrator import primary_jobs
    from .baselines import NAMES
    run_dir = Path(run_dir).resolve()
    missing, hashes = [], {}
    for job in primary_jobs():
        sid, rep = job["scenario_id"], job["repeat"]
        target = run_dir / "training" / sid / f"self_evolve_h200_r{rep}" / "completed.json"
        if not target.exists():
            missing.append(f"{sid}/r{rep}")
            continue
        record = json.loads(target.read_text())
        expected_id = f"self_evolve_h200_r{rep}"
        if (record.get("status") not in {"complete", "completed"} or not record.get("full_protocol")
                or record.get("scenario_id") != sid or record.get("repeat") != rep
                or record.get("source_training_horizon") != 200 or record.get("policy_id") != expected_id):
            missing.append(f"{sid}/r{rep}")
            continue
        code_path = Path(record["best_code_path"])
        if not code_path.is_absolute():
            code_path = target.parent / code_path
        code_path = code_path.resolve()
        if file_sha256(code_path) != record["code_sha256"]:
            raise ValueError("Selected policy file differs from training completion")
        hashes[str(code_path.relative_to(run_dir))] = file_sha256(code_path)
        hashes[str(target.relative_to(run_dir))] = file_sha256(target)
    for scenario in scenario_specs():
        target = run_dir / "baselines" / scenario.scenario_id / "h200" / "completed.json"
        if not target.exists():
            missing.append(scenario.scenario_id+"/baselines")
        else:
            completion = json.loads(target.read_text())
            record_path = target.with_name("records.json")
            records = json.loads(record_path.read_text())
            if (completion.get("status") != "complete" or completion.get("scenario_id") != scenario.scenario_id
                    or completion.get("source_training_horizon") != 200
                    or set(completion.get("families", [])) != set(NAMES) or set(records) != set(NAMES)):
                raise ValueError("Baseline set is incomplete or has mismatched metadata")
            for name, record in records.items():
                if (record["name"] != name or record["scenario"]["scenario_id"] != scenario.scenario_id
                        or record["training"]["horizon"] != 200 or record["training"]["burnin"] != 500
                        or record["training"]["n_paths"] != 50):
                    raise ValueError("Baseline training definition mismatch")
            hashes[str(target.relative_to(run_dir))] = file_sha256(target)
            hashes[str(record_path.relative_to(run_dir))] = file_sha256(record_path)
    if missing:
        raise RuntimeError("Primary policy set is not frozen: " + ", ".join(missing))
    target = run_dir / "primary_freeze.json"
    if target.exists():
        if json.loads(target.read_text())["completion_hashes"] != hashes:
            raise ValueError("Primary completion manifest changed after freeze")
    else:
        atomic_json(target, dict(completion_hashes=hashes, selection="train only", frozen_before_holdout=True))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", type=Path, default=DEFAULT_RUN)
    parser.add_argument("--scenario")
    parser.add_argument("--split", choices=["validation", "test"], default="test")
    args = parser.parse_args()
    if args.split == "test":
        verify_primary_frozen(args.run_dir)
    scenarios = [args.scenario] if args.scenario else [s.scenario_id for s in scenario_specs()]
    for sid in scenarios:
        records = evaluate_scenario(args.run_dir, sid, split=args.split)
        print(json.dumps(dict(scenario_id=sid, split=args.split, evaluated_rows=len(records))), flush=True)
