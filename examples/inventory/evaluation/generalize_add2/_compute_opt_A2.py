import argparse
import json
import re
from collections import deque
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional

import numpy as np
import pandas as pd


def _rewrite_dataset_id(file_name: str, L: int, p: float) -> str:
    """Rewrite file_name by replacing embedded lead time / cost token with (L, p).

    Notes
    -----
    - The raw JSON filenames may encode an original lead time / cost token (e.g., _L6_c1_2_...).
    - We override (L, p) in-memory for experimentation; this function ensures the saved `dataset`
      identifier matches the overridden configuration.
    - The function preserves the original train/test suffix if present.
    """
    pt = str(int(p)) if float(p).is_integer() else str(p)

    # Replace common encodings:
    #   - lead time: _L<digits>
    #   - cost ratio: either _c1_2 style, or already _p2 / _p2p5 style
    out = re.sub(r"_L\d+(?=[^0-9]|$)", f"_L{int(L)}", file_name)
    out = re.sub(r"_c\d+_\d+(?=[^0-9A-Za-z]|$)", f"_p{pt}", out)
    out = re.sub(r"_p\d+(?:p\d+)?(?=[^0-9A-Za-z]|$)", f"_p{pt}", out)

    # If nothing matched, append _L{L}_p{p} before the (optional) train/test suffix.
    if out == file_name:
        m = re.search(r"(_train|_test)(\.json)?$", file_name)
        suffix = m.group(0) if m else ""
        base = file_name[:-len(suffix)] if suffix else file_name
        out = f"{base}_L{int(L)}_p{pt}{suffix}"
    return out


def _load_dataset_with_overrides(
    path: Path,
    lead_time_override: Optional[int] = None,
    lost_sales_cost_override: Optional[float] = None,
) -> List[Dict[str, Any]]:
    """Load a dataset (list of instances) and optionally override (L, p) in-memory."""
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


