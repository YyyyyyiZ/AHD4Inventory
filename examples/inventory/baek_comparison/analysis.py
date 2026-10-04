"""Paired statistical reports and train-only historical policy selection."""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
import re

import numpy as np


def _costs(values, label):
    if hasattr(values, "total_cost"):
        values = values.total_cost
    raw = np.asarray(values)
    if np.iscomplexobj(raw):
        raise ValueError(f"{label} must be real")
    array = np.asarray(raw, dtype=float)
    if array.ndim != 1 or not len(array) or not np.isfinite(array).all():
        raise ValueError(f"{label} must be a nonempty finite 1-D array")
    if (array < 0).any():
        raise ValueError(f"{label} cannot contain negative costs")
    return array


def paired_statistics(candidate, reference, *, seed=20260915, n_bootstrap=5000,
                      confidence=0.95) -> dict:
    """Bootstrap matched demand paths; positive improvement favors candidate.

    The interval resamples trajectories, not individual periods or generated
    policies. Generation variability must be reported separately. Caller must
    ensure corresponding entries were scored on the exact same demand paths.
    """
    cand, ref = _costs(candidate, "candidate"), _costs(reference, "reference")
    if cand.shape != ref.shape:
        raise ValueError("Paired trajectories must have the same shape")
    if not isinstance(n_bootstrap, int) or isinstance(n_bootstrap, bool) or n_bootstrap < 1:
        raise ValueError("n_bootstrap must be a positive integer")
    if not 0.0 < confidence < 1.0:
        raise ValueError("confidence must lie strictly between 0 and 1")
    delta = cand - ref
    rng = np.random.default_rng(seed)
    boot_delta, boot_pct = [], []
    for start in range(0, n_bootstrap, 128):
        indices = rng.integers(len(cand), size=(min(128, n_bootstrap - start), len(cand)))
        d = delta[indices].mean(axis=1)
        r = ref[indices].mean(axis=1)
        boot_delta.extend(d.tolist())
        boot_pct.extend(np.divide(-100.0 * d, r, out=np.full_like(d, np.nan),
                                  where=r > 0).tolist())
    quantiles = [(1.0 - confidence) / 2, (1.0 + confidence) / 2]
    lo, hi = map(float, np.quantile(boot_delta, quantiles))
    valid_pct = np.asarray(boot_pct)
    valid_pct = valid_pct[np.isfinite(valid_pct)]
    pct_ci = list(map(float, np.quantile(valid_pct, quantiles))) if len(valid_pct) == n_bootstrap else None
    cand_mean, ref_mean = float(cand.mean()), float(ref.mean())
    return {
        "n_paths": len(cand), "candidate_mean_cost": cand_mean,
        "reference_mean_cost": ref_mean, "mean_cost_difference": float(delta.mean()),
        "cost_difference_ci": [lo, hi],
        "improvement_pct": 100.0 * (ref_mean - cand_mean) / ref_mean if ref_mean > 0 else None,
        "improvement_pct_ci": pct_ci, "confidence": confidence,
        "bootstrap_seed": int(seed), "bootstrap_replicates": n_bootstrap,
        "significant_outcome": "win" if hi < 0 else "loss" if lo > 0 else "inconclusive",
        "sign_convention": "candidate_minus_reference; negative difference favors candidate",
        "uncertainty_scope": "paired demand-path sampling, excluding generation variation",
    }


def summarize_simulation(result) -> dict:
    """Cost decomposition and fill rates from one frozen policy evaluation."""
    if hasattr(result, "summary"):
        return result.summary()
    raise TypeError("Expected environment.SimulationResult")


def summarize_repeats(records: list[dict]) -> dict:
    """Report every generated draw without choosing the best test score.

    Input records have repeat_id, ok, mean_total_cost and optionally attempt,
    error, metadata. A retry is part of its original draw, not a new repeat.
    Records must be supplied in generation order; first valid per repeat is kept.
    """
    groups = {}
    for record in records:
        if "repeat_id" not in record:
            raise ValueError("Each generation record needs repeat_id")
        groups.setdefault(str(record["repeat_id"]), []).append(record)
    rows = []
    for repeat_id, attempts in groups.items():
        valid = [record for record in attempts if record.get("ok")]
        chosen = valid[0] if valid else None
        cost = chosen.get("mean_total_cost") if chosen else None
        if chosen and (not isinstance(cost, (int, float)) or not math.isfinite(cost) or cost < 0):
            raise ValueError("A valid repeat requires finite nonnegative mean_total_cost")
        rows.append({"repeat_id": repeat_id, "ok": bool(chosen),
                     "first_attempt_ok": bool(attempts[0].get("ok")),
                     "attempts": len(attempts), "mean_total_cost": cost,
                     "selected_attempt": attempts.index(chosen) + 1 if chosen else None,
                     "errors": [r.get("error") for r in attempts if not r.get("ok")]})
    costs = [row["mean_total_cost"] for row in rows if row["ok"]]
    return {"repeats": rows, "n_planned_repeats": len(rows), "n_valid_repeats": len(costs),
            "first_attempt_success_rate": sum(row["first_attempt_ok"] for row in rows) / len(rows) if rows else None,
            "final_failure_rate": 1.0 - len(costs) / len(rows) if rows else None,
            "mean_across_repeats": float(np.mean(costs)) if costs else None,
            "sd_across_repeats": float(np.std(costs, ddof=1)) if len(costs) > 1 else None,
            "min_across_repeats": min(costs) if costs else None,
            "max_across_repeats": max(costs) if costs else None,
            "selection_rule": "first_valid_attempt_per_repeat; no test-based selection"}


