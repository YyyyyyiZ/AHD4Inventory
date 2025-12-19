import json
from collections import deque
from pathlib import Path
from typing import Dict, Any, Tuple, List

import numpy as np
import pandas as pd

FILE_PREFIXES = [
    'normal_std10_L2_c1_2', 'normal_std10_L2_c1_5', 'normal_std10_L4_c1_2', 'normal_std10_L4_c1_5',
    'normal_std10_L6_c1_2', 'normal_std10_L6_c1_5',
    'normal_std30_L2_c1_2', 'normal_std30_L2_c1_5', 'normal_std30_L4_c1_2', 'normal_std30_L4_c1_5',
    'normal_std30_L6_c1_2', 'normal_std30_L6_c1_5',

    'normal_std50_L2_c1_2','normal_std50_L2_c1_5','normal_std50_L4_c1_2','normal_std50_L4_c1_5',
    'normal_std50_L6_c1_2','normal_std50_L6_c1_5',

    'poisson_L2_c1_2', 'poisson_L2_c1_5', 'poisson_L4_c1_2', 'poisson_L4_c1_5',
    'poisson_L6_c1_2', 'poisson_L6_c1_5',

    'exponential_L2_c1_2', 'exponential_L2_c1_5', 'exponential_L4_c1_2', 'exponential_L4_c1_5',
    'exponential_L6_c1_2', 'exponential_L6_c1_5',
]

BASE_DIR = Path("../data")

def simulate_policy(instance, policy, S=None, q=None, cap=None):
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
        elif policy == "capped":
            order = min(max(0, S - on_hand - outstanding), cap)
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

def optimize_for_dataset(path: Path, dataset_name: str):

    with path.open("r") as f:
        data = json.load(f)

    N = len(data)
    T = data[0]["num_periods"]
    h = data[0]["holding_cost"]
    p = data[0]["lost_sales_cost"]
    L = data[0]["lead_time"]

    all_demands = np.array([d for inst in data for d in inst["demand"]])
    mean_d = all_demands.mean()

    center = mean_d * (L + 1)
    S_min = int(max(0, center - 300))
    S_max = int(center + 300)
    S_grid = list(range(S_min, S_max + 1))

    # =====================
    # Basestock
    # =====================
    best_S, best_avg50, best_total_cost = None, float("inf"), None

    for S in S_grid:
        total_cost_all, avg50_sum = 0.0, 0.0
        for inst in data:
            tot, avg50 = simulate_policy(inst, "basestock", S=S)
            total_cost_all += tot
            avg50_sum += avg50

        dataset_avg50 = avg50_sum / N
        if dataset_avg50 < best_avg50:
            best_avg50 = dataset_avg50
            best_S = S
            best_total_cost = total_cost_all

    local_lo, local_hi = best_S - 15, best_S + 15
    per_inst_S = []
    for inst in data:
        best_local_S, best_local_avg = None, float("inf")
        for S in range(local_lo, local_hi + 1):
            if S < 0:
                continue
            _, avg50 = simulate_policy(inst, "basestock", S=S)
            if avg50 < best_local_avg:
                best_local_avg = avg50
                best_local_S = S
        per_inst_S.append(best_local_S)


    best_total_cost = best_total_cost/len(data)
    print(f"=== {dataset_name} ===")
    print(f"L = {L}, h = {h}, p = {p}, N = {N}, T = {T}")
    print(f"Optimal base-stock S* = {best_S}, avg cost = {best_total_cost:.5f}")

    # =====================
    # Constant Order
    # =====================
    best_q, best_q_avg, best_q_tot = None, float("inf"), None
    for q in range(0, S_max + 1):
        tot_all, avg_all = 0, 0
        for inst in data:
            tot, avg = simulate_policy(inst, "constant", q=q)
            tot_all += tot
            avg_all += avg
        avg_dataset = avg_all / N
        if avg_dataset < best_q_avg:
            best_q_avg = avg_dataset
            best_q = q
            best_q_tot = tot_all
    best_q_tot = best_q_tot/len(data)
    print(f"Optimal constant order q* = {best_q}, avg cost = {best_q_tot:.5f}")

    # =====================
    # Capped Basestock
    # =====================
    best_Sc, best_cap, best_cap_avg, best_cap_tot = None, None, float("inf"), None
    for S in S_grid:
        for cap in range(0, S_max + 1, 5):
            tot_all, avg_all = 0, 0
            for inst in data:
                tot, avg = simulate_policy(inst, "capped", S=S, cap=cap)
                tot_all += tot
                avg_all += avg

            avg_dataset = avg_all / N
            if avg_dataset < best_cap_avg:
                best_cap_avg = avg_dataset
                best_Sc, best_cap, best_cap_tot = S, cap, tot_all
    best_cap_tot = best_cap_tot/len(data)
    print(f"Optimal capped basestock (S,C) = ({best_Sc}, {best_cap}), avg cost = {best_cap_tot:.5f}")
    print()

    return {
        "dataset": dataset_name,
        "opt_basestock": best_S,
        "total_cost_all_basestock": best_total_cost,
        "opt_const_q": best_q,
        "total_cost_all_const": best_q_tot,
        "opt_capped_S": best_Sc,
        "opt_capped_cap": best_cap,
        "total_cost_all_capped": best_cap_tot,
    }


def main():
    results = []

    for prefix in FILE_PREFIXES:
        for split in ["train", "test"]:
            json_name = f"{prefix}_{split}.json"
            path = BASE_DIR / json_name

            if not path.exists():
                print(f"[WARN] {json_name} not found, skip")
                continue

            summary = optimize_for_dataset(path, json_name)
            results.append(summary)

    df = pd.DataFrame(results)
    csv_path = BASE_DIR / "all_policies_summary.csv"
    df.to_csv(csv_path, index=False)
    print("\n=== Final summary written to:", csv_path)
    print(df)


if __name__ == "__main__":
    main()
