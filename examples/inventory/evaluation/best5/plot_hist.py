# plot_hist.py
# Place this file in the SAME directory as the cost_matrix_L{L}_p{p}.csv files (e.g., best5/).
#
# It will automatically find matching pairs:
#   - best5/cost_matrix_L{L}_p{p}.csv
#   - generalize/basestock_constant_summary_L{L}_p{p}.csv    (generalize is a sibling folder of best5)
#
# For each matched (L, p) pair and for each requested split (train/test),
# the script merges baseline columns from the summary CSV into the cost matrix CSV
# (keyed by the dataset id, stripping a trailing ".json" in the summary dataset field),
# then plots histograms of "% cost reduction vs each baseline" for every policy column,
# using the same plotting logic as the original script.
#
# Example:
#   python plot_hist.py --splits both --baseline-cols avg_cost_basestock,avg_cost_constant
#
# Outputs (for each (L,p) and split):
#   histograms/<split>/L{L}_p{p}/<policy>__Khists.png
#   histograms/<split>/L{L}_p{p}/hist_summary.csv

from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


DATASET_COL = "dataset"
SOURCE_FILE_COL = "source_file"


def normalize_dataset_id(s: str) -> str:
    """Strip a trailing '.json' if present (only at the end)."""
    s = str(s)
    return re.sub(r"\.json$", "", s)


