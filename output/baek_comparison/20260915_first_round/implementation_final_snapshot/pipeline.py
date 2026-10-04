"""Frozen baseline construction and paired scoring, separate from generation."""
from __future__ import annotations

import argparse
from dataclasses import asdict
import json
from pathlib import Path
import sys

import numpy as np

from .analysis import historical_policy_inventory, paired_statistics
from .baselines import fit_baselines, evaluate_classical, make_policy
from .environment import CORE_SCENARIO_IDS, discover_scenarios, load_demands, sample_demands, simulate_policy
from .runner import DEFAULT_RUN, REPO, atomic_json, sha256


def build_baselines(run_dir: Path):
    inventory = historical_policy_inventory(REPO / "examples/inventory", include_code=True)
    atomic_json(run_dir / "historical_inventory.json", inventory)
    for scenario in discover_scenarios():
        path = run_dir / "baselines" / f"{scenario.scenario_id}.json"
        if path.exists():
            continue
        train = load_demands(scenario, "train", n_paths=50)
        fits = fit_baselines(train, scenario, n_train=50)
        atomic_json(path, {"scenario": asdict(scenario), "fits": fits})
        print(json.dumps({"event": "baselines_frozen", "scenario": scenario.scenario_id}), flush=True)


def result_dict(result):
    return {"status": "ok", "summary": result.summary(),
            "per_path": {field: getattr(result, field).tolist() for field in (
                "total_cost", "holding_cost", "lost_sales_cost", "demand_units", "sales_units", "lost_units")}}


def scenario_batches(scenario, index, manifest):
    current = load_demands(scenario, "test")
    fresh = sample_demands(scenario, manifest["fresh_test_paths"], seed=manifest["seed_fresh_test"] + index)
    batches = [
        {"name": "existing_test", "demands": current},
        {"name": "fresh_test", "demands": fresh},
        {"name": "integer_test", "demands": current, "integer_orders": True},
    ]
    if scenario.scenario_id in CORE_SCENARIO_IDS:
        long = sample_demands(scenario, manifest["long_run_paths"],
            seed=manifest["seed_long_run"] + index, horizon=manifest["long_run_periods"])
        batches.append({"name": "long_run", "demands": long, "mode": "long_run",
                        "burn_in": manifest["long_run_burn_in"]})
    return batches


def score_classical(run_dir: Path, *, only: str | None = None):
    manifest = json.loads((run_dir / "manifest.json").read_text())
    for index, scenario in enumerate(discover_scenarios()):
        if only and scenario.scenario_id != only:
            continue
        fit_record = json.loads((run_dir / "baselines" / f"{scenario.scenario_id}.json").read_text())
        batches = scenario_batches(scenario, index, manifest)
        for name, fit in fit_record["fits"].items():
            path = run_dir / "scores" / scenario.scenario_id / f"classical_{name}.json"
            if path.exists():
                continue
            values = {}
            for batch in batches:
                if batch.get("mode") == "long_run":
                    result = simulate_policy(make_policy(name, fit["params"]), scenario, batch["demands"],
                        mode="long_run", burn_in=batch["burn_in"])
                else:
                    result = evaluate_classical(name, fit["params"], batch["demands"], scenario,
                        integer_orders=batch.get("integer_orders", False))
                values[batch["name"]] = result_dict(result)
                values[batch["name"]]["demand_sha256"] = sha256(
                    np.ascontiguousarray(batch["demands"], dtype="<f8").tobytes())
            atomic_json(path, {"method": name, "source": "training_tuned_classical", "scenario_id": scenario.scenario_id,
                               "fit": fit, "batches": values})
        print(json.dumps({"event": "classical_scored", "scenario": scenario.scenario_id}), flush=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("baselines", "score-classical"))
    parser.add_argument("--run-dir", type=Path, default=DEFAULT_RUN)
    parser.add_argument("--only")
    args = parser.parse_args()
    if args.action == "baselines":
        build_baselines(args.run_dir)
    else:
        score_classical(args.run_dir, only=args.only)


if __name__ == "__main__":
    main()
