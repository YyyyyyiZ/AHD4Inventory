import argparse
import json
import re
from pathlib import Path
from typing import Dict, Any, List, Tuple

import numpy as np
import pandas as pd


def _rewrite_dataset_id(file_name: str, L: int, p: float) -> str:
    """Rewrite file_name by replacing embedded lead time / cost token with (L, p)."""
    pt = str(int(p)) if float(p).is_integer() else str(p)
    out = re.sub(r"_L\d+(?=[^0-9]|$)", f"_L{int(L)}", file_name)
    out = re.sub(r"_c\d+_\d+(?=[^0-9A-Za-z]|$)", f"_p{pt}", out)
    out = re.sub(r"_p\d+(?:p\d+)?(?=[^0-9A-Za-z]|$)", f"_p{pt}", out)

    if out == file_name:
        m = re.search(r"(_train|_test)(\.json)?$", file_name)
        suffix = m.group(0) if m else ""
        base = file_name[:-len(suffix)] if suffix else file_name
        out = f"{base}_L{int(L)}_p{pt}{suffix}"
    return out


# ----------------------------
# Dataset pairing (new)
# ----------------------------
def discover_train_test_pairs(base_dir: Path) -> List[Tuple[Path, Path]]:
    """Return list of (train_path, test_path) pairs discovered in base_dir."""
    pairs: List[Tuple[Path, Path]] = []
    for train_path in sorted(base_dir.glob("*_train.json")):
        test_name = train_path.name.replace("_train.json", "_test.json")
        test_path = base_dir / test_name
        if not test_path.exists():
            # Per user: skip incomplete pairs with a warning (they claim won't happen).
            print(f"[WARN] Missing matching test file for {train_path.name}: expected {test_name}. Skipping.")
            continue
        pairs.append((train_path, test_path))
    return pairs