_SCENARIO_RE = re.compile(r"(?P<scenario>(?:poisson|exponential|normal_std\d+)_L\d+_c\d+_\d+)")
_RUN_RE = re.compile(r"_50_plain_processed_scipy_15_default_m2_(?P<width>\d+)_r(?P<repeat>\d+)$")


def historical_policy_inventory(inventory_dir: Path | str, *, include_code=True) -> dict:
    """Inspect generation-10 m2/SciPy populations; never execute saved code.

    Scope is fixed by path naming before scores are inspected. Exclude old
    directories and m2plural. Select a training-best candidate within each run;
    retain model/run identities. A scenario-best choice across available runs is
    separately labeled a heterogeneous historical reference, not one AHD model.
    Test scores and test trajectories are neither selected nor returned.
    """
    root = Path(inventory_dir).resolve()
    runs, errors = [], []
    for path in sorted(root.rglob("population_generation_10.json")):
        relative = path.relative_to(root)
        if path.parent.name != "pops" or any("old" in part.lower() for part in relative.parts):
            continue
        run_name = path.parent.parent.name
        settings = _RUN_RE.search(run_name)
        scenario = _SCENARIO_RE.search(run_name)
        if not settings or not scenario:
            continue
        try:
            raw = path.read_bytes()
            records = json.loads(raw)
            if not isinstance(records, list):
                raise ValueError("population is not a list")
            candidates = []
            for index, record in enumerate(records):
                if not isinstance(record, dict):
                    continue
                objective, code = record.get("objective"), record.get("code")
                if (isinstance(objective, (int, float)) and not isinstance(objective, bool)
                        and math.isfinite(objective) and objective >= 0
                        and isinstance(code, str) and code.strip()):
                    candidates.append((float(objective), index, code, record))
            if not candidates:
                raise ValueError("no candidate with finite training objective and code")
            objective, index, code, selected = min(candidates, key=lambda item: (item[0], item[1]))
            model_suffix = run_name[:scenario.start()].rstrip("_")
            provider_parts = relative.parts[:-3]
            model = "/".join((*provider_parts, model_suffix))
            row = {
                "scenario_id": scenario.group("scenario"), "model": model,
                "run_name": run_name, "run_path": str(path.parent.parent),
                "population_path": str(path), "population_sha256": hashlib.sha256(raw).hexdigest(),
                "candidate_index": index, "candidate_code_sha256": hashlib.sha256(code.encode()).hexdigest(),
                "recorded_train_objective": objective, "valid_candidates": len(candidates),
                "generation": 10, "search_width": int(settings.group("width")),
                "historical_repeat": int(settings.group("repeat")),
                "selection_rule": "minimum_recorded_training_objective_in_generation_10",
                "recorded_opt_params": selected.get("opt_params"),
                "requires_execution_audit": True,
            }
            if include_code:
                row["code"] = code
            runs.append(row)
        except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
            errors.append({"population_path": str(path), "error": str(exc)})
    by_scenario = {}
    for row in runs:
        previous = by_scenario.get(row["scenario_id"])
        if previous is None or (row["recorded_train_objective"], row["population_path"]) < (
                previous["recorded_train_objective"], previous["population_path"]):
            by_scenario[row["scenario_id"]] = row
    return {
        "scope": "non-old generation-10 pops; 50_plain_processed_scipy_15_default_m2 runs",
        "runs": runs, "scenario_train_best": by_scenario,
        "reference_label": "historical best available by recorded training score; heterogeneous models and budgets",
        "scenario_count": len(by_scenario), "run_count": len(runs), "errors": errors,
        "test_scores_used": False,
    }
