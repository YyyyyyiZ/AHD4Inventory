"""
evaluate.py  (Pro version, dual outputs)

This script produces TWO CSV outputs:

1) Detailed (long-format, per policy × dataset × split):
   - streamed row-by-row (append)
   - file: policy_generalization_results.csv
   - retains the previous "detailed" structure (including CI columns if enabled)

2) Cost matrix (required final format):
   - each dataset contributes exactly TWO rows: <dataset_id>_train and <dataset_id>_test
   - each policy is a column (policy_id = extracted .py stem)
   - each cell is the average cost only (no CI columns in this file)
   - file: policy_generalization_cost_matrix.csv

Resume behavior
- Detailed CSV: skip (policy_id, dataset_id) if BOTH train and test rows already exist.
- Matrix CSV: skip an entire dataset if BOTH <dataset_id>_train and <dataset_id>_test rows already exist.

Simulation hard constraints (implemented in utils.inventory_sim)
- order_before_sell sequence
- demand padding with L zeros
- planning horizon (first L periods): no demand and NO costs
"""

import argparse
import json
import re
from pathlib import Path
from typing import Dict, Tuple, Set, List, Any

import pandas as pd

from utils.datasets import discover_pairs, load_instances
from utils.tuner_scipy import tune_policy_on_train
from utils.inventory_sim import evaluate_policy
from utils.results_io import load_completed, append_rows


# -------- Config --------
SEED = 0
SCREEN_N = 150

# Detailed output (keeps CI if enabled)
N_BOOTSTRAP = 300  # set 0 to disable CI bootstrap for speed
OUT_CSV_DETAILED = "policy_generalization_results.csv"

# Matrix output (costs only)
OUT_CSV_MATRIX = "cost_matrix_l2.csv"
DATASET_COL = "dataset"  # first column name in matrix CSV

def _safe_id_token(v: Any) -> str:
    """Convert a numeric/str value into a filename-safe token."""
    # Normalize 6.0 -> 6 to keep identifiers clean.
    if isinstance(v, float) and v.is_integer():
        v = int(v)
    s = str(v)
    # Keep alnum, underscore, dash; replace anything else with 'p'
    s = re.sub(r"[^0-9A-Za-z_\-]+", "p", s)
    return s


def _make_effective_dataset_id(base_id: str, lead_time: Any, lost_sales_cost: Any) -> str:
    """
    Build a unique dataset identifier that reflects optional overrides.
    If no overrides are provided, returns base_id unchanged.
    """
    parts: List[str] = []
    if lead_time is not None:
        parts.append(f"L{_safe_id_token(lead_time)}")
    if lost_sales_cost is not None:
        parts.append(f"p{int(_safe_id_token(lost_sales_cost))}")  # 'p' stands for penalty (lost sales cost)
    if not parts:
        return base_id
    return base_id[:-8] + "_" + "_".join(parts)


def _apply_instance_overrides(instances: List[Dict[str, Any]], lead_time: Any, lost_sales_cost: Any) -> None:
    """
    In-place override of selected instance fields.
    Demand data and all other fields remain unchanged.
    """
    if lead_time is None and lost_sales_cost is None:
        return
    for inst in instances:
        if lead_time is not None:
            inst["lead_time"] = int(lead_time)
        if lost_sales_cost is not None:
            inst["lost_sales_cost"] = float(lost_sales_cost)

def _load_cost_map(detailed_csv: Path) -> Dict[Tuple[str, str, str], float]:
    """
    Load (policy_id, dataset_id, split) -> avg_cost from the detailed CSV for fast lookup.
    """
    if not detailed_csv.exists():
        return {}
    df = pd.read_csv(detailed_csv, usecols=["policy_id", "dataset_id", "split", "avg_cost"])
    m: Dict[Tuple[str, str, str], float] = {}
    for row in df.itertuples(index=False):
        m[(str(row.policy_id), str(row.dataset_id), str(row.split))] = float(row.avg_cost)
    return m