# ----------------------------
# Vectorized simulation
# ----------------------------
def pack_dataset(data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Convert list-of-instances JSON into vectorized arrays for fast simulation."""
    if not data:
        raise ValueError("Empty dataset.")

    L = int(data[0]["lead_time"])
    num_periods = int(data[0]["num_periods"])
    T_total = L + num_periods

    h = float(data[0]["holding_cost"])
    p = float(data[0]["lost_sales_cost"])

    N = len(data)

    init_inv = np.array([int(inst["initial_inventory"]) for inst in data], dtype=np.int64)

    demand = np.zeros((N, T_total), dtype=np.int64)
    for i, inst in enumerate(data):
        d = inst.get("demand", [])
        if len(d) != num_periods:
            raise ValueError(
                f"Instance {i} demand length mismatch: expected {num_periods}, got {len(d)}"
            )
        demand[i, L:] = np.array(d, dtype=np.int64)

    return {
        "N": N,
        "L": L,
        "num_periods": num_periods,
        "T_total": T_total,
        "h": h,
        "p": p,
        "init_inv": init_inv,
        "demand": demand,
    }


def simulate_capped_batch(pack: Dict[str, Any], S: int, cap: int) -> float:
    """Vectorized simulation for capped basestock; returns average cost per period per instance."""
    N = pack["N"]
    L = pack["L"]
    T_total = pack["T_total"]
    h = pack["h"]
    p = pack["p"]
    demand = pack["demand"]

    on_hand = pack["init_inv"].astype(np.int64).copy()

    if L > 0:
        pipeline = np.zeros((N, L), dtype=np.int64)
    else:
        pipeline = None

    total_cost = 0.0

    for t in range(T_total):
        if L > 0:
            on_hand += pipeline[:, 0]
            if L > 1:
                pipeline[:, :-1] = pipeline[:, 1:]
            pipeline[:, -1] = 0

            outstanding = pipeline.sum(axis=1)
            gap = S - on_hand - outstanding
            order = np.clip(gap, 0, cap).astype(np.int64)
            pipeline[:, -1] = order
        else:
            gap = S - on_hand
            order = np.clip(gap, 0, cap).astype(np.int64)
            on_hand += order

        d = demand[:, t]
        sales = np.minimum(on_hand, d)
        lost = d - sales
        on_hand -= sales

        total_cost += float(h) * float(on_hand.sum()) + float(p) * float(lost.sum())

    return total_cost / float(N)


# ----------------------------
# Two-stage search (coarse -> refine)
# ----------------------------
def optimize_capped(pack_full: Dict[str, Any], mean_d: float) -> Tuple[int, int, float]:
    """Coarse-to-fine search for (S, cap). Returns (best_S, best_cap, best_avg_cost)."""

    L = pack_full["L"]
    center = mean_d * (L + 1)
    S_min = int(max(0, center - 300))
    S_max = int(center + 300)

    # Stage 0: subsample screening
    N = pack_full["N"]
    rng = np.random.default_rng(0)
    n0 = min(120, N)
    idx = rng.choice(N, size=n0, replace=False)

    pack0 = dict(pack_full)
    pack0["N"] = n0
    pack0["init_inv"] = pack_full["init_inv"][idx].copy()
    pack0["demand"] = pack_full["demand"][idx, :].copy()

    S_step0 = 10
    cap_step0 = 25
    S_grid0 = list(range(S_min, S_max + 1, S_step0))
    cap_grid0 = list(range(0, S_max + 1, cap_step0))
    if cap_grid0 and cap_grid0[-1] != S_max:
        cap_grid0.append(S_max)

    K = 12
    best_list: List[Tuple[float, int, int]] = []
    for cap in cap_grid0:
        for S in S_grid0:
            c = simulate_capped_batch(pack0, S=S, cap=cap)
            if len(best_list) < K:
                best_list.append((c, S, cap))
                best_list.sort(key=lambda x: x[0])
            else:
                if c < best_list[-1][0]:
                    best_list[-1] = (c, S, cap)
                    best_list.sort(key=lambda x: x[0])

    # Stage 1: local refinement on full dataset
    S_win = 40
    cap_win = 80
    S_step1 = 2
    cap_step1 = 5

    best_cost = float("inf")
    best_S = 0
    best_cap = 0

    cand_pairs = set()
    for _, S0, cap0 in best_list:
        S_lo = max(0, S0 - S_win)
        S_hi = S0 + S_win
        cap_lo = max(0, cap0 - cap_win)
        cap_hi = cap0 + cap_win
        for cap in range(cap_lo, cap_hi + 1, cap_step1):
            for S in range(S_lo, S_hi + 1, S_step1):
                cand_pairs.add((S, cap))

    for (S, cap) in sorted(cand_pairs, key=lambda z: (z[1], z[0])):
        c = simulate_capped_batch(pack_full, S=S, cap=cap)
        if c < best_cost:
            best_cost = c
            best_S = S
            best_cap = cap

    return int(best_S), int(best_cap), float(best_cost)


def _load_and_override(path: Path, lead_time_override: int = None, lost_sales_cost_override: float = None) -> List[Dict[str, Any]]:
    with path.open("r") as f:
        data = json.load(f)

    if not isinstance(data, list) or len(data) == 0:
        raise ValueError(f"Dataset file {path.name} is empty or not a list.")

    if lead_time_override is not None or lost_sales_cost_override is not None:
        for inst in data:
            if lead_time_override is not None:
                inst["lead_time"] = int(lead_time_override)
            if lost_sales_cost_override is not None:
                inst["lost_sales_cost"] = float(lost_sales_cost_override)
    return data


def optimize_on_train(train_path: Path, lead_time_override: int, lost_sales_cost_override: float) -> Tuple[Dict[str, Any], int, int]:
    """Optimize (S,cap) on train; return train_row and (S*,cap*)."""
    data = _load_and_override(train_path, lead_time_override, lost_sales_cost_override)

    all_demands = np.array([d for inst in data for d in inst["demand"]], dtype=float)
    mean_d = float(all_demands.mean()) if all_demands.size > 0 else 0.0
    pack = pack_dataset(data)

    best_S, best_cap, best_avg = optimize_capped(pack, mean_d)

    print(f"=== TRAIN {train_path.name} ===")
    print(
        f"L={pack['L']}, h={pack['h']}, p={pack['p']}, N={pack['N']}, num_periods={pack['num_periods']}, mean_d={mean_d:.4f}"
    )
    print(f"Optimal capped basestock (S,cap)=({best_S},{best_cap}), avg cost={best_avg:.6f}")
    print()

    row = {
        "dataset": _rewrite_dataset_id(train_path.name, pack["L"], pack["p"]),
        "source_file": train_path.name,
        "L": pack["L"],
        "h": pack["h"],
        "p": pack["p"],
        "N": pack["N"],
        "num_periods": pack["num_periods"],
        "mean_d": mean_d,
        "opt_capped_S": best_S,
        "opt_capped_cap": best_cap,
        "avg_cost_capped": float(best_avg),
    }
    return row, best_S, best_cap


def evaluate_on_test(
    test_path: Path,
    S: int,
    cap: int,
    lead_time_override: int,
    lost_sales_cost_override: float,
) -> Dict[str, Any]:
    """Evaluate capped basestock on test using provided (S,cap); return test_row."""
    data = _load_and_override(test_path, lead_time_override, lost_sales_cost_override)

    all_demands = np.array([d for inst in data for d in inst["demand"]], dtype=float)
    mean_d = float(all_demands.mean()) if all_demands.size > 0 else 0.0
    pack = pack_dataset(data)

    avg = simulate_capped_batch(pack, S=S, cap=cap)

    print(f"=== TEST  {test_path.name} ===")
    print(
        f"L={pack['L']}, h={pack['h']}, p={pack['p']}, N={pack['N']}, num_periods={pack['num_periods']}, mean_d={mean_d:.4f}"
    )
    print(f"Evaluate capped basestock (S,cap)=({S},{cap}), avg cost={avg:.6f}")
    print()

    return {
        "dataset": _rewrite_dataset_id(test_path.name, pack["L"], pack["p"]),
        "source_file": test_path.name,
        "L": pack["L"],
        "h": pack["h"],
        "p": pack["p"],
        "N": pack["N"],
        "num_periods": pack["num_periods"],
        "mean_d": mean_d,
        "opt_capped_S": int(S),
        "opt_capped_cap": int(cap),
        "avg_cost_capped": float(avg),
    }


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Optimize capped basestock (S,cap) on TRAIN only, then evaluate on TEST, "
            "for each dataset pair under a grid of (lead_time, lost_sales_cost) overrides."
        )
    )
    parser.add_argument(
        "--lead_time",
        type=int,
        default=None,
        help="Optional: override lead_time (L). If omitted, run the full grid {2,4,6,8}.",
    )
    parser.add_argument(
        "--lost_sales_cost",
        type=float,
        default=None,
        help="Optional: override lost_sales_cost (p). If omitted, run the full grid {2,4,6,10}.",
    )
    args = parser.parse_args()

    base_dir = Path(__file__).resolve().parent
    pairs = discover_train_test_pairs(base_dir)
    if not pairs:
        raise FileNotFoundError(f"No *_train.json found in {base_dir}")

    lead_times = [2, 4, 6, 8] if args.lead_time is None else [int(args.lead_time)]
    lost_sales_costs = [2, 4, 6, 10] if args.lost_sales_cost is None else [float(args.lost_sales_cost)]

    for L in lead_times:
        for p in lost_sales_costs:
            print("\n==============================")
            print(f"Running configuration: L={L}, lost_sales_cost={p}")
            print("==============================\n")

            results: List[Dict[str, Any]] = []
            for i, (train_path, test_path) in enumerate(pairs, start=1):
                print(f"[{i}/{len(pairs)}] Pair: {train_path.name}  <->  {test_path.name}")
                try:
                    train_row, S_star, cap_star = optimize_on_train(
                        train_path, lead_time_override=L, lost_sales_cost_override=p
                    )
                    results.append(train_row)
                    test_row = evaluate_on_test(
                        test_path,
                        S=S_star,
                        cap=cap_star,
                        lead_time_override=L,
                        lost_sales_cost_override=p,
                    )
                    results.append(test_row)
                except Exception as e:
                    print(f"[ERROR] Failed on pair {train_path.name} / {test_path.name}: {e}")

            df = pd.DataFrame(results)
            csv_path = base_dir / f"capped_basestock_summary_L{L}_p{int(p) if float(p).is_integer() else p}.csv"
            df.to_csv(csv_path, index=False)
            print("\n=== Final summary written to:", csv_path)
            print(df)


if __name__ == "__main__":
    main()