def build_join_id_from_source_file(source_file: str, L: int, p_str: str) -> str:
    """Build the cost-matrix-style dataset id from a summary row's source_file.

    Expected source_file format (example):
        beta_a0p5_b0p5_M20_L6_c1_2_train.json

    Expected cost_matrix dataset id format (example):
        beta_a0p5_b0p5_M20_L6_p2_train

    Key requirement: the rewrite must be *anchored* at the lead-time/cost token
    ("_L{digit}_c{digit}_{digit}_") so that distribution parameters like
    "binom_n100_p0p05" are not accidentally modified.
    """
    s = normalize_dataset_id(source_file)
    # Replace the "_L{old}_c{a}_{b}_" token with the target "_L{L}_p{p}_" token.
    s2, n = re.subn(r"_L\d+_c\d+_\d+_", f"_L{L}_p{p_str}_", s)
    if n == 0:
        # Fall back to the normalized string if the expected token is missing.
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
        }
    mean = float(np.mean(v))
    median = float(np.median(v))
    pct_pos = float(np.mean(v > 0.0) * 100.0)
    pct_neg = float(np.mean(v < 0.0) * 100.0)
    return {"n_valid": n, "mean": mean, "median": median, "pct_pos": pct_pos, "pct_neg": pct_neg}


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
        default="avg_cost_basestock,avg_cost_constant",
        help="Comma-separated column names (from basestock_constant_summary_*.csv) to use as baselines."
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

    cost_files = discover_cost_files(cost_dir)
    if not cost_files:
        raise FileNotFoundError(f"No cost_matrix_L{{L}}_p{{p}}.csv files found in: {cost_dir}")

    if not generalize_dir.exists():
        raise FileNotFoundError(f"generalize directory not found: {generalize_dir}")

    n_pairs_used = 0
    n_pairs_skipped = 0

    for cost_path, L, p_str in cost_files:
        summary_name = f"basestock_constant_summary_L{L}_p{p_str}.csv"
        summary_path = generalize_dir / summary_name
        if not summary_path.exists():
            print(f"[SKIP] No matching summary file for {cost_path.name}: expected {summary_path}")
            n_pairs_skipped += 1
            continue

        # Read cost matrix
        cost_df = pd.read_csv(cost_path)
        if DATASET_COL not in cost_df.columns:
            # Fallback: rename first column to dataset
            cost_df = cost_df.rename(columns={cost_df.columns[0]: DATASET_COL})

        # Read summary, keep only dataset + baselines
        sum_df = pd.read_csv(summary_path)
        if DATASET_COL not in sum_df.columns:
            sum_df = sum_df.rename(columns={sum_df.columns[0]: DATASET_COL})

        # Build a robust join id for the summary rows.
        # Preferred: derive from source_file (more unique; avoids collisions in summary 'dataset').
        # Fallback: normalize summary 'dataset' by stripping a trailing .json.
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

        # Merge baselines into cost matrix (left join, keyed by cost_df.dataset = sum_df._join_id)
        df = cost_df.merge(sum_keep, left_on=DATASET_COL, right_on="_join_id", how="left")
        if "_join_id" in df.columns:
            df = df.drop(columns=["_join_id"])

        # Diagnostics: how many rows got baselines?
        matched_all = df[baseline_cols].notna().all(axis=1)
        n_total = int(len(df))
        n_matched = int(matched_all.sum())
        if n_total > 0:
            if n_matched < n_total:
                ex = df.loc[~matched_all, DATASET_COL].astype(str).head(5).tolist()
                print(
                    f"[JOIN] {cost_path.name} <- {summary_path.name}: matched {n_matched}/{n_total} rows "
                    f"({n_matched/n_total:.1%}). Example unmatched dataset ids: {ex}"
                )
            else:
                print(f"[JOIN] {cost_path.name} <- {summary_path.name}: matched {n_matched}/{n_total} rows (100%).")

        # Identify policy columns (everything except dataset and baselines)
        policy_cols = [c for c in cost_df.columns if c != DATASET_COL]
        if not policy_cols:
            print(f"[SKIP] No policy columns found in {cost_path.name}")
            n_pairs_skipped += 1
            continue

        # Coerce numeric for baselines and policies
        df = coerce_numeric(df, baseline_cols + policy_cols)

        # Loop splits
        for split in splits:
            df_split = df[df[DATASET_COL].astype(str).apply(lambda s: matches_split(s, split))].copy()
            if df_split.empty:
                print(f"[WARN] No rows for split='{split}' in {cost_path.name} after filtering; skipping this split.")
                continue

            # Ensure baselines exist (and not all NaN)
            baseline_arr = {b: df_split[b].to_numpy(dtype=float) for b in baseline_cols}
            n_rows = len(df_split)

            K = len(baseline_cols)
            out_dir = here / "histograms" / split / f"L{L}_p{p_str}"
            out_dir.mkdir(parents=True, exist_ok=True)

            summary_rows = []

            # Colors: use Matplotlib's default cycle so each subplot uses a distinct color.
            try:
                color_cycle = plt.rcParams["axes.prop_cycle"].by_key().get("color", [])
            except Exception:
                color_cycle = []
            if not color_cycle:
                color_cycle = [f"C{i}" for i in range(10)]

            # Make plots policy-by-policy (one figure contains K histograms)
            for policy in policy_cols:
                p_cost = df_split[policy].to_numpy(dtype=float)

                # Dynamic subplots based on K
                fig_h = 3.0 * K + 1.0
                fig, axes = plt.subplots(nrows=K, ncols=1, figsize=(9, fig_h), sharex=False)
                axes = np.atleast_1d(axes).ravel()

                fig.suptitle(
                    f"{policy} — % Cost Reduction (positive = better, negative = worse)\n"
                    f"Split: {split} | L={L}, p={p_str}",
                    fontsize=13
                )

                for i, baseline in enumerate(baseline_cols):
                    ax = axes[i]
                    color = color_cycle[i % len(color_cycle)]
                    pr = percent_reduction(p_cost, baseline_arr[baseline])
                    stats = summarize(pr)

                    x = pr[np.isfinite(pr)]

                    # Histogram (keep the same default style logic; do not assume colors exist)
                    ax.hist(
                        x,
                        bins=args.bins,
                        color=color,
                        alpha=0.75,
                        edgecolor="white",
                        linewidth=0.6,
                    )

                    # Zero line to show +/- explicitly
                    ax.axvline(0.0, color="black", linewidth=1.0, linestyle="-")

                    # Mean line (if exists)
                    if np.isfinite(stats["mean"]):
                        ax.axvline(stats["mean"], color="black", linewidth=1.0, linestyle="--")

                    # Aesthetics
                    ax.grid(True, linestyle="--", linewidth=0.5, alpha=0.4)
                    ax.set_ylabel("Count")
                    ax.set_title(
                        f"vs {baseline} | mean={stats['mean']:.2f}% | pos={stats['pct_pos']:.1f}% | "
                        f"neg={stats['pct_neg']:.1f}% | n_valid={stats['n_valid']}/{n_rows}",
                        fontsize=11,
                    )

                    ax.set_xlabel("% cost reduction (baseline - policy) / baseline × 100")

                    # X-limits
                    if args.robust:
                        lim = robust_xlim_include_zero(pr, symmetric=args.symmetric)
                        if lim is not None:
                            ax.set_xlim(lim[0], lim[1])
                    elif args.symmetric:
                        lim = robust_xlim_include_zero(pr, symmetric=True)
                        if lim is not None:
                            ax.set_xlim(lim[0], lim[1])

                    # Summary row
                    summary_rows.append({
                        "policy": policy,
                        "split": split,
                        "L": L,
                        "p": p_str,
                        "baseline": baseline,
                        "mean_%": stats["mean"],
                        "median_%": stats["median"],
                        "pct_pos_%": stats["pct_pos"],
                        "pct_neg_%": stats["pct_neg"],
                        "n_rows_total": int(n_rows),
                        "n_valid": int(stats["n_valid"]),
                        "n_missing_or_invalid": int(n_rows - stats["n_valid"]),
                    })

                fig.tight_layout(rect=[0, 0.0, 1, 0.95])
                fig_path = out_dir / f"{safe_filename(policy)}__{K}hists.png"
                fig.savefig(fig_path, dpi=180)
                plt.close(fig)

            # Write per-(L,p,split) summary CSV into the same folder
            summary_df = pd.DataFrame(summary_rows)
            summary_path = out_dir / "hist_summary.csv"
            summary_df.to_csv(summary_path, index=False)

            print(f"[OK] {cost_path.name} + {summary_path.name} ({split})")
            print(f"     Figures: {out_dir} | Policies: {len(policy_cols)} | Rows used: {n_rows}")

        n_pairs_used += 1

    print("\nDone.")
    print(f"Pairs processed: {n_pairs_used} | Pairs skipped: {n_pairs_skipped}")
    print(f"generalize dir: {generalize_dir}")
    print(f"baseline cols: {baseline_cols}")
    print(f"splits: {splits}")


if __name__ == "__main__":
    main()
