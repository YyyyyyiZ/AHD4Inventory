
import json
from collections import deque
from pathlib import Path
from typing import Dict, Any, Tuple, List

import numpy as np
import pandas as pd

# ----------------------------------------------------------------------
# 1. 所有要处理的文件前缀（不含 _train / _test / .json）
# ----------------------------------------------------------------------

FILE_PREFIXES = [
    # normal (std = 10, 20, 30)
    'normal_std10_L2_c1_2','normal_std10_L2_c1_5','normal_std10_L4_c1_2','normal_std10_L4_c1_5','normal_std10_L6_c1_2','normal_std10_L6_c1_5',
    'normal_std30_L2_c1_2','normal_std30_L2_c1_5','normal_std30_L4_c1_2','normal_std30_L4_c1_5','normal_std30_L6_c1_2','normal_std30_L6_c1_5',

    # poisson
    'poisson_L2_c1_2','poisson_L2_c1_5','poisson_L4_c1_2','poisson_L4_c1_5','poisson_L6_c1_2','poisson_L6_c1_5',

    # exponential
    'exponential_L2_c1_2','exponential_L2_c1_5','exponential_L4_c1_2','exponential_L4_c1_5','exponential_L6_c1_2','exponential_L6_c1_5',

    # pareto
    'pareto_L2_c1_2','pareto_L2_c1_5','pareto_L4_c1_2','pareto_L4_c1_5','pareto_L6_c1_2','pareto_L6_c1_5',
]

# 所有 json 与脚本放在同一目录；如需调整路径，在这里改
BASE_DIR = Path(".")


# ----------------------------------------------------------------------
# 2. 单条轨迹仿真：给定 base-stock S，返回 (total_cost, avg_cost_over_50)
# ----------------------------------------------------------------------

def simulate_instance(instance: Dict[str, Any], S: int) -> Tuple[float, float]:
    """
    仿真一条 demand 轨迹，在给定 base-stock S 下的总成本和 50 期平均成本。

    时序：到货(期初) -> 下单 -> 需求(lost sales) -> 期末 cost
    成本：h * ending_inventory + p * lost_sales
    """
    L = instance["lead_time"]
    h = instance["holding_cost"]
    p = instance["lost_sales_cost"]
    T = instance["num_periods"]
    demand = instance["demand"]
    on_hand = instance["initial_inventory"]

    # 初始管道队列全 0，长度 L
    pipeline: deque[int] = deque([0] * L, maxlen=L)

    total_cost = 0.0

    for t in range(T):
        # 1) 期初到货
        if L > 0:
            on_hand += pipeline.popleft()

        # 2) 下单 (base-stock policy)
        outstanding = sum(pipeline) if L > 0 else 0
        order = max(0, S - on_hand - outstanding)
        if L > 0:
            pipeline.append(order)

        # 3) 需求 (lost sales)
        d = demand[t]
        sales = min(on_hand, d)
        lost = d - sales
        on_hand -= sales

        # 4) 成本
        total_cost += h * on_hand + p * lost

    avg_50 = total_cost / T
    return total_cost, avg_50


# ----------------------------------------------------------------------
# 3. 对一个数据集 (某个 json 文件) 搜索 S* 并做验证
# ----------------------------------------------------------------------

def optimize_for_dataset(path: Path, dataset_name: str) -> Dict[str, Any]:
    with path.open("r") as f:
        data: List[Dict[str, Any]] = json.load(f)

    N = len(data)
    assert N > 0, f"{path} is empty"

    T = data[0]["num_periods"]
    h = data[0]["holding_cost"]
    p = data[0]["lost_sales_cost"]
    L = data[0]["lead_time"]

    # 所有 demand 展开成一个数组，用于估计搜索区间
    all_demands = np.array([d for inst in data for d in inst["demand"]], dtype=float)
    mean_d = float(all_demands.mean())

    # 以 (L+1)*mean_d 为中心，左右各 140，覆盖绝大部分合理 S
    center = mean_d * (L + 1)
    S_min = int(max(0, center - 300))
    S_max = int(center + 300)
    S_grid = list(range(S_min, S_max + 1))

    best_S = None
    best_avg50 = float("inf")
    best_total_cost = None

    # ---- 全局网格搜索 ----
    for S in S_grid:
        total_cost_all = 0.0
        avg50_sum = 0.0
        for inst in data:
            tot, avg50 = simulate_instance(inst, S)
            total_cost_all += tot
            avg50_sum += avg50
        dataset_avg50 = avg50_sum / N

        if dataset_avg50 < best_avg50:
            best_avg50 = dataset_avg50
            best_S = S
            best_total_cost = total_cost_all

    assert best_S is not None

    # ---- 验证：按轨迹局部搜索 S_i (在 S*±15 内) ----
    local_lo = max(S_min, best_S - 15)
    local_hi = min(S_max, best_S + 15)
    local_grid = list(range(local_lo, local_hi + 1))

    per_inst_S = []
    per_inst_avg50 = []

    for inst in data:
        best_local_S = None
        best_local_avg = float("inf")
        for S in local_grid:
            _, avg50 = simulate_instance(inst, S)
            if avg50 < best_local_avg:
                best_local_avg = avg50
                best_local_S = S
        per_inst_S.append(best_local_S)
        per_inst_avg50.append(best_local_avg)

    S_i_mean = float(np.mean(per_inst_S))
    S_i_std = float(np.std(per_inst_S, ddof=0))

    # 打印验证信息，方便你 eyeball check
    print(f"=== {dataset_name} ===")
    print(f"file: {path.name}")
    print(f"L = {L}, h = {h}, p = {p}, N = {N}, T = {T}")
    print(f"S grid: [{S_min}, {S_max}], step = 1")
    print(f"Optimal base-stock S* = {best_S}")
    print(f"Dataset avg 50-period cost (mean over trajectories) = {best_avg50:.5f}")
    print(f"Per-trajectory local search range: [{local_lo}, {local_hi}]")
    print(f"  mean(S_i) = {S_i_mean:.3f}, std(S_i) = {S_i_std:.3f}")
    print()

    return {
        "dataset": dataset_name,
        "opt_basestock": int(best_S),
        "opt_cost_50": float(best_avg50)*50,
        "total_cost_all": float(best_total_cost),
        "L": L,
        "h": h,
        "p": p,
        "S_grid_min": S_min,
        "S_grid_max": S_max,
        "S_i_mean": S_i_mean,
        "S_i_std": S_i_std,
    }


# ----------------------------------------------------------------------
# 4. 主程序：所有前缀 × {train, test} 跑一遍，并写 CSV
# ----------------------------------------------------------------------

def main():
    results = []

    for prefix in FILE_PREFIXES:
        for split in ["train", "test"]:
            json_name = f"{prefix}_{split}.json"
            path = BASE_DIR / json_name
            if not path.exists():
                print(f"[WARN] {json_name} not found, skip")
                continue

            dataset_name = f"{prefix}_{split}"
            summary = optimize_for_dataset(path, dataset_name)

            # 只保留你需要的三列 + dataset 名
            results.append({
                "dataset": summary["dataset"],          # 文件名（含 _train/_test）
                "opt_basestock": summary["opt_basestock"],
                "opt_cost_50": summary["opt_cost_50"],
            })

    # 汇总成一个 CSV
    if results:
        df = pd.DataFrame(results)
        csv_path = BASE_DIR / "basestock_summary.csv"
        df.to_csv(csv_path, index=False)
        print("=== Final summary written to:", csv_path)
        print(df)
    else:
        print("No datasets processed (no json files found?).")


if __name__ == "__main__":
    main()
