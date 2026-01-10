#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Compute 2-period newsvendor lower bound with lead-time padding, and output ONE row per JSON file:
- For each trajectory (instance) in the JSON list:
    demand_ext = [0]*L + demand
    T = len(demand_ext) = 50 + L
  Partition into non-overlapping 2-period blocks:
    D2_b = demand_ext[2b] + demand_ext[2b+1]
  Newsvendor:
    q = p/(p+h)
    S* = empirical q-quantile of {D2_b}
    cost per block = h*(S*-D2_b)^+ + p*(D2_b-S*)^+
    total LB for this trajectory over T periods = sum over blocks (and handle leftover period if T is odd)
- For each JSON file: take mean over trajectories; write one CSV row.

Assumption: lost sales penalty (no backorder), per-unit holding cost h, per-unit lost sales penalty p.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any, Dict, List, Tuple

import numpy as np


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--output_csv", type=str, default="lb_2period.csv",
                   help="Output CSV filename (saved in the same directory as this script).")
    p.add_argument("--recursive", action="store_true", default=True,
                   help="Recursively scan the script directory for *.json (default True).")
    # Quantile method: numpy supports different methods depending on version; we use a robust fallback.
    p.add_argument("--quantile_method", type=str, default="linear",
                   help="Quantile interpolation/method passed to numpy (if supported). "
                        "Common: linear, higher, lower, midpoint, nearest. Default linear.")
    return p.parse_args()


def scan_json_files(root_dir: Path, recursive: bool) -> List[Path]:
    if recursive:
        return sorted([p for p in root_dir.rglob("*.json") if p.is_file()])
    return sorted([p for p in root_dir.glob("*.json") if p.is_file()])


def load_instances(path: Path) -> List[Dict[str, Any]]:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError(f"{path} must contain a list of instances.")
    return data


def critical_fractile(h: float, p: float) -> float:
    denom = h + p
    if denom <= 0:
        return 0.5
    return float(p / denom)


def empirical_quantile(x: np.ndarray, q: float, method: str) -> float:
    """
    Wrapper to handle numpy version differences:
    - Newer numpy: np.quantile(..., method=)
    - Older numpy: np.quantile(..., interpolation=)
    """
    q = min(max(q, 1e-12), 1 - 1e-12)
    try:
        return float(np.quantile(x, q, method=method))
    except TypeError:
        # older numpy
        return float(np.quantile(x, q, interpolation=method))


def trajectory_lb_2period(demand: List[float], L: int, h: float, p: float, q: float, quantile_method: str) -> Tuple[float, int]:
    """
    Return (LB_total_over_T, T_total) for one trajectory, where T_total = len([0]*L + demand) = 50+L.
    Uses non-overlapping 2-period blocks across the entire padded horizon.
    """
    demand_ext = np.array(([0.0] * L) + [float(x) for x in demand], dtype=float)
    T_total = int(demand_ext.size)

    # If T_total is odd, append one more 0 so we can form full 2-period blocks (does not add demand).
    if T_total % 2 == 1:
        demand_ext = np.concatenate([demand_ext, np.array([0.0], dtype=float)])
        T_total += 1

    # Non-overlapping 2-period block demands
    D2 = demand_ext.reshape(-1, 2).sum(axis=1)  # shape = (T_total/2,)

    # Newsvendor S*
    S_star = empirical_quantile(D2, q, quantile_method)

    # Block costs and total
    over = np.maximum(S_star - D2, 0.0)
    under = np.maximum(D2 - S_star, 0.0)
    cost_blocks = h * over + p * under
    total_cost = float(cost_blocks.sum())
    return total_cost, T_total


def main() -> None:
    args = parse_args()
    script_dir = Path(__file__).resolve().parent
    out_csv = (script_dir / args.output_csv).resolve()

    json_files = scan_json_files(script_dir, args.recursive)
    if not json_files:
        raise RuntimeError(f"No json files found under {script_dir}")

    rows: List[Dict[str, Any]] = []

    for jp in json_files:
        try:
            instances = load_instances(jp)
        except Exception as e:
            print(f"[WARN] skip {jp}: {e}")
            continue
        if not instances:
            continue

        # Assume these are consistent within file; if not, we still compute per trajectory but report uniques.
        dist_name = str(instances[0].get("distribution", "")).lower().strip()

        # Collect per-trajectory LB
        lbs: List[float] = []
        L_values = []
        T_values = []

        # If costs differ across trajectories (unlikely), we handle per-trajectory and report ranges.
        h_values = []
        p_values = []

        for ins in instances:
            L = int(ins.get("lead_time", 0))
            demand = ins.get("demand", [])
            if not isinstance(demand, list):
                continue

            h = float(ins.get("holding_cost", instances[0].get("holding_cost", 0.0)))
            p = float(ins.get("lost_sales_cost", instances[0].get("lost_sales_cost", 0.0)))
            q = critical_fractile(h, p)

            lb_total, T_total = trajectory_lb_2period(
                demand=demand,
                L=L,
                h=h,
                p=p,
                q=q,
                quantile_method=args.quantile_method,
            )

            lbs.append(lb_total)
            L_values.append(L)
            T_values.append(T_total)
            h_values.append(h)
            p_values.append(p)

        if not lbs:
            continue

        lbs_arr = np.array(lbs, dtype=float)

        rows.append({
            "file": str(jp.relative_to(script_dir)),
            "LB_mean": float(lbs_arr.mean()),
            "LB_std": float(lbs_arr.std(ddof=0)),
        })

        print(f"[OK] {jp.name}: n={len(lbs)}, LB_mean={lbs_arr.mean():.6f}")

    if not rows:
        raise RuntimeError("No output rows produced. Check JSON schema / directory contents.")

    # Write one row per JSON file
    with out_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    print(f"\nSaved: {out_csv} (rows={len(rows)})")


if __name__ == "__main__":
    main()
