#!/usr/bin/env python3
"""
Optimize DeepSeek no-optimizer policies selected from prompt_for_code files.

Selection rule:
- DeepSeek paths containing processed_no
- distribution in TARGETS
- Section 4 historical-policy mean within TOL of at least one target table cost

The optimizer tunes OPT_PARAM annotations for 15 L-BFGS-B iterations on the train
instances and then evaluates the optimized code on train and test instances.
"""

from __future__ import annotations

import ast
import csv
import hashlib
import json
import math
import re
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np
from scipy.optimize import minimize


ROOT = Path(__file__).resolve().parents[3]
INVENTORY_DIR = ROOT / "examples" / "inventory"
DATA_DIR = INVENTORY_DIR / "evaluation" / "data"
OUT_DIR = INVENTORY_DIR / "evaluation" / "deepseek_noopt_selected_optimizer"

TOL = 0.03
MAXITER = 15
N_TRAIN = 50
EPS = 0.1

TARGETS: dict[str, dict[str, float]] = {
    "normal_std30_L6_c1_2": {
        "M": 3250.30,
        "W": 4193.86,
        "AG": 4195.74,
        "AQ": 4196.04,
        "BA": 4368.66,
        "BK": 4284.40,
        "BU": 4224.24,
        "CE": 4195.74,
        "CO": 4193.86,
        "CY": 4196.04,
    },
    "poisson_L6_c1_2": {
        "M": 2815.20,
        "W": 2815.20,
        "AG": 2815.20,
        "AQ": 2790.72,
        "BA": 2815.20,
        "BK": 2790.72,
        "BU": 2784.74,
        "CE": 2815.20,
        "CO": 2815.20,
        "CY": 2815.20,
    },
    "exponential_L6_c1_2": {
        "M": 7242.76,
        "W": 7242.76,
        "AG": 7242.76,
        "AQ": 6854.22,
        "BA": 7243.28,
        "BK": 7242.44,
        "BU": 7242.76,
        "CE": 7242.76,
        "CO": 7242.76,
        "CY": 7242.76,
    },
}


@dataclass
class SelectedPolicy:
    policy_id: str
    distribution: str
    code_hash: str
    code: str
    prompt_paths: set[str] = field(default_factory=set)
    prompt_means: set[float] = field(default_factory=set)
    matched_cells: set[str] = field(default_factory=set)
    historical_base_stock: float | None = None


def extract_section4_code(section: str) -> str | None:
    match = re.search(
        r"I have one policy with its code as follows:\n(?P<code>.*?)(?:\n\s*Below is the cost statistics|\Z)",
        section,
        re.S,
    )
    if not match:
        return None
    code = match.group("code").strip("\n")
    return code or None


def parse_prompt(prompt_path: Path) -> tuple[str, float, str] | None:
    path_str = str(prompt_path)
    distribution = next((dist for dist in TARGETS if dist in path_str), None)
    if distribution is None:
        return None

    text = prompt_path.read_text(errors="ignore")
    section = text.split("Section 4 Historical Policy and Cost Statistics:")[-1]
    code = extract_section4_code(section)
    means = re.findall(r"mean\s*=\s*([0-9]+(?:\.[0-9]+)?)", section)
    if code is None or not means:
        return None

    return distribution, round(float(means[-1]), 2), code


def find_selected_policies() -> list[SelectedPolicy]:
    policies: dict[tuple[str, str], SelectedPolicy] = {}

    for prompt_path in sorted((ROOT / "examples").glob("**/deepseek*processed_no*/prompt_for_code/*.txt")):
        parsed = parse_prompt(prompt_path)
        if parsed is None:
            continue
        distribution, prompt_mean, code = parsed

        matched_cells = [
            col
            for col, target in TARGETS[distribution].items()
            if abs(prompt_mean - target) / target <= TOL
        ]
        if not matched_cells:
            continue

        code_hash = hashlib.sha1(code.encode("utf-8")).hexdigest()
        key = (distribution, code_hash)
        if key not in policies:
            base_stock_matches = re.findall(r"base_stock\s*=\s*([0-9]+(?:\.[0-9]+)?)", code)
            policies[key] = SelectedPolicy(
                policy_id=f"{distribution}__{len(policies) + 1:03d}__{code_hash[:10]}",
                distribution=distribution,
                code_hash=code_hash,
                code=code,
                historical_base_stock=float(base_stock_matches[-1]) if base_stock_matches else None,
            )

        policy = policies[key]
        policy.prompt_paths.add(str(prompt_path.relative_to(ROOT)))
        policy.prompt_means.add(prompt_mean)
        for col in matched_cells:
            policy.matched_cells.add(col)

    return sorted(policies.values(), key=lambda p: (p.distribution, p.policy_id))