def _matrix_completed_datasets(matrix_csv: Path) -> Set[str]:
    """
    A dataset is complete if both "<dataset_id>_train" and "<dataset_id>_test" rows exist.
    """
    if not matrix_csv.exists():
        return set()

    df = pd.read_csv(matrix_csv, usecols=[DATASET_COL], dtype=str)
    if df.empty:
        return set()

    seen = set(df[DATASET_COL].tolist())
    bases = set()
    for r in seen:
        if r.endswith("_train"):
            bases.add(r[:-len("_train")])
        elif r.endswith("_test"):
            bases.add(r[:-len("_test")])

    done = set()
    for b in bases:
        if f"{b}_train" in seen and f"{b}_test" in seen:
            done.add(b)
    return done


def _append_matrix_rows(matrix_csv: Path, policy_ids: List[str], rows: List[Dict[str, Any]]):
    """
    Append rows to the matrix CSV, creating it with the correct header if needed.
    Ensures columns order is [dataset] + policy_ids.
    """
    cols = [DATASET_COL] + policy_ids
    df_new = pd.DataFrame(rows)

    # Ensure all columns exist
    for pid in policy_ids:
        if pid not in df_new.columns:
            df_new[pid] = float("nan")
    if DATASET_COL not in df_new.columns:
        raise ValueError("Matrix row missing dataset column")

    df_new = df_new[cols]

    if not matrix_csv.exists():
        df_new.to_csv(matrix_csv, index=False)
    else:
        df_new.to_csv(matrix_csv, mode="a", header=False, index=False)



