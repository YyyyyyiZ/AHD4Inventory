
"""
2-period newsvendor lower bound with lead-time padding, output ONE row per JSON file,
reporting both empirical and parametric results.

Given:
  demand_ext = [0]*L + demand
  Horizon length T = len(demand_ext) = 50 + L (or whatever the JSON provides)

We partition into non-overlapping 2-period blocks: (0,1), (2,3), ...
If T is odd, we append one extra 0 to make it even (does not add demand).

To avoid forcing a single S* across blocks with deterministic 0-demand padding, we use block types
based on indices (not on realized demand value):
  - "00": both indices < L (both are padding)
  - "0D": exactly one index < L
  - "DD": both indices >= L

For each type we compute an optimal newsvendor base-stock level S*:
  - Empirical: S*_type is the empirical q-quantile of block demands of that type (within each trajectory).
  - Parametric: S*_type is the theoretical q-quantile using known distribution with mean=100
               (Normal std is taken from JSON 'std_normal' if present, otherwise parsed from filename 'STDxx').

Cost per block: h*(S - D)^+ + p*(D - S)^+   (lost sales penalty, no backorders)
Trajectory total LB = sum over blocks
File-level output: mean/std/min/max over trajectories, one row per JSON file.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

# Optional SciPy for exact Poisson/Gamma quantiles; fallback to MC if not available.
try:
    from scipy import stats as st  # type: ignore
    HAS_SCIPY = True
except Exception:
    HAS_SCIPY = False

from statistics import NormalDist


MEAN_DEMAND = 100.0  # given by user


@dataclass
class NormalSpec:
    std: float


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--output_csv", type=str, default="_lb_2period.csv",
                   help="Output CSV filename saved in the same directory as this script.")
    p.add_argument("--recursive", action="store_true", default=True,
                   help="Recursively scan the script directory for *.json (default True).")
    p.add_argument("--seed", type=int, default=123, help="RNG seed (used only for MC fallback quantiles).")
    p.add_argument("--mc_samples", type=int, default=300000,
                   help="MC samples for parametric quantiles if SciPy is unavailable.")
    p.add_argument("--quantile_method", type=str, default="linear",
                   help="Quantile method for empirical quantiles (numpy). Common: linear, higher, lower, nearest.")
    return p.parse_args()


def scan_json_files(root_dir: Path, recursive: bool) -> List[Path]:
    if recursive:
        return sorted([p for p in root_dir.rglob("*.json") if p.is_file()])
    return sorted([p for p in root_dir.glob("*.json") if p.is_file()])


def load_instances(path: Path) -> Optional[List[Dict[str, Any]]]:
    """Return list of instances or None if the file is not in expected dataset format."""
    try:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        return None
    if not isinstance(data, list) or len(data) == 0 or not isinstance(data[0], dict):
        return None
    # Heuristic: dataset instance should have 'demand' list and 'lead_time'
    if "demand" not in data[0] or "lead_time" not in data[0]:
        return None
    if not isinstance(data[0].get("demand"), list):
        return None
    return data


def critical_fractile(h: float, p: float) -> float:
    denom = h + p
    if denom <= 0:
        return 0.5
    return float(p / denom)


def empirical_quantile(x: np.ndarray, q: float, method: str) -> float:
    q = min(max(q, 1e-12), 1 - 1e-12)
    if x.size == 0:
        return 0.0
    try:
        return float(np.quantile(x, q, method=method))
    except TypeError:
        return float(np.quantile(x, q, interpolation=method))


def parse_normal_std_from_filename(filename: str) -> Optional[float]:
    m = re.search(r"STD(\d+)", filename, flags=re.IGNORECASE)
    if not m:
        return None
    return float(m.group(1))


def get_normal_std(jp: Path, instances: List[Dict[str, Any]]) -> Optional[float]:
    # Prefer std_normal field if present
    for ins in instances:
        sn = ins.get("std_normal", None)
        if sn is not None:
            try:
                return float(sn)
            except Exception:
                pass
    # Fallback: parse from filename
    return parse_normal_std_from_filename(jp.name)


def parametric_quantile(dist: str, q: float, normal_std: Optional[float],
                        rng: np.random.Generator, mc_samples: int,
                        block_type: str) -> float:
    """
    Return theoretical q-quantile for the block-demand distribution for a given block type:
      - "00": degenerate 0
      - "0D": one-period demand
      - "DD": two-period sum
    Mean demand is known: 100.
    """
    q = min(max(q, 1e-12), 1 - 1e-12)

    if block_type == "00":
        return 0.0

    k = 1 if block_type == "0D" else 2  # number of real-demand periods in the block

    dist = dist.lower().strip()
    if dist == "poisson":
        lam = k * MEAN_DEMAND
        if HAS_SCIPY:
            return float(st.poisson(mu=lam).ppf(q))
        # MC fallback
        samples = rng.poisson(lam=lam, size=mc_samples).astype(float)
        return float(np.quantile(samples, q))

    if dist == "exponential":
        # one-period: Exp(mean=100) == Gamma(shape=1, scale=100)
        # two-period sum: Gamma(shape=2, scale=100)
        shape = float(k)
        scale = MEAN_DEMAND
        if HAS_SCIPY:
            return float(st.gamma(a=shape, scale=scale).ppf(q))
        samples = rng.gamma(shape=shape, scale=scale, size=mc_samples)
        return float(np.quantile(samples, q))

    if dist == "normal":
        if normal_std is None:
            raise ValueError("Normal distribution requires std (std_normal field or STDxx in filename).")
        mu = k * MEAN_DEMAND
        sigma = math.sqrt(k) * float(normal_std)
        nd = NormalDist(mu=mu, sigma=sigma)
        return float(nd.inv_cdf(q))

    raise ValueError(f"Unsupported distribution: {dist}")


def block_indices(T: int) -> List[Tuple[int, int]]:
    """Return list of non-overlapping pairs (0,1),(2,3),... after making T even via appending one 0 if needed."""
    if T % 2 == 1:
        T += 1
    return [(t, t + 1) for t in range(0, T, 2)]


def block_type_by_index(i: int, j: int, L: int) -> str:
    in_pad_i = (i < L)
    in_pad_j = (j < L)
    if in_pad_i and in_pad_j:
        return "00"
    if in_pad_i ^ in_pad_j:
        return "0D"
    return "DD"


def trajectory_costs_emp_param(
    demand: List[float],
    L: int,
    h: float,
    p: float,
    dist: str,
    normal_std: Optional[float],
    q: float,
    quantile_method: str,
    rng: np.random.Generator,
    mc_samples: int
) -> Tuple[float, float]:
    """
    Compute (LB_empirical, LB_parametric) total over the padded horizon for one trajectory.
    """
    # Build padded demand
    demand_ext = np.array(([0.0] * L) + [float(x) for x in demand], dtype=float)
    T = int(demand_ext.size)
    if T % 2 == 1:
        demand_ext = np.concatenate([demand_ext, np.array([0.0], dtype=float)])
        T += 1

    pairs = block_indices(T)

    # Collect block demands per type for empirical S*
    blocks: Dict[str, List[float]] = {"00": [], "0D": [], "DD": []}
    for (i, j) in pairs:
        bt = block_type_by_index(i, j, L)
        dsum = float(demand_ext[i] + demand_ext[j])
        blocks[bt].append(dsum)

    # Empirical S* per type (within this trajectory)
    S_emp = {
        bt: (0.0 if bt == "00" else empirical_quantile(np.array(vals, dtype=float), q, quantile_method))
        for bt, vals in blocks.items()
    }

    # Parametric S* per type (known mean=100; normal std from JSON/filename)
    S_par = {
        bt: parametric_quantile(dist, q, normal_std, rng, mc_samples, bt)
        for bt in ["00", "0D", "DD"]
    }

    # Compute realized total costs using the corresponding S* by type
    total_emp = 0.0
    total_par = 0.0
    for (i, j) in pairs:
        bt = block_type_by_index(i, j, L)
        dsum = float(demand_ext[i] + demand_ext[j])

        se = S_emp[bt]
        sp = S_par[bt]

        total_emp += h * max(se - dsum, 0.0) + p * max(dsum - se, 0.0)
        total_par += h * max(sp - dsum, 0.0) + p * max(dsum - sp, 0.0)

    return float(total_emp), float(total_par)


def main() -> None:
    args = parse_args()
    rng = np.random.default_rng(args.seed)

    script_dir = Path(__file__).resolve().parent
    out_csv = (script_dir / args.output_csv).resolve()

    json_files = scan_json_files(script_dir, args.recursive)
    if not json_files:
        raise RuntimeError(f"No json files found under {script_dir}")

    rows: List[Dict[str, Any]] = []

    for jp in json_files:
        instances = load_instances(jp)
        if instances is None:
            continue

        # File-level metadata (assume consistent)
        dist = str(instances[0].get("distribution", "")).lower().strip()
        # Costs could be inside each instance; assume consistent, but we still take from each instance when computing.
        normal_std = get_normal_std(jp, instances) if dist == "normal" else None

        # Compute per-trajectory totals, then aggregate
        emp_list: List[float] = []
        par_list: List[float] = []
        L_list: List[int] = []
        h_list: List[float] = []
        p_list: List[float] = []

        for ins in instances:
            demand = ins.get("demand", [])
            if not isinstance(demand, list):
                continue
            L = int(ins.get("lead_time", 0))
            h = float(ins.get("holding_cost", 0.0))
            p = float(ins.get("lost_sales_cost", 0.0))
            q = critical_fractile(h, p)

            emp, par = trajectory_costs_emp_param(
                demand=demand,
                L=L,
                h=h,
                p=p,
                dist=dist,
                normal_std=normal_std,
                q=q,
                quantile_method=args.quantile_method,
                rng=rng,
                mc_samples=args.mc_samples,
            )

            emp_list.append(emp)
            par_list.append(par)
            L_list.append(L)
            h_list.append(h)
            p_list.append(p)

        if not emp_list:
            continue

        emp_arr = np.array(emp_list, dtype=float)
        par_arr = np.array(par_list, dtype=float)

        rows.append({
            "file": str(jp.relative_to(script_dir)),
            # "distribution": dist,
            # "mean_demand_assumed": MEAN_DEMAND,
            # "normal_std_used": normal_std,
            # "num_trajectories": int(len(emp_arr)),
            # "lead_time_L_unique": sorted(list(set(L_list))),
            # "holding_cost_unique": sorted(list(set(h_list))),
            # "lost_sales_cost_unique": sorted(list(set(p_list))),
            "LB_emp_mean": float(emp_arr.mean()),
            # "LB_emp_std": float(emp_arr.std(ddof=0)),
            # "LB_emp_min": float(emp_arr.min()),
            # "LB_emp_max": float(emp_arr.max()),
            "LB_par_mean": float(par_arr.mean()),
            # "LB_par_std": float(par_arr.std(ddof=0)),
            # "LB_par_min": float(par_arr.min()),
            # "LB_par_max": float(par_arr.max()),
        })

        print(f"[OK] {jp.name}: n={len(emp_arr)}, emp_mean={emp_arr.mean():.6f}, par_mean={par_arr.mean():.6f}")

    if not rows:
        raise RuntimeError("No dataset JSON files were processed. Check file format and directory.")

    with out_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    print(f"\nSaved: {out_csv} (rows={len(rows)})")


if __name__ == "__main__":
    main()