def parse_opt_params(code: str) -> dict[str, dict[str, Any]]:
    opt_params: dict[str, dict[str, Any]] = {}
    for line in code.splitlines():
        if "OPT_PARAM:" not in line:
            continue

        name_match = re.match(r"^\s*([A-Za-z_]\w*)\s*=", line)
        if not name_match:
            continue

        raw = line.split("OPT_PARAM:", 1)[1].strip()
        try:
            cfg = ast.literal_eval(raw)
        except Exception:
            try:
                cfg = json.loads(raw.replace("'", '"'))
            except Exception:
                continue

        if not isinstance(cfg, dict):
            continue
        if not {"initial", "min", "max"}.issubset(cfg):
            continue
        cfg.setdefault("type", "float")
        opt_params[name_match.group(1)] = cfg

    return opt_params


def coerce_params(raw_params: dict[str, float], opt_params: dict[str, dict[str, Any]]) -> dict[str, float | int]:
    coerced: dict[str, float | int] = {}
    for name, value in raw_params.items():
        cfg = opt_params[name]
        bounded = min(max(float(value), float(cfg["min"])), float(cfg["max"]))
        if cfg.get("type") == "int":
            coerced[name] = int(round(bounded))
        else:
            coerced[name] = float(bounded)
    return coerced


def replace_params(code: str, params: dict[str, float | int], opt_params: dict[str, dict[str, Any]]) -> str:
    lines = code.splitlines()
    for idx, line in enumerate(lines):
        if "OPT_PARAM:" not in line:
            continue
        name_match = re.match(r"^(?P<indent>\s*)(?P<name>[A-Za-z_]\w*)\s*=", line)
        if not name_match:
            continue
        name = name_match.group("name")
        if name not in params:
            continue
        cfg = dict(opt_params[name])
        cfg["initial"] = params[name]
        lines[idx] = f"{name_match.group('indent')}{name} = {params[name]}  # OPT_PARAM: {json.dumps(cfg)}"
    return "\n".join(lines)


def load_instances(distribution: str, split: str) -> list[dict[str, Any]]:
    path = DATA_DIR / f"{distribution}_{split}.json"
    instances = json.loads(path.read_text())
    if split == "train":
        instances = instances[:N_TRAIN]
    return instances


def build_policy_fn(code: str):
    namespace: dict[str, Any] = {"__builtins__": __builtins__}
    exec(code, namespace)
    fn = namespace.get("compute_order_amount")
    if not callable(fn):
        raise ValueError("compute_order_amount not found")
    return fn


def evaluate_code(code: str, instances: list[dict[str, Any]]) -> dict[str, Any]:
    fn = build_policy_fn(code)
    trajectories: list[float] = []

    for inst in instances:
        lead_time = int(inst["lead_time"])
        demand = [0] * lead_time + list(inst["demand"])
        total_periods = lead_time + int(inst["num_periods"])
        holding_cost = float(inst["holding_cost"])
        lost_sales_cost = float(inst["lost_sales_cost"])

        current_inventory = float(inst["initial_inventory"])
        pipeline = [0.0] * lead_time
        total_cost = 0.0

        for t in range(total_periods):
            incoming = pipeline.pop(0) if lead_time > 0 else 0.0
            current_inventory += incoming

            order_amount = fn(
                on_hand_inventory=current_inventory,
                pipeline_orders=pipeline.copy(),
            )
            order_amount = float(order_amount)
            if not math.isfinite(order_amount):
                raise ValueError("non-finite order amount")

            current_demand = float(demand[t])
            sales = min(current_inventory, current_demand)
            lost_sales = max(0.0, current_demand - sales)
            current_inventory -= sales

            if lead_time > 0:
                pipeline.append(order_amount)
            else:
                current_inventory += order_amount

            total_cost += holding_cost * current_inventory + lost_sales_cost * lost_sales

        trajectories.append(float(total_cost))

    return {"avg": float(np.mean(trajectories)), "trajectory": trajectories}


