#!/usr/bin/env python3
# plot_hist_by_p_combined.py
# For each policy and split, aggregate all L values for a given p into a single histogram.
#
# Example:
#   python plot_hist_by_p_combined.py --splits both --baseline-cols avg_cost_basestock
#
# Outputs:
#   histograms_by_p_combined/<split>/<policy>/p{p}.png
#   histograms_by_p_combined/<split>/hist_summary.csv

from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


DATASET_COL = "dataset"
SOURCE_FILE_COL = "source_file"


def normalize_dataset_id(s: str) -> str:
    return re.sub(r"\.json$", "", str(s))


def build_join_id_from_source_file(source_file: str, L: int, p_str: str) -> str:
    s = normalize_dataset_id(source_file)
    s2, n = re.subn(r"_L\d+_c\d+_\d+_", f"_L{L}_p{p_str}_", s)
    return s2 if n else s


def coerce_numeric(df: pd.DataFrame, cols: List[str]) -> pd.DataFrame:
    for c in cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    return df


def percent_reduction(policy_cost: np.ndarray, baseline_cost: np.ndarray) -> np.ndarray:
    b = baseline_cost.astype(float)
    p = policy_cost.astype(float)
    out = np.full_like(b, np.nan, dtype=float)
    mask = np.isfinite(b) & np.isfinite(p) & (b > 1e-12)
    out[mask] = 100.0 * (b[mask] - p[mask]) / b[mask]
    return out


def robust_xlim_include_zero(
    x: np.ndarray,
    q_lo: float = 0.01,
    q_hi: float = 0.99,
    symmetric: bool = False
) -> Tuple[float, float] | None:
    x = x[np.isfinite(x)]
    if x.size < 20:
        if x.size == 0:
            return None
        lo, hi = float(np.min(x)), float(np.max(x))
        lo = min(lo, 0.0)
        hi = max(hi, 0.0)
        if lo == hi:
            lo -= 1.0
            hi += 1.0
        return lo, hi

    lo = float(np.quantile(x, q_lo))
    hi = float(np.quantile(x, q_hi))
    lo = min(lo, 0.0)
    hi = max(hi, 0.0)

    if symmetric:
        m = max(abs(lo), abs(hi))
        if m <= 0:
            m = 1.0
        return -m, m

    if lo == hi:
        lo -= 1.0
        hi += 1.0
    return lo, hi


def summarize(values: np.ndarray) -> Dict[str, float]:
    v = values[np.isfinite(values)]
    n = int(v.size)
    if n == 0:
        return {
            "n_valid": 0,
            "mean": np.nan,
            "median": np.nan,
            "pct_pos": np.nan,
            "pct_zero": np.nan,
            "pct_neg": np.nan,
        }
    mean = float(np.mean(v))
    median = float(np.median(v))
    pct_pos = float(np.mean(v > 0.0) * 100.0)
    pct_zero = float(np.mean(v == 0.0) * 100.0)
    pct_neg = float(np.mean(v < 0.0) * 100.0)
    return {
        "n_valid": n,
        "mean": mean,
        "median": median,
        "pct_pos": pct_pos,
        "pct_zero": pct_zero,
        "pct_neg": pct_neg,
    }


def matches_split(dataset: str, split: str) -> bool:
    ds = str(dataset)
    return bool(re.search(rf"_{re.escape(split)}(\.json)?$", ds))


