# make_policy_histograms.py
# Put this file in the SAME directory as cost_matrix1.csv and run:
#   python make_policy_histograms.py --split test
#
# Outputs:
#   histograms/<split>/POLICY__3hists.png          (one figure per policy, 3 histograms)
#   hist_summary_<split>.csv                      (per policy x baseline summary)

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


DATASET_COL = "dataset"
BASELINE_COLS = ["basestock", "capped_base_stock", "constant"]
# BASELINE_COLS = ["constant"]

# Non-blue, nicer palette (user explicitly requested)
BASELINE_STYLE = {
    "basestock": {"color": "#2ca02c", "label": "Base-stock"},          # green
    "capped_base_stock": {"color": "#ff7f0e", "label": "Capped BS"},   # orange
    "constant": {"color": "#9467bd", "label": "Constant order"},       # purple
}


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


def robust_xlim_include_zero(x: np.ndarray, q_lo=0.01, q_hi=0.99, symmetric=False) -> Tuple[float, float] | None:
    """
    Robust x-limits that include 0. Optionally symmetric around 0.
    """
    x = x[np.isfinite(x)]
    if x.size < 20:
        # if too few points, let matplotlib autoscale but keep 0 visible by adding a small margin
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


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", type=str, default="cost_matrix_capped_l2.csv")
    parser.add_argument("--split", type=str, default="test", choices=["train", "test"])
    parser.add_argument("--bins", type=int, default=40)
    parser.add_argument("--robust", action="store_true", help="Use robust x-limits based on quantiles (still includes 0).")
    parser.add_argument("--symmetric", action="store_true", help="Force symmetric x-limits around 0 (good for showing +/-).")
    args = parser.parse_args()

    here = Path(__file__).resolve().parent
    csv_path = here / args.csv
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV not found: {csv_path}")

    df = pd.read_csv(csv_path)

    # Normalize dataset column name
    if DATASET_COL not in df.columns:
        df = df.rename(columns={df.columns[0]: DATASET_COL})

    # Identify policy columns
    missing_baselines = [c for c in BASELINE_COLS if c not in df.columns]
    if missing_baselines:
        raise ValueError(f"Missing baseline columns: {missing_baselines}. Found: {list(df.columns)}")

    policy_cols = [c for c in df.columns if c not in ([DATASET_COL] + BASELINE_COLS)]
    if not policy_cols:
        raise ValueError("No policy columns found besides dataset and baselines.")

    # Coerce numeric for baselines and policies (handles unfinished policies with blanks)
    df = coerce_numeric(df, BASELINE_COLS + policy_cols)

    # Filter by split suffix
    suffix = f"_{args.split}.json"
    df = df[df[DATASET_COL].astype(str).str.endswith(suffix)].copy()
    if df.empty:
        raise ValueError(f"No rows ending with '{suffix}' found.")

    out_dir = here / "histograms" / args.split
    out_dir.mkdir(parents=True, exist_ok=True)

    summary_rows = []

    # Baseline arrays
    baseline_arr = {b: df[b].to_numpy(dtype=float) for b in BASELINE_COLS}
    n_rows = len(df)

    # Make plots policy-by-policy (one figure contains 3 histograms)
    for policy in policy_cols:
        p_cost = df[policy].to_numpy(dtype=float)

        fig, axes = plt.subplots(nrows=3, ncols=1, figsize=(9, 10), sharex=False)
        fig.suptitle(f"{policy} — % Cost Reduction (positive = better, negative = worse)\nSplit: {args.split}", fontsize=13)

        for ax, baseline in zip(axes, BASELINE_COLS):
            pr = percent_reduction(p_cost, baseline_arr[baseline])
            stats = summarize(pr)

            style = BASELINE_STYLE.get(baseline, {"color": "#444444", "label": baseline})
            color = style["color"]
            label = style["label"]

            x = pr[np.isfinite(pr)]

            # Histogram
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
                f"vs {label} | mean={stats['mean']:.2f}% | pos={stats['pct_pos']:.1f}% | neg={stats['pct_neg']:.1f}%"
                f" | n_valid={stats['n_valid']}/{n_rows}",
                fontsize=11,
            )

            # X label
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
                "split": args.split,
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
        fig_path = out_dir / f"{policy}__3hists.png"
        fig.savefig(fig_path, dpi=180)
        plt.close(fig)

    # Write summary CSV
    summary_df = pd.DataFrame(summary_rows)
    summary_path = here / f"hist_summary_{args.split}.csv"
    summary_df.to_csv(summary_path, index=False)

    print(f"Done.\n- Figures: {out_dir}\n- Summary: {summary_path}")
    print(f"Policies: {len(policy_cols)} ; Rows used: {n_rows} ({args.split})")


if __name__ == "__main__":
    main()