def optimize_policy(policy: SelectedPolicy, train_instances: list[dict[str, Any]], test_instances: list[dict[str, Any]]):
    opt_params = parse_opt_params(policy.code)
    original_train = evaluate_code(policy.code, train_instances)
    original_test = evaluate_code(policy.code, test_instances)

    if not opt_params:
        return {
            "status": "no_params",
            "optimized_code": policy.code,
            "optimized_params": {},
            "eval_count": 0,
            "original_train": original_train,
            "original_test": original_test,
            "optimized_train": original_train,
            "optimized_test": original_test,
        }

    param_names = list(opt_params)
    initial = [float(opt_params[name]["initial"]) for name in param_names]
    bounds = [(float(opt_params[name]["min"]), float(opt_params[name]["max"])) for name in param_names]
    history: list[dict[str, Any]] = []

    def objective(x):
        raw_params = dict(zip(param_names, x))
        params = coerce_params(raw_params, opt_params)
        tuned_code = replace_params(policy.code, params, opt_params)
        train_result = evaluate_code(tuned_code, train_instances)
        history.append(
            {
                "params": params,
                "train_avg": train_result["avg"],
                "code": tuned_code,
                "train_trajectory": train_result["trajectory"],
            }
        )
        return train_result["avg"]

    status = "ok"
    message = ""
    started = time.time()
    try:
        result = minimize(
            objective,
            initial,
            bounds=bounds,
            method="L-BFGS-B",
            options={"maxiter": MAXITER, "eps": EPS, "ftol": 1e-6, "gtol": 1e-4},
        )
        message = str(result.message)
        if not result.success:
            status = "partial"
    except Exception as exc:
        status = "failed_with_partial" if history else "failed"
        message = repr(exc)

    if history:
        best = min(history, key=lambda item: item["train_avg"])
        optimized_code = best["code"]
        optimized_params = best["params"]
        optimized_train = {"avg": best["train_avg"], "trajectory": best["train_trajectory"]}
        optimized_test = evaluate_code(optimized_code, test_instances)
    else:
        optimized_code = policy.code
        optimized_params = {}
        optimized_train = original_train
        optimized_test = original_test

    return {
        "status": status,
        "message": message,
        "elapsed_sec": round(time.time() - started, 4),
        "optimized_code": optimized_code,
        "optimized_params": optimized_params,
        "eval_count": len(history),
        "original_train": original_train,
        "original_test": original_test,
        "optimized_train": optimized_train,
        "optimized_test": optimized_test,
    }


