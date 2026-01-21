import argparse
import json
from collections import deque
from pathlib import Path
from typing import Dict, Any, List, Tuple

import numpy as np
import pandas as pd


def simulate_policy(instance: Dict[str, Any], policy: str, S: int = None, q: int = None) -> Tuple[float, float]:
    """
    Simulate one instance under a given policy.
    Returns: (total_cost, avg_cost_per_period_over_T)
    """
    L = instance["lead_time"]
    h = instance["holding_cost"]
    p = instance["lost_sales_cost"]
    T = instance["lead_time"] + instance["num_periods"]

    demand = [0] * instance["lead_time"] + instance["demand"]
    on_hand = instance["initial_inventory"]

    pipeline = deque([0] * L, maxlen=L)
    total_cost = 0.0

    for t in range(T):
        if L > 0:
            on_hand += pipeline.popleft()

        outstanding = sum(pipeline) if L > 0 else 0

        if policy == "basestock":
            order = max(0, S - on_hand - outstanding)
        elif policy == "constant":
            order = q
        else:
            raise ValueError("Unknown policy")

        if L > 0:
            pipeline.append(order)
        else:
            on_hand += order

        d = demand[t]
        sales = min(on_hand, d)
        lost = d - sales
        on_hand -= sales

        total_cost += h * on_hand + p * lost

    return total_cost, total_cost / T


def optimize_for_dataset(path: Path, lead_time_override: int = None, lost_sales_cost_override: float = None) -> Dict[str, Any]:
    """
    Compute optimal basestock S* and constant order q* for a dataset json file.
    Keeps the same search logic as the original script: S grid centered at mean_d*(L+1) +/- 300,
    q grid from 0..S_max.
    """
    with path.open("r") as f:
        data = json.load(f)

    # Optional in-memory overrides (keep demand data unchanged)
    if lead_time_override is not None or lost_sales_cost_override is not None:
        for inst in data:
            if lead_time_override is not None:
                inst["lead_time"] = int(lead_time_override)
            if lost_sales_cost_override is not None:
                inst["lost_sales_cost"] = float(lost_sales_cost_override)

    if not isinstance(data, list) or len(data) == 0:
        raise ValueError(f"Dataset file {path.name} is empty or not a list.")

    N = len(data)
    T = data[0]["num_periods"]
    h = data[0]["holding_cost"]
    p = data[0]["lost_sales_cost"]
    L = data[0]["lead_time"]

    all_demands = np.array([d for inst in data for d in inst["demand"]], dtype=float)
    mean_d = float(all_demands.mean()) if all_demands.size > 0 else 0.0

    center = mean_d * (L + 1)
    S_min = int(max(0, center - 300))
    S_max = int(center + 300)
    S_grid = list(range(S_min, S_max + 1))

    # =====================
    # Basestock
    # =====================
    best_S, best_avg, best_total_cost = None, float("inf"), None

    for S in S_grid:
        total_cost_all, avg_sum = 0.0, 0.0
        for inst in data:
            tot, avg = simulate_policy(inst, "basestock", S=S)
            total_cost_all += tot
            avg_sum += avg

        dataset_avg = avg_sum / N
        if dataset_avg < best_avg:
            best_avg = dataset_avg
            best_S = S
            best_total_cost = total_cost_all

    best_total_cost = best_total_cost / N

    # =====================
    # Constant Order
    # =====================
    best_q, best_q_avg, best_q_tot = None, float("inf"), None
    for q in range(0, S_max + 1):
        tot_all, avg_all = 0.0, 0.0
        for inst in data:
            tot, avg = simulate_policy(inst, "constant", q=q)
            tot_all += tot
            avg_all += avg

        avg_dataset = avg_all / N
        if avg_dataset < best_q_avg:
            best_q_avg = avg_dataset
            best_q = q
            best_q_tot = tot_all

    best_q_tot = best_q_tot / N

    print(f"=== {path.name} ===")
    print(f"L={L}, h={h}, p={p}, N={N}, num_periods={T}, mean_d={mean_d:.4f}")
    print(f"Optimal basestock S*={best_S}, avg cost={best_total_cost:.5f}")
    print(f"Optimal constant order q*={best_q}, avg cost={best_q_tot:.5f}")
    print()

    return {
        "dataset": f"{path.name}_L{L}_p{int(p)}",
        # "source_file": path.name,
        "L": L,
        "h": h,
        "p": p,
        "N": N,
        "num_periods": T,
        "mean_d": mean_d,
        "opt_basestock_S": best_S,
        "avg_cost_basestock": best_total_cost,
        "opt_constant_q": best_q,
        "avg_cost_constant": best_q_tot,
    }


def discover_json_datasets(base_dir: Path) -> List[Path]:
    """
    New dataset discovery:
    - Scan the current directory for *_train.json and *_test.json files.
    - Assumption: these are the generated inventory instances.
    """
    train = sorted(base_dir.glob("*_train.json"))
    test = sorted(base_dir.glob("*_test.json"))
    return train + test


def main():
    parser = argparse.ArgumentParser(description="Compute optimal basestock S* and constant order q* for each dataset, under a grid of (lead_time, lost_sales_cost) overrides.")
    parser.add_argument("--lead_time", type=int, default=None, help="Optional: override lead_time (L). If omitted, run the full grid {2,4,6,8}.")
    parser.add_argument("--lost_sales_cost", type=float, default=None, help="Optional: override lost_sales_cost (p). If omitted, run the full grid {2,4,6,10}.")
    args = parser.parse_args()

    base_dir = Path(__file__).resolve().parent
    paths = discover_json_datasets(base_dir)

    if not paths:
        raise FileNotFoundError(f"No *_train.json / *_test.json found in {base_dir}")

    lead_times = [2, 4, 6, 8] if args.lead_time is None else [int(args.lead_time)]
    lost_sales_costs = [2, 4, 6, 10] if args.lost_sales_cost is None else [float(args.lost_sales_cost)]

    for L in lead_times:
        for p in lost_sales_costs:
            print("\n==============================")
            print(f"Running configuration: L={L}, lost_sales_cost={p}")
            print("==============================\n")

            results = []
            for i, path in enumerate(paths, start=1):
                print(f"[{i}/{len(paths)}] Processing {path.name}")
                try:
                    summary = optimize_for_dataset(path, lead_time_override=L, lost_sales_cost_override=p)
                    results.append(summary)
                except Exception as e:
                    print(f"[ERROR] Failed on {path.name}: {e}")

            df = pd.DataFrame(results)
            csv_path = base_dir / f"basestock_constant_summary_L{L}_p{int(p) if float(p).is_integer() else p}.csv"
            df.to_csv(csv_path, index=False)
            print("\n=== Final summary written to:", csv_path)
            print(df)


if __name__ == "__main__":
    main()
