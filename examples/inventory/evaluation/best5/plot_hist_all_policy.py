#!/usr/bin/env python3
# plot_hist_all_policy.py
# Aggregate all (L, p) cost matrices into a single histogram per policy and split.
#
# Example:
#   python plot_hist_all_policy.py --splits both --baseline-cols avg_cost_basestock
#
# Outputs:
#   histograms_all_lp/<split>/<policy>__Khists.png
#   histograms_all_lp/<split>/hist_summary.csv

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
    """Strip a trailing '.json' if present (only at the end)."""
    s = str(s)
    return re.sub(r"\.json$", "", s)


def build_join_id_from_source_file(source_file: str, L: int, p_str: str) -> str:
    """Build the cost-matrix-style dataset id from a summary row's source_file."""
    s = normalize_dataset_id(source_file)
    s2, n = re.subn(r"_L\d+_c\d+_\d+_", f"_L{L}_p{p_str}_", s)
    if n == 0:
        return s
    return s2


def coerce_numeric(df: pd.DataFrame, cols: List[str]) -> pd.DataFrame:
    """Convert columns to numeric; blanks/non-numeric -> NaN."""
    for c in cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    return df


def percent_reduction(policy_cost: np.ndarray, baseline_cost: np.ndarray) -> np.ndarray:
    """
    % cost reduction relative to baseline:
        100 * (baseline - policy) / baseline
    Positive => policy better than baseline; Negative => worse.
    """
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
    """Robust x-limits that include 0. Optionally symmetric around 0."""
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
            "pct_neg": np.nan,
            "pct_zero": np.nan,
        }
    mean = float(np.mean(v))
    median = float(np.median(v))
    pct_pos = float(np.mean(v > 0.0) * 100.0)
    pct_neg = float(np.mean(v < 0.0) * 100.0)
    pct_zero = float(np.mean(v == 0.0) * 100.0)
    return {
        "n_valid": n,
        "mean": mean,
        "median": median,
        "pct_pos": pct_pos,
        "pct_neg": pct_neg,
        "pct_zero": pct_zero,
    }


def matches_split(dataset: str, split: str) -> bool:
    """Accept both ..._train and ..._train.json (same for test)."""
    ds = str(dataset)
    return bool(re.search(rf"_{re.escape(split)}(\.json)?$", ds))


def safe_filename(name: str) -> str:
    """Make a string safe to use as a filename."""
    name = str(name)
    name = name.replace("/", "_").replace("\\", "_")
    name = re.sub(r"\s+", "_", name).strip("_")
    return name