def json_ready(policy: SelectedPolicy, result: dict[str, Any]) -> dict[str, Any]:
    return {
        "policy_id": policy.policy_id,
        "distribution": policy.distribution,
        "code_hash": policy.code_hash,
        "historical_base_stock": policy.historical_base_stock,
        "prompt_count": len(policy.prompt_paths),
        "prompt_means": sorted(policy.prompt_means),
        "matched_cells": sorted(policy.matched_cells),
        "prompt_paths": sorted(policy.prompt_paths),
        **result,
    }


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows = []
    for line in path.read_text().splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def write_final_outputs(records: list[dict[str, Any]]) -> None:
    oracle_by_dist: dict[str, dict[str, float]] = {}
    summary_rows = []

    for distribution in TARGETS:
        dist_records = [r for r in records if r["distribution"] == distribution]
        if not dist_records:
            continue

        opt_train_stack = np.array([r["optimized_train"]["trajectory"] for r in dist_records], dtype=float)
        opt_test_stack = np.array([r["optimized_test"]["trajectory"] for r in dist_records], dtype=float)
        orig_train_avgs = [r["original_train"]["avg"] for r in dist_records]
        orig_test_avgs = [r["original_test"]["avg"] for r in dist_records]
        opt_train_avgs = [r["optimized_train"]["avg"] for r in dist_records]
        opt_test_avgs = [r["optimized_test"]["avg"] for r in dist_records]

        oracle_train = float(np.mean(np.min(opt_train_stack, axis=0)))
        oracle_test = float(np.mean(np.min(opt_test_stack, axis=0)))
        oracle_by_dist[distribution] = {
            "oracle_train_avg": oracle_train,
            "oracle_test_avg": oracle_test,
            "train_instances": int(opt_train_stack.shape[1]),
            "test_instances": int(opt_test_stack.shape[1]),
        }

        best_opt_test_record = min(dist_records, key=lambda r: r["optimized_test"]["avg"])
        summary_rows.append(
            {
                "distribution": distribution,
                "n_unique_policies": len(dist_records),
                "best_original_train_avg": min(orig_train_avgs),
                "best_original_test_avg": min(orig_test_avgs),
                "best_optimized_train_avg": min(opt_train_avgs),
                "best_optimized_test_avg": min(opt_test_avgs),
                "instancewise_best_optimized_train_avg": oracle_train,
                "instancewise_best_optimized_test_avg": oracle_test,
                "best_single_opt_test_gap_to_instancewise": best_opt_test_record["optimized_test"]["avg"] - oracle_test,
                "best_single_opt_test_gap_pct": (
                    (best_opt_test_record["optimized_test"]["avg"] - oracle_test) / oracle_test
                    if oracle_test
                    else float("nan")
                ),
                "best_optimized_test_policy_id": best_opt_test_record["policy_id"],
                "median_policy_opt_test_gap_to_instancewise": float(
                    np.median([avg - oracle_test for avg in opt_test_avgs])
                ),
            }
        )

    detailed_rows = []
    for record in records:
        oracle = oracle_by_dist[record["distribution"]]
        detailed_rows.append(
            {
                "policy_id": record["policy_id"],
                "distribution": record["distribution"],
                "historical_base_stock": record["historical_base_stock"],
                "prompt_count": record["prompt_count"],
                "prompt_means": ";".join(f"{x:.2f}" for x in record["prompt_means"]),
                "matched_cells": ";".join(record["matched_cells"]),
                "status": record["status"],
                "eval_count": record["eval_count"],
                "elapsed_sec": record.get("elapsed_sec", ""),
                "original_train_avg": record["original_train"]["avg"],
                "optimized_train_avg": record["optimized_train"]["avg"],
                "train_improvement": record["original_train"]["avg"] - record["optimized_train"]["avg"],
                "train_improvement_pct": (
                    (record["original_train"]["avg"] - record["optimized_train"]["avg"]) / record["original_train"]["avg"]
                    if record["original_train"]["avg"]
                    else float("nan")
                ),
                "original_test_avg": record["original_test"]["avg"],
                "optimized_test_avg": record["optimized_test"]["avg"],
                "test_improvement": record["original_test"]["avg"] - record["optimized_test"]["avg"],
                "test_improvement_pct": (
                    (record["original_test"]["avg"] - record["optimized_test"]["avg"]) / record["original_test"]["avg"]
                    if record["original_test"]["avg"]
                    else float("nan")
                ),
                "instancewise_best_optimized_train_avg": oracle["oracle_train_avg"],
                "opt_train_gap_to_instancewise": record["optimized_train"]["avg"] - oracle["oracle_train_avg"],
                "opt_train_gap_to_instancewise_pct": (
                    (record["optimized_train"]["avg"] - oracle["oracle_train_avg"]) / oracle["oracle_train_avg"]
                    if oracle["oracle_train_avg"]
                    else float("nan")
                ),
                "instancewise_best_optimized_test_avg": oracle["oracle_test_avg"],
                "opt_test_gap_to_instancewise": record["optimized_test"]["avg"] - oracle["oracle_test_avg"],
                "opt_test_gap_to_instancewise_pct": (
                    (record["optimized_test"]["avg"] - oracle["oracle_test_avg"]) / oracle["oracle_test_avg"]
                    if oracle["oracle_test_avg"]
                    else float("nan")
                ),
                "optimized_params": json.dumps(record["optimized_params"], ensure_ascii=False),
                "sample_prompt_path": record["prompt_paths"][0] if record["prompt_paths"] else "",
            }
        )

    detailed_path = OUT_DIR / "policy_optimization_results.csv"
    with detailed_path.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(detailed_rows[0].keys()))
        writer.writeheader()
        writer.writerows(detailed_rows)

    summary_path = OUT_DIR / "distribution_summary.csv"
    with summary_path.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(summary_rows[0].keys()))
        writer.writeheader()
        writer.writerows(summary_rows)

    (OUT_DIR / "instancewise_best_policy_summary.json").write_text(
        json.dumps(oracle_by_dist, indent=2, ensure_ascii=False)
    )


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    jsonl_path = OUT_DIR / "optimized_policies.jsonl"

    policies = find_selected_policies()
    print(f"Selected {len(policies)} unique distribution+code policies")

    existing = {row["policy_id"]: row for row in load_jsonl(jsonl_path)}
    completed = set(existing)
    with jsonl_path.open("a") as out:
        for idx, policy in enumerate(policies, start=1):
            if policy.policy_id in completed:
                print(f"[{idx}/{len(policies)}] skip {policy.policy_id}")
                continue

            train_instances = load_instances(policy.distribution, "train")
            test_instances = load_instances(policy.distribution, "test")
            print(
                f"[{idx}/{len(policies)}] optimize {policy.policy_id} "
                f"base_stock={policy.historical_base_stock} prompts={len(policy.prompt_paths)}"
            )
            result = optimize_policy(policy, train_instances, test_instances)
            record = json_ready(policy, result)
            out.write(json.dumps(record, ensure_ascii=False) + "\n")
            out.flush()

    records = load_jsonl(jsonl_path)
    expected_ids = {p.policy_id for p in policies}
    records = [r for r in records if r["policy_id"] in expected_ids]
    if len(records) != len(expected_ids):
        missing = sorted(expected_ids - {r["policy_id"] for r in records})
        print(f"Missing {len(missing)} records; rerun to resume.", file=sys.stderr)
        return 1

    write_final_outputs(records)
    print(f"Done. Outputs written to {OUT_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
