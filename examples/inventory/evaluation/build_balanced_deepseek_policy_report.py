#!/usr/bin/env python3
"""
Build a balanced 30-row report from DeepSeek no-optimizer prompt matches.

For each target table cell, select the closest prompt historical-policy cost
within the same distribution. The report maps those rows to the existing
15-iteration optimizer results and compares them with an optimized base-stock
baseline on the same distribution.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
import re
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = ROOT / "examples" / "inventory" / "evaluation" / "data"
OUT_DIR = ROOT / "examples" / "inventory" / "evaluation" / "deepseek_noopt_selected_optimizer"
UNIQUE_RESULTS_CSV = OUT_DIR / "policy_optimization_results.csv"
OPTIMIZED_JSONL = OUT_DIR / "optimized_policies.jsonl"
OUT_CSV = OUT_DIR / "balanced_10x3_policy_optimization_vs_basestock.csv"

N_TRAIN = 50
TABLE_COLUMNS = ["M", "W", "AG", "AQ", "BA", "BK", "BU", "CE", "CO", "CY"]
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


def load_prompt_candidates() -> dict[str, list[dict[str, Any]]]:
    candidates: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for prompt_path in sorted((ROOT / "examples").glob("**/deepseek*processed_no*/prompt_for_code/*.txt")):
        path_str = str(prompt_path)
        distribution = next((dist for dist in TARGETS if dist in path_str), None)
        if distribution is None:
            continue

        text = prompt_path.read_text(errors="ignore")
        section = text.split("Section 4 Historical Policy and Cost Statistics:")[-1]
        code = extract_section4_code(section)
        means = re.findall(r"mean\s*=\s*([0-9]+(?:\.[0-9]+)?)", section)
        if code is None or not means:
            continue

        code_hash = hashlib.sha1(code.encode("utf-8")).hexdigest()
        base_stock_matches = re.findall(r"base_stock\s*=\s*([0-9]+(?:\.[0-9]+)?)", code)
        candidates[distribution].append(
            {
                "distribution": distribution,
                "prompt_path": prompt_path.relative_to(ROOT).as_posix(),
                "prompt_mean_train_cost": round(float(means[-1]), 2),
                "code_hash": code_hash,
                "historical_base_stock": float(base_stock_matches[-1]) if base_stock_matches else None,
                "code": code,
            }
        )
    return candidates


def load_instances(distribution: str, split: str) -> list[dict[str, Any]]:
    instances = json.loads((DATA_DIR / f"{distribution}_{split}.json").read_text())
    return instances[:N_TRAIN] if split == "train" else instances


def evaluate_basestock(base_stock: float, instances: list[dict[str, Any]]) -> float:
    costs = []
    for inst in instances:
        lead_time = int(inst["lead_time"])
        demand = [0] * lead_time + list(inst["demand"])
        total_periods = lead_time + int(inst["num_periods"])
        current_inventory = float(inst["initial_inventory"])
        pipeline = [0.0] * lead_time
        total_cost = 0.0

        for t in range(total_periods):
            incoming = pipeline.pop(0) if lead_time > 0 else 0.0
            current_inventory += incoming
            outstanding = sum(pipeline)
            order_amount = max(0.0, float(base_stock) - current_inventory - outstanding)

            current_demand = float(demand[t])
            sales = min(current_inventory, current_demand)
            lost_sales = max(0.0, current_demand - sales)
            current_inventory -= sales

            if lead_time > 0:
                pipeline.append(order_amount)
            else:
                current_inventory += order_amount

            total_cost += float(inst["holding_cost"]) * current_inventory
            total_cost += float(inst["lost_sales_cost"]) * lost_sales
        costs.append(total_cost)
    return float(np.mean(costs))


def optimize_basestock_grid(instances: list[dict[str, Any]]) -> tuple[int, float]:
    best_s = 0
    best_avg = math.inf
    for s in range(0, 1001):
        avg = evaluate_basestock(s, instances)
        if avg < best_avg:
            best_s = s
            best_avg = avg
    return best_s, best_avg


def build_basestock_baselines() -> dict[str, dict[str, float]]:
    baselines: dict[str, dict[str, float]] = {}
    for distribution in TARGETS:
        train_instances = load_instances(distribution, "train")
        test_instances = load_instances(distribution, "test")
        train_s, train_avg = optimize_basestock_grid(train_instances)
        test_s, test_avg = optimize_basestock_grid(test_instances)
        baselines[distribution] = {
            "basestock_train_opt_s": train_s,
            "basestock_train_opt_train_avg": train_avg,
            "basestock_train_opt_test_avg": evaluate_basestock(train_s, test_instances),
            "basestock_test_oracle_s": test_s,
            "basestock_test_oracle_test_avg": test_avg,
        }
    return baselines


def choose_balanced_rows(candidates: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    rows = []
    for distribution, targets in TARGETS.items():
        used_prompts: set[str] = set()
        used_hashes: set[str] = set()
        dist_candidates = candidates[distribution]
        for column in TABLE_COLUMNS:
            target = targets[column]
            ranked = sorted(
                dist_candidates,
                key=lambda c: (
                    abs(c["prompt_mean_train_cost"] - target) / target,
                    c["code_hash"] in used_hashes,
                    c["prompt_path"] in used_prompts,
                    abs(c["prompt_mean_train_cost"] - target),
                    c["prompt_path"],
                ),
            )
            chosen = ranked[0]
            used_prompts.add(chosen["prompt_path"])
            used_hashes.add(chosen["code_hash"])
            row = dict(chosen)
            row["table_column"] = column
            row["target_cost"] = target
            row["match_abs_error"] = row["prompt_mean_train_cost"] - target
            row["match_abs_error_pct"] = row["match_abs_error"] / target
            rows.append(row)
    return rows


def main() -> int:
    candidates = load_prompt_candidates()
    selected = choose_balanced_rows(candidates)

    unique_by_hash: dict[tuple[str, str], dict[str, Any]] = {}
    with OPTIMIZED_JSONL.open() as fh:
        for line in fh:
            if not line.strip():
                continue
            record = json.loads(line)
            unique_by_hash[(record["distribution"], record["code_hash"])] = record
    baselines = build_basestock_baselines()

    out_rows = []
    for row in selected:
        key = (row["distribution"], row["code_hash"])
        if key not in unique_by_hash:
            raise KeyError(f"Missing optimizer result for {key}")
        opt = unique_by_hash[key]
        base = baselines[row["distribution"]]

        original_train = float(opt["original_train"]["avg"])
        optimized_train = float(opt["optimized_train"]["avg"])
        original_test = float(opt["original_test"]["avg"])
        optimized_test = float(opt["optimized_test"]["avg"])
        train_base = float(base["basestock_train_opt_train_avg"])
        test_base_train_tuned = float(base["basestock_train_opt_test_avg"])
        test_base_oracle = float(base["basestock_test_oracle_test_avg"])

        out_rows.append(
            {
                "distribution": row["distribution"],
                "table_column": row["table_column"],
                "target_cost": row["target_cost"],
                "matched_prompt_mean_train_cost": row["prompt_mean_train_cost"],
                "match_abs_error": row["match_abs_error"],
                "match_abs_error_pct": row["match_abs_error_pct"],
                "prompt_path": row["prompt_path"],
                "policy_id": opt["policy_id"],
                "code_hash": row["code_hash"],
                "historical_base_stock": row["historical_base_stock"],
                "optimizer_status": opt["status"],
                "optimizer_eval_count": opt["eval_count"],
                "original_train_avg": original_train,
                "optimized_train_avg": optimized_train,
                "train_improvement": original_train - optimized_train,
                "train_improvement_pct": (original_train - optimized_train) / original_train,
                "original_test_avg": original_test,
                "optimized_test_avg": optimized_test,
                "test_improvement": original_test - optimized_test,
                "test_improvement_pct": (original_test - optimized_test) / original_test,
                "basestock_train_opt_s": base["basestock_train_opt_s"],
                "basestock_train_opt_train_avg": train_base,
                "train_gap_vs_train_opt_basestock": optimized_train - train_base,
                "train_gap_pct_vs_train_opt_basestock": (optimized_train - train_base) / train_base,
                "basestock_train_opt_test_avg": test_base_train_tuned,
                "test_gap_vs_train_opt_basestock": optimized_test - test_base_train_tuned,
                "test_gap_pct_vs_train_opt_basestock": (optimized_test - test_base_train_tuned) / test_base_train_tuned,
                "basestock_test_oracle_s": base["basestock_test_oracle_s"],
                "basestock_test_oracle_test_avg": test_base_oracle,
                "test_gap_vs_test_oracle_basestock": optimized_test - test_base_oracle,
                "test_gap_pct_vs_test_oracle_basestock": (optimized_test - test_base_oracle) / test_base_oracle,
                "optimized_params": json.dumps(opt["optimized_params"], ensure_ascii=False),
            }
        )

    with OUT_CSV.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(out_rows[0].keys()))
        writer.writeheader()
        writer.writerows(out_rows)

    print(f"Wrote {OUT_CSV}")
    print(pd.DataFrame(out_rows).groupby("distribution").agg(
        rows=("table_column", "count"),
        unique_codes=("code_hash", "nunique"),
        avg_train_gap_vs_basestock=("train_gap_vs_train_opt_basestock", "mean"),
        avg_test_gap_vs_train_tuned_basestock=("test_gap_vs_train_opt_basestock", "mean"),
        best_optimized_test=("optimized_test_avg", "min"),
    ).to_string())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