def _run_configuration(
    *,
    base_dir: Path,
    data_dir: Path,
    policies_dir: Path,
    datasets: List[Tuple[str, Path, Path]],
    policy_paths: List[Path],
    policy_ids: List[str],
    lead_time_override: int | None,
    lost_sales_cost_override: float | None,
    detailed_csv: Path,
    matrix_csv: Path,
) -> None:
    """
    Run evaluation for a single (lead_time, lost_sales_cost) configuration and write outputs to the given files.
    All overrides are applied in-memory; source JSON files are never modified.
    """
    # Resume helpers (scoped to this configuration's output files)
    done_pairs = load_completed(detailed_csv)  # (policy_id, dataset_id) completed if train+test exist
    cost_map = _load_cost_map(detailed_csv)
    done_datasets_matrix = _matrix_completed_datasets(matrix_csv)

    total_jobs = len(datasets) * len(policy_paths)
    job_idx = 0

    for dataset_id, train_path, test_path in datasets:
        effective_dataset_id = _make_effective_dataset_id(
            dataset_id, lead_time_override, lost_sales_cost_override
        )

        # If matrix already has this dataset's two rows, we assume it is complete.
        if effective_dataset_id in done_datasets_matrix:
            print(f"\n=== Dataset {effective_dataset_id}: SKIP (matrix already complete) ===")
            continue

        train_instances = load_instances(train_path)
        test_instances = load_instances(test_path)

        _apply_instance_overrides(train_instances, lead_time_override, lost_sales_cost_override)
        _apply_instance_overrides(test_instances, lead_time_override, lost_sales_cost_override)

        print(f"\n=== Dataset {effective_dataset_id}: RUN ===")

        train_row = {DATASET_COL: f"{effective_dataset_id}_train"}
        test_row = {DATASET_COL: f"{effective_dataset_id}_test"}

        for pol_path in policy_paths:
            policy_id = pol_path.stem
            job_idx += 1

            # If detailed already has this policy-dataset, reuse costs for matrix
            if (policy_id, effective_dataset_id) in done_pairs:
                train_row[policy_id] = cost_map.get(
                    (policy_id, effective_dataset_id, "train"), float("nan")
                )
                test_row[policy_id] = cost_map.get(
                    (policy_id, effective_dataset_id, "test"), float("nan")
                )
                print(f"[{job_idx}/{total_jobs}] SKIP policy={policy_id} (already in detailed)")
                continue

            print(f"[{job_idx}/{total_jobs}] RUN  policy={policy_id}")

            code = pol_path.read_text(encoding="utf-8")
            try:
                tune_res = tune_policy_on_train(
                    code,
                    train_instances,
                    seed=SEED,
                    screen_n=SCREEN_N,
                )
                tuned_code = tune_res.tuned_code
                tuned_params_json = json.dumps(tune_res.tuned_params, ensure_ascii=False)

                res_train = evaluate_policy(tuned_code, train_instances, seed=SEED, n_bootstrap=N_BOOTSTRAP)
                res_test = evaluate_policy(tuned_code, test_instances, seed=SEED, n_bootstrap=N_BOOTSTRAP)

                # Detailed rows: append immediately (for resume robustness)
                detailed_rows = [
                    {
                        "policy_id": policy_id,
                        "dataset_id": effective_dataset_id,
                        "split": "train",
                        "avg_cost": res_train["avg"],
                        "ci_lower": res_train["lower"],
                        "ci_upper": res_train["upper"],
                        "tune_status": tune_res.status,
                        "tune_train_avg": tune_res.train_avg,
                        "tuned_params": tuned_params_json,
                        "error": "",
                    },
                    {
                        "policy_id": policy_id,
                        "dataset_id": effective_dataset_id,
                        "split": "test",
                        "avg_cost": res_test["avg"],
                        "ci_lower": res_test["lower"],
                        "ci_upper": res_test["upper"],
                        "tune_status": tune_res.status,
                        "tune_train_avg": tune_res.train_avg,
                        "tuned_params": tuned_params_json,
                        "error": "",
                    },
                ]
                append_rows(detailed_csv, detailed_rows)

                # Update state
                done_pairs.add((policy_id, effective_dataset_id))
                cost_map[(policy_id, effective_dataset_id, "train")] = float(res_train["avg"])
                cost_map[(policy_id, effective_dataset_id, "test")] = float(res_test["avg"])

                # Matrix cells
                train_row[policy_id] = float(res_train["avg"])
                test_row[policy_id] = float(res_test["avg"])

            except Exception as e:
                detailed_rows = [
                    {
                        "policy_id": policy_id,
                        "dataset_id": effective_dataset_id,
                        "split": "train",
                        "avg_cost": float("nan"),
                        "ci_lower": float("nan"),
                        "ci_upper": float("nan"),
                        "tune_status": "failed",
                        "tune_train_avg": float("nan"),
                        "tuned_params": "",
                        "error": str(e),
                    },
                    {
                        "policy_id": policy_id,
                        "dataset_id": effective_dataset_id,
                        "split": "test",
                        "avg_cost": float("nan"),
                        "ci_lower": float("nan"),
                        "ci_upper": float("nan"),
                        "tune_status": "failed",
                        "tune_train_avg": float("nan"),
                        "tuned_params": "",
                        "error": str(e),
                    },
                ]
                append_rows(detailed_csv, detailed_rows)

                done_pairs.add((policy_id, effective_dataset_id))
                cost_map[(policy_id, effective_dataset_id, "train")] = float("nan")
                cost_map[(policy_id, effective_dataset_id, "test")] = float("nan")

                train_row[policy_id] = float("nan")
                test_row[policy_id] = float("nan")

        # After all policies for this dataset, append the two matrix rows
        _append_matrix_rows(matrix_csv, policy_ids, [train_row, test_row])
        done_datasets_matrix.add(effective_dataset_id)
        print(f"[OK] Dataset {effective_dataset_id}: appended 2 rows to {matrix_csv.name}")


