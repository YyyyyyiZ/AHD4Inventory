"""Generate the frozen dataset without consulting any policy outcome."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path

import numpy as np

from .api_client import atomic_json
from .data import generate_tapes, load_tapes, save_tapes, scenario_specs, tape_diagnostics
from .protocol import DEFAULT_RUN, PROTOCOL, file_sha256, freeze_protocol


def prepare(run_dir=DEFAULT_RUN):
    run_dir = Path(run_dir)
    freeze_protocol(run_dir)
    existing_path = run_dir / "dataset_manifest.json"
    if existing_path.exists():
        record = json.loads(existing_path.read_text())
        for item in record["files"]:
            if file_sha256(run_dir / item["path"]) != item["file_sha256"]:
                raise ValueError("Frozen dataset file changed: " + item["path"])
        return record
    files, diagnostics = [], []
    # Fixed/random lead-time comparisons share exactly the same demand tape.
    # Train, validation and test have disjoint SeedSequence-derived streams.
    demand_groups = [0, 1, 2, 3, 0, 3]
    for index, scenario in enumerate(scenario_specs()):
        for split_index, split in enumerate(PROTOCOL["splits"]):
            seed = int(np.random.SeedSequence([PROTOCOL["seed_root"], demand_groups[index], split_index]).generate_state(1, dtype=np.uint64)[0])
            n_paths = PROTOCOL[split + "_paths"]
            target = run_dir / "datasets" / scenario.scenario_id / (split + ".npz")
            if target.exists():
                tapes = load_tapes(target, scenario)
                if tapes["metadata"]["seed"] != seed or tapes["demands"].shape != (n_paths, PROTOCOL["tape_periods"]):
                    raise ValueError("Partial dataset metadata mismatch")
            else:
                tapes = generate_tapes(scenario, n_paths=n_paths, seed=seed, n_periods=PROTOCOL["tape_periods"])
                save_tapes(target, tapes)
            diagnostic = tape_diagnostics(tapes, scenario)
            diagnostics.append({"split": split, **diagnostic})
            files.append(dict(scenario_id=scenario.scenario_id, split=split,
                              path=str(target.relative_to(run_dir)), seed=seed, n_paths=n_paths,
                              n_periods=PROTOCOL["tape_periods"],
                              arrays_sha256=tapes["metadata"]["arrays_sha256"], file_sha256=file_sha256(target)))
    record = dict(created_utc=datetime.now(timezone.utc).isoformat(),
                  policy_outcomes_consulted=False,
                  shared_demand_comparisons=[["exp_iid_fixed6", "exp_iid_random3_9"],
                                            ["exp_regime095_fixed6", "exp_regime095_random3_9"]],
                  scenarios=[s.to_dict() for s in scenario_specs()], files=files)
    atomic_json(run_dir / "dataset_diagnostics.json", diagnostics)
    atomic_json(existing_path, record)
    lines = ["# Stationary autocorrelated inventory demand dataset", "",
             "The complete dataset was generated before any policy outcome was evaluated. "
             "Train, validation and test streams are disjoint; no scenario will be omitted because of its winner.", "",
             "## Files and use", "",
             "Each scenario has `train.npz` (50 paths), `validation.npz` (128), and `test.npz` (1000). "
             "Every path has 1000 periods plus one preceding observed demand. Fields: `demands`, `lead_times`, "
             "`initial_last_demand`, `metadata_json`. Load with `numpy.load(..., allow_pickle=False)`.", "",
             "For steady evaluations use demand periods 500:500+H, after simulating periods 0:500. "
             "For cold starts use 0:H from zero inventory and an empty pipeline. H is 50, 100, 200, or 500. "
             "Do not skip simulation of the burn-in. Use the same frozen rule across all H in the primary comparison.", "",
             "## Model", "",
             "All scenarios have the exact continuous Exponential(mean=100) stationary marginal. "
             "There is no integer rounding. Holding cost is 1 and lost-sales cost is 2 per unit per period.", "",
             "- iid: Gaussian latent correlation zero.",
             "- AR+: Z starts N(0,1), Z_t=0.8 Z_(t-1)+sqrt(1-0.8²) epsilon_t; D_t=-100 log(1-Phi(Z_t)).",
             "- AR−: same construction with latent rho=-0.6.",
             "- regime: stationary equally likely low/high state, stay probability 0.95; U_t=(S_t+V_t)/2, V iid Uniform(0,1), D_t=-100 log(1-U_t).",
             "- Fixed lead is 6; random lead is 3 or 9 with equal probability, independent by calendar period and independent of demand.", "",
             "Latent rho is not Pearson demand correlation. The regime construction has demand ACF(k)=ln(2)²×0.9^k. "
             "Demand is stationary from the initial observation, without a zero-state transient. "
             "Fixed/random lead variants share identical demand paths, isolating the lead-time change.", "",
             "## Information and timing", "",
             "Receive old orders; observe current lead quotation; place current order; realize demand; charge ending-inventory holding and lost-sales costs. "
             "Current quotation is known before ordering. Orders may overtake; existing pipeline buckets contain amounts due in 1,...,maxLead−1 periods. "
             "All methods observe the complete preceding demand, including unmet demand, and know the generator parameters. "
             "They never see current/future demand or future lead quotations. There is no policy clock or horizon input.", "",
             "## Training-set diagnostics", "",
             "| Scenario | Mean | SD | Demand lag-1 ACF | Demand lag-5 ACF |", "|---|---:|---:|---:|---:|"]
    for row in diagnostics:
        if row["split"] == "train":
            lines.append(f"| {row['scenario_id']} | {row['marginal_mean']:.2f} | {row['marginal_std']:.2f} | {row['acf_demand']['1']:.3f} | {row['acf_demand']['5']:.3f} |")
    lines += ["", "Array hashes and file hashes are recorded in `dataset_manifest.json`; all split diagnostics are in `dataset_diagnostics.json`. "
              "Diagnostics are descriptive generator checks, never a filter based on policy performance.", ""]
    (run_dir / "DATASET.md").write_text("\n".join(lines))
    return record


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", type=Path, default=DEFAULT_RUN)
    args = parser.parse_args()
    result = prepare(args.run_dir)
    print(json.dumps({"dataset_files": len(result["files"]), "run_dir": str(args.run_dir)}))