def simulate_policy(instance: Dict[str, Any], policy: str, S: int = None, q: int = None) -> Tuple[float, float]:
    """
    Simulate one instance under a given policy.

    Returns
    -------
    total_cost : float
        Total cost accumulated over T = lead_time + num_periods periods, with demand padded by L zeros.
    avg_cost : float
        total_cost / T
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
            if S is None:
                raise ValueError("Basestock policy requires S.")
            order = max(0, S - on_hand - outstanding)
        elif policy == "constant":
            if q is None:
                raise ValueError("Constant policy requires q.")
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


def _summarize_dataset(
    data: List[Dict[str, Any]],
    source_file: str,
) -> Dict[str, Any]:
    """Extract shared metadata and compute mean demand across all trajectories."""
    N = len(data)
    T = data[0]["num_periods"]
    h = data[0]["holding_cost"]
    p = data[0]["lost_sales_cost"]
    L = data[0]["lead_time"]

    all_demands = np.array([d for inst in data for d in inst["demand"]], dtype=float)
    mean_d = float(all_demands.mean()) if all_demands.size > 0 else 0.0

    return {
        "dataset": _rewrite_dataset_id(source_file, L, p),
        "source_file": source_file,
        "L": L,
        "h": h,
        "p": p,
        "N": N,
        "num_periods": T,
        "mean_d": mean_d,
    }


def optimize_on_training_dataset(
    train_path: Path,
    lead_time_override: Optional[int] = None,
    lost_sales_cost_override: Optional[float] = None,
) -> Dict[str, Any]:
    """
    Optimize basestock S* and constant order q* on a training dataset.

    Keeps the same search logic as the original script:
    - S grid centered at mean_d*(L+1) +/- 300
    - q grid from 0..S_max
    """
    data = _load_dataset_with_overrides(
        train_path,
        lead_time_override=lead_time_override,
        lost_sales_cost_override=lost_sales_cost_override,
    )
    meta = _summarize_dataset(data, train_path.name)

    N = meta["N"]
    L = meta["L"]
    p = meta["p"]
    h = meta["h"]
    T = meta["num_periods"]
    mean_d = meta["mean_d"]

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

    best_total_cost = (best_total_cost / N) if best_total_cost is not None else float("inf")

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

    best_q_tot = (best_q_tot / N) if best_q_tot is not None else float("inf")

    print(f"=== TRAIN OPT: {train_path.name} ===")
    print(f"L={L}, h={h}, p={p}, N={N}, num_periods={T}, mean_d={mean_d:.4f}")
    print(f"Optimal basestock S*={best_S}, avg cost={best_total_cost:.5f}")
    print(f"Optimal constant order q*={best_q}, avg cost={best_q_tot:.5f}")
    print()

    return {
        **meta,
        "opt_basestock_S": best_S,
        "avg_cost_basestock": best_total_cost,
        "opt_constant_q": best_q,
        "avg_cost_constant": best_q_tot,
    }


def evaluate_dataset_with_fixed_params(
    path: Path,
    basestock_S: int,
    constant_q: int,
    lead_time_override: Optional[int] = None,
    lost_sales_cost_override: Optional[float] = None,
) -> Dict[str, Any]:
    """Evaluate a dataset under fixed basestock/constant parameters (no re-optimization)."""
    data = _load_dataset_with_overrides(
        path,
        lead_time_override=lead_time_override,
        lost_sales_cost_override=lost_sales_cost_override,
    )
    meta = _summarize_dataset(data, path.name)

    N = meta["N"]
    L = meta["L"]
    p = meta["p"]
    h = meta["h"]
    T = meta["num_periods"]
    mean_d = meta["mean_d"]

    # Basestock evaluation
    tot_all, avg_all = 0.0, 0.0
    for inst in data:
        tot, avg = simulate_policy(inst, "basestock", S=basestock_S)
        tot_all += tot
        avg_all += avg
    avg_cost_bs = (tot_all / N)

    # Constant evaluation
    tot_all2, avg_all2 = 0.0, 0.0
    for inst in data:
        tot, avg = simulate_policy(inst, "constant", q=constant_q)
        tot_all2 += tot
        avg_all2 += avg
    avg_cost_c = (tot_all2 / N)

    print(f"=== EVAL (FIXED PARAMS): {path.name} ===")
    print(f"L={L}, h={h}, p={p}, N={N}, num_periods={T}, mean_d={mean_d:.4f}")
    print(f"Using basestock S={basestock_S}, avg cost={avg_cost_bs:.5f}")
    print(f"Using constant q={constant_q}, avg cost={avg_cost_c:.5f}")
    print()

    return {
        **meta,
        "opt_basestock_S": basestock_S,
        "avg_cost_basestock": avg_cost_bs,
        "opt_constant_q": constant_q,
        "avg_cost_constant": avg_cost_c,
    }


def discover_train_test_pairs(base_dir: Path) -> List[Tuple[Path, Path]]:
    """Return (train_path, test_path) pairs matched by filename prefix."""
    train_files = sorted(base_dir.glob("*_train.json"))
    test_set = {p.name: p for p in base_dir.glob("*_test.json")}

    pairs: List[Tuple[Path, Path]] = []
    for tr in train_files:
        te_name = tr.name.replace("_train.json", "_test.json")
        te = test_set.get(te_name)
        if te is None:
            # Per user instruction, pairs always exist; keep a defensive skip.
            print(f"[WARN] Missing test file for train={tr.name}. Skipping.")
            continue
        pairs.append((tr, te))
    return pairs


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Optimize on training sets and evaluate on matching test sets, "
            "under a grid of (lead_time, lost_sales_cost) overrides."
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
        raise FileNotFoundError(f"No *_train.json / *_test.json pairs found in {base_dir}")

    lead_times = [6,8] if args.lead_time is None else [int(args.lead_time)]
    lost_sales_costs = [2, 4, 6, 10] if args.lost_sales_cost is None else [float(args.lost_sales_cost)]

    for L in lead_times:
        for p in lost_sales_costs:
            print("\n==============================")
            print(f"Running configuration: L={L}, lost_sales_cost={p}")
            print("==============================\n")

            results: List[Dict[str, Any]] = []
            for i, (train_path, test_path) in enumerate(pairs, start=1):
                print(f"[{i}/{len(pairs)}] OPTIMIZE on TRAIN {train_path.name}")
                try:
                    train_summary = optimize_on_training_dataset(
                        train_path, lead_time_override=L, lost_sales_cost_override=p
                    )
                    results.append(train_summary)

                    print(f"[{i}/{len(pairs)}] EVALUATE on TEST {test_path.name} (no re-optimization)")
                    test_summary = evaluate_dataset_with_fixed_params(
                        test_path,
                        basestock_S=int(train_summary["opt_basestock_S"]),
                        constant_q=int(train_summary["opt_constant_q"]),
                        lead_time_override=L,
                        lost_sales_cost_override=p,
                    )
                    results.append(test_summary)
                except Exception as e:
                    print(f"[ERROR] Failed on pair train={train_path.name}, test={test_path.name}: {e}")

            df = pd.DataFrame(results)
            csv_path = base_dir / f"basestock_constant_summary_L{L}_p{int(p) if float(p).is_integer() else p}.csv"
            df.to_csv(csv_path, index=False)
            print("\n=== Final summary written to:", csv_path)
            print(df)


if __name__ == "__main__":
    main()