def discover_cost_files(cost_dir: Path) -> List[Tuple[Path, int, str]]:
    """
    Return list of (path, L, p_str) for files matching cost_matrix_L{L}_p{p}.csv
    where p can be integer or float-like (e.g., 2, 2.0, 10).
    """
    out = []
    pat = re.compile(r"^cost_matrix_L(?P<L>\d+)_p(?P<p>[0-9]+(?:\.[0-9]+)?)\.csv$")
    for f in sorted(cost_dir.iterdir()):
        if not f.is_file():
            continue
        m = pat.match(f.name)
        if not m:
            continue
        L = int(m.group("L"))
        p_str = m.group("p")
        out.append((f, L, p_str))
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
        help="Comma-separated column names (from basestock_constant_summary_*.csv) to use as baselines."
    )
    parser.add_argument(
        "--policies",
        type=str,
        default="normal,poisson,exponential",
        help="Comma-separated policy column names to include. Default: normal,poisson,exponential."
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
        help="Force symmetric x-limits around 0 (good for showing +/-)."
    )
    parser.add_argument(
        "--generalize-dir",
        type=str,
        default=None,
        help="Path to the generalize folder. Default: sibling 'generalize' next to the cost dir."
    )
    args = parser.parse_args()

    here = Path(__file__).resolve().parent
    cost_dir = here
    generalize_dir = Path(args.generalize_dir).resolve() if args.generalize_dir else (here.parent / "generalize")

    baseline_cols = [c.strip() for c in args.baseline_cols.split(",") if c.strip()]
    if not baseline_cols:
        raise ValueError("No baseline columns specified. Use --baseline-cols col1,col2,...")

    if args.splits == "both":
        splits = ["train", "test"]
    else:
        splits = [args.splits]

    policy_groups = [c.strip() for c in args.policies.split(",") if c.strip()]
    if not policy_groups:
        raise ValueError("No policies specified. Use --policies p1,p2,...")

    cost_files = discover_cost_files(cost_dir)
    if not cost_files:
        raise FileNotFoundError(f"No cost_matrix_L{{L}}_p{{p}}.csv files found in: {cost_dir}")

    if not generalize_dir.exists():
        raise FileNotFoundError(f"generalize directory not found: {generalize_dir}")

    agg: Dict[str, Dict[str, Dict[str, List[np.ndarray]]]] = {
        split: {p: {b: [] for b in baseline_cols} for p in policy_groups} for split in splits
    }
    n_rows_by_policy: Dict[str, Dict[str, int]] = {split: {p: 0 for p in policy_groups} for split in splits}

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
                for col in matching_cols:
                    p_cost = df_split[col].to_numpy(dtype=float)
                    for baseline in baseline_cols:
                        pr = percent_reduction(p_cost, df_split[baseline].to_numpy(dtype=float))
                        agg[split][policy][baseline].append(pr)
                    n_rows_by_policy[split][policy] += int(len(df_split))

        n_pairs_used += 1

    for split in splits:
        out_dir = here / "histograms_all_lp" / split
        out_dir.mkdir(parents=True, exist_ok=True)

        summary_rows = []
        try:
            color_cycle = plt.rcParams["axes.prop_cycle"].by_key().get("color", [])
        except Exception:
            color_cycle = []
        if not color_cycle:
            color_cycle = [f"C{i}" for i in range(10)]

        for policy in policy_groups:
            if all(len(agg[split][policy][b]) == 0 for b in baseline_cols):
                print(f"[WARN] No data for policy='{policy}' in split='{split}'.")
                continue

            K = len(baseline_cols)
            fig_h = 3.0 * K + 1.0
            fig, axes = plt.subplots(nrows=K, ncols=1, figsize=(9, fig_h), sharex=False)
            axes = np.atleast_1d(axes).ravel()

            fig.suptitle(
                f"{policy} — % Cost Reduction (positive = better, negative = worse)\n"
                f"Split: {split} | All L,p combined",
                fontsize=13
            )

            n_rows = n_rows_by_policy[split][policy]
            for i, baseline in enumerate(baseline_cols):
                ax = axes[i]
                color = color_cycle[i % len(color_cycle)]
                pr = np.concatenate(agg[split][policy][baseline]) if agg[split][policy][baseline] else np.array([])
                stats = summarize(pr)

                x = pr[np.isfinite(pr)]
                ax.hist(
                    x,
                    bins=args.bins,
                    color=color,
                    alpha=0.75,
                    edgecolor="white",
                    linewidth=0.6,
                )
                ax.axvline(0.0, color="black", linewidth=1.0, linestyle="-")
                if np.isfinite(stats["mean"]):
                    ax.axvline(stats["mean"], color="black", linewidth=1.0, linestyle="--")

                ax.grid(True, linestyle="--", linewidth=0.5, alpha=0.4)
                ax.set_ylabel("Count")
                ax.set_title(
                    f"vs {baseline} | mean={stats['mean']:.2f}% | pos={stats['pct_pos']:.1f}% | "
                    f"zero={stats['pct_zero']:.1f}% | neg={stats['pct_neg']:.1f}% | "
                    f"n_valid={stats['n_valid']}/{n_rows}",
                    fontsize=11,
                )
                ax.set_xlabel("% cost reduction (baseline - policy) / baseline × 100")

                if args.robust:
                    lim = robust_xlim_include_zero(pr, symmetric=args.symmetric)
                    if lim is not None:
                        ax.set_xlim(lim[0], lim[1])
                elif args.symmetric:
                    lim = robust_xlim_include_zero(pr, symmetric=True)
                    if lim is not None:
                        ax.set_xlim(lim[0], lim[1])

                summary_rows.append({
                    "policy": policy,
                    "split": split,
                    "baseline": baseline,
                    "mean_%": stats["mean"],
                    "median_%": stats["median"],
                    "pct_pos_%": stats["pct_pos"],
                    "pct_neg_%": stats["pct_neg"],
                    "pct_zero_%": stats["pct_zero"],
                    "n_rows_total": int(n_rows),
                    "n_valid": int(stats["n_valid"]),
                    "n_missing_or_invalid": int(n_rows - stats["n_valid"]),
                })

            fig.tight_layout(rect=[0, 0.0, 1, 0.95])
            fig_path = out_dir / f"{safe_filename(policy)}__{K}hists.png"
            fig.savefig(fig_path, dpi=180)
            plt.close(fig)
            print(f"[OK] {fig_path}")

        summary_df = pd.DataFrame(summary_rows)
        summary_path = out_dir / "hist_summary.csv"
        summary_df.to_csv(summary_path, index=False)
        print(f"[OK] {summary_path}")

    print("\nDone.")
    print(f"Pairs processed: {n_pairs_used} | Pairs skipped: {n_pairs_skipped}")
    print(f"generalize dir: {generalize_dir}")
    print(f"baseline cols: {baseline_cols}")
    print(f"policies: {policy_groups}")
    print(f"splits: {splits}")


if __name__ == "__main__":
    main()