def main(argv: List[str] | None = None):
    base_dir = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(
        description=(
            "Evaluate extracted inventory policies across paired JSON datasets, producing a detailed CSV "
            "and a cost-matrix CSV. If --lead_time/--lost_sales_cost are omitted, runs a 4x4 sweep grid "
            "over lead_time ∈ {2,4,6,8} and lost_sales_cost ∈ {2,4,6,10} and writes separate output files per configuration."
        )
    )
    parser.add_argument(
        "--lead_time",
        type=int,
        default=None,
        help="Override instance lead_time (single-run mode). If omitted, grid-sweep mode is used.",
    )
    parser.add_argument(
        "--lost_sales_cost",
        type=float,
        default=None,
        help="Override instance lost_sales_cost (single-run mode). If omitted, grid-sweep mode is used.",
    )
    args = parser.parse_args(argv)

    data_dir = base_dir.parent / "generalize"
    policies_dir = base_dir / "pops_best" / "extracted"

    if not data_dir.exists():
        raise FileNotFoundError(f"Missing data dir: {data_dir}")
    if not policies_dir.exists():
        raise FileNotFoundError(f"Missing policy dir: {policies_dir} (run extract_code.py first)")

    datasets = discover_pairs(data_dir)
    if not datasets:
        raise FileNotFoundError(f"No paired *_train/_test datasets found in {data_dir}")

    policy_paths = sorted(policies_dir.glob("*.py"))
    if not policy_paths:
        raise FileNotFoundError(f"No extracted policies found in {policies_dir}")

    policy_ids = [p.stem for p in policy_paths]

    # Decide run mode:
    # - If either override is specified => single configuration (uses existing default filenames).
    # - Otherwise => sweep the fixed 4×4 grid and write separate outputs per configuration.
    if args.lead_time is not None or args.lost_sales_cost is not None:
        lead_time_override = args.lead_time
        lost_sales_cost_override = args.lost_sales_cost

        detailed_csv = base_dir / OUT_CSV_DETAILED
        matrix_csv = base_dir / OUT_CSV_MATRIX

        print("\n=== RUN MODE: single configuration ===")
        print(f"lead_time_override={lead_time_override}, lost_sales_cost_override={lost_sales_cost_override}")
        print(f"Detailed CSV: {detailed_csv}")
        print(f"Matrix CSV:   {matrix_csv}")

        _run_configuration(
            base_dir=base_dir,
            data_dir=data_dir,
            policies_dir=policies_dir,
            datasets=datasets,
            policy_paths=policy_paths,
            policy_ids=policy_ids,
            lead_time_override=lead_time_override,
            lost_sales_cost_override=lost_sales_cost_override,
            detailed_csv=detailed_csv,
            matrix_csv=matrix_csv,
        )
        print(f"\nDone.\n- Detailed: {detailed_csv}\n- Matrix:   {matrix_csv}")
        return

    # Grid sweep mode
    lead_times = [2, 4, 6, 8]  # feng: [2, 4] ; yi:[6, 8]
    cost_ratios = [2, 4, 6, 10]

    print("\n=== RUN MODE: grid sweep (16 configurations) ===")
    print(f"lead_time grid: {lead_times}")
    print(f"lost_sales_cost grid: {cost_ratios}")

    for L in lead_times:
        for p in cost_ratios:
            detailed_csv = base_dir / f"policy_generalization_results_L{L}_p{_safe_id_token(p)}.csv"
            matrix_csv = base_dir / f"cost_matrix_L{L}_p{_safe_id_token(p)}.csv"

            print("\n" + "=" * 80)
            print(f"CONFIG: lead_time={L}, lost_sales_cost={p}")
            print(f"Detailed CSV: {detailed_csv.name}")
            print(f"Matrix CSV:   {matrix_csv.name}")
            print("=" * 80)

            _run_configuration(
                base_dir=base_dir,
                data_dir=data_dir,
                policies_dir=policies_dir,
                datasets=datasets,
                policy_paths=policy_paths,
                policy_ids=policy_ids,
                lead_time_override=L,
                lost_sales_cost_override=float(p),
                detailed_csv=detailed_csv,
                matrix_csv=matrix_csv,
            )

    print("\nAll configurations completed.")
    print(f"Output directory: {base_dir}")


if __name__ == "__main__":
    main()