def discover_cost_files(cost_dir: Path) -> List[Tuple[Path, int, str]]:
    out = []
    pat = re.compile(r"^cost_matrix_L(?P<L>\d+)_p(?P<p>[0-9]+(?:\.[0-9]+)?)\.csv$")
    for f in sorted(cost_dir.iterdir()):
        if not f.is_file():
            continue
        m = pat.match(f.name)
        if not m:
            continue
        out.append((f, int(m.group("L")), m.group("p")))
    return out


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--splits",
        type=str,
        default="both",
        choices=["train", "test", "both"],
        help="Which split(s) to plot."
    )
    parser.add_argument(
        "--baseline-cols",
        type=str,
        default="avg_cost_basestock",
        help="Comma-separated baseline column names from basestock_constant_summary_*.csv."
    )
    parser.add_argument(
        "--policies",
        type=str,
        default="normal,poisson,exponential",
        help="Comma-separated policy prefixes to include."
    )
    parser.add_argument("--bins", type=int, default=40)
    parser.add_argument(
        "--robust",
        action="store_true",
        help="Use robust x-limits based on quantiles (still includes 0)."
    )
    parser.add_argument(
        "--symmetric",
        action="store_true",
        help="Force symmetric x-limits around 0."
    )
    parser.add_argument(
        "--generalize-dir",
        type=str,
        default=None,
        help="Path to generalize folder. Default: sibling 'generalize' next to the cost dir."
    )
    args = parser.parse_args()

    here = Path(__file__).resolve().parent
    cost_dir = here
    generalize_dir = Path(args.generalize_dir).resolve() if args.generalize_dir else (here.parent / "generalize")

    baseline_cols = [c.strip() for c in args.baseline_cols.split(",") if c.strip()]
    if not baseline_cols:
        raise ValueError("No baseline columns specified. Use --baseline-cols col1,col2,...")

    policy_groups = [c.strip() for c in args.policies.split(",") if c.strip()]
    if not policy_groups:
        raise ValueError("No policies specified. Use --policies p1,p2,...")

    splits = ["train", "test"] if args.splits == "both" else [args.splits]

    cost_files = discover_cost_files(cost_dir)
    if not cost_files:
        raise FileNotFoundError(f"No cost_matrix_L{{L}}_p{{p}}.csv files found in: {cost_dir}")
    if not generalize_dir.exists():
        raise FileNotFoundError(f"generalize directory not found: {generalize_dir}")

    try:
        color_cycle = plt.rcParams["axes.prop_cycle"].by_key().get("color", [])
    except Exception:
        color_cycle = []
    if not color_cycle:
        color_cycle = [f"C{i}" for i in range(10)]

    agg: Dict[str, Dict[str, Dict[str, List[np.ndarray]]]] = {
        split: {policy: {} for policy in policy_groups} for split in splits
    }
    n_rows: Dict[str, Dict[str, Dict[str, int]]] = {
        split: {policy: {} for policy in policy_groups} for split in splits
    }

    n_pairs_used = 0
    n_pairs_skipped = 0

    for cost_path, L, p_str in cost_files:
        summary_name = f"basestock_constant_summary_L{L}_p{p_str}.csv"
        summary_path = generalize_dir / summary_name
        if not summary_path.exists():
            print(f"[SKIP] No matching summary file for {cost_path.name}: expected {summary_path}")
            n_pairs_skipped += 1
            continue

        cost_df = pd.read_csv(cost_path)
        if DATASET_COL not in cost_df.columns:
            cost_df = cost_df.rename(columns={cost_df.columns[0]: DATASET_COL})

        sum_df = pd.read_csv(summary_path)
        if DATASET_COL not in sum_df.columns:
            sum_df = sum_df.rename(columns={sum_df.columns[0]: DATASET_COL})

        if SOURCE_FILE_COL in sum_df.columns:
            sum_df["_join_id"] = sum_df[SOURCE_FILE_COL].astype(str).map(
                lambda s: build_join_id_from_source_file(s, L, p_str)
            )
        else:
            sum_df["_join_id"] = sum_df[DATASET_COL].astype(str).map(normalize_dataset_id)

        missing_in_summary = [c for c in baseline_cols if c not in sum_df.columns]
        if missing_in_summary:
            print(f"[SKIP] Missing baseline columns in {summary_path.name}: {missing_in_summary}")
            n_pairs_skipped += 1
            continue

        sum_keep = sum_df[["_join_id"] + baseline_cols].copy()
        df = cost_df.merge(sum_keep, left_on=DATASET_COL, right_on="_join_id", how="left")
        if "_join_id" in df.columns:
            df = df.drop(columns=["_join_id"])

        policy_cols = [c for c in cost_df.columns if c != DATASET_COL]
        if not policy_cols:
            print(f"[SKIP] No policy columns found in {cost_path.name}")
            n_pairs_skipped += 1
            continue

        df = coerce_numeric(df, baseline_cols + policy_cols)

        for split in splits:
            df_split = df[df[DATASET_COL].astype(str).apply(lambda s: matches_split(s, split))].copy()
            if df_split.empty:
                continue

            for policy in policy_groups:
                matching_cols = [c for c in policy_cols if c.startswith(policy)]
                if not matching_cols:
                    continue

                pr_all = []
                for col in matching_cols:
                    p_cost = df_split[col].to_numpy(dtype=float)
                    pr = percent_reduction(p_cost, df_split[baseline_cols[0]].to_numpy(dtype=float))
                    pr_all.append(pr)

                if not pr_all:
                    continue

                agg[split][policy].setdefault(p_str, []).append(np.concatenate(pr_all))
                n_rows[split][policy][p_str] = n_rows[split][policy].get(p_str, 0) + int(len(df_split))

        n_pairs_used += 1

    for split in splits:
        out_dir = here / "histograms_by_p_combined" / split
        out_dir.mkdir(parents=True, exist_ok=True)
        summary_rows = []

        for policy in policy_groups:
            for p_str, chunks in sorted(agg[split][policy].items(), key=lambda x: float(x[0])):
                pr = np.concatenate(chunks) if chunks else np.array([])
                stats = summarize(pr)
                total_rows = n_rows[split][policy].get(p_str, 0)

                fig, ax = plt.subplots(figsize=(9, 4))
                x = pr[np.isfinite(pr)]
                ax.hist(
                    x,
                    bins=args.bins,
                    color=color_cycle[0],
                    alpha=0.75,
                    edgecolor="white",
                    linewidth=0.6,
                )
                ax.axvline(0.0, color="black", linewidth=1.0, linestyle="-")
                if np.isfinite(stats["mean"]):
                    ax.axvline(stats["mean"], color="black", linewidth=1.0, linestyle="--")
                ax.grid(True, linestyle="--", linewidth=0.5, alpha=0.4)
                ax.set_ylabel("Count")
                ax.set_xlabel("% cost reduction (baseline - policy) / baseline × 100")
                ax.set_title(
                    f"{policy} | Split: {split} | p={p_str} (all L) | "
                    f"mean={stats['mean']:.2f}% | pos={stats['pct_pos']:.1f}% | "
                    f"zero={stats['pct_zero']:.1f}% | neg={stats['pct_neg']:.1f}% | "
                    f"n_valid={stats['n_valid']}/{total_rows}",
                    fontsize=9,
                )

                if args.robust:
                    lim = robust_xlim_include_zero(pr, symmetric=args.symmetric)
                    if lim is not None:
                        ax.set_xlim(lim[0], lim[1])
                elif args.symmetric:
                    lim = robust_xlim_include_zero(pr, symmetric=True)
                    if lim is not None:
                        ax.set_xlim(lim[0], lim[1])

                fig.tight_layout()
                fig_path = out_dir / f"{policy}__p{p_str}.png"
                fig.savefig(fig_path, dpi=180)
                plt.close(fig)

                summary_rows.append({
                    "policy": policy,
                    "split": split,
                    "p": p_str,
                    "mean_%": stats["mean"],
                    "median_%": stats["median"],
                    "pct_pos_%": stats["pct_pos"],
                    "pct_zero_%": stats["pct_zero"],
                    "pct_neg_%": stats["pct_neg"],
                    "n_rows_total": int(total_rows),
                    "n_valid": int(stats["n_valid"]),
                    "n_missing_or_invalid": int(total_rows - stats["n_valid"]),
                })

        summary_path = out_dir / "hist_summary.csv"
        pd.DataFrame(summary_rows).to_csv(summary_path, index=False)
        print(f"[OK] {summary_path}")

    print("\nDone.")
    print(f"Pairs processed: {n_pairs_used} | Pairs skipped: {n_pairs_skipped}")
    print(f"generalize dir: {generalize_dir}")
    print(f"baseline cols: {baseline_cols}")
    print(f"policies: {policy_groups}")
    print(f"splits: {splits}")


if __name__ == "__main__":
    main()
