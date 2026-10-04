"""Render frozen core results with Matplotlib; no simulation or model calls."""
import argparse
import csv
import json
from pathlib import Path
import statistics

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D


ROOT = Path(__file__).resolve().parent
CORES = [
    ("poisson_L6_c1_2", "Poisson"),
    ("normal_std30_L6_c1_2", "Normal, std = 30"),
    ("exponential_L6_c1_2", "Exponential"),
]
COLORS = {1: "#2563eb", 2: "#d97706", 3: "#7c3aed"}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--preview", action="store_true")
    args = parser.parse_args()
    with (ROOT / "tables/paired_comparisons.csv").open(encoding="utf-8-sig") as stream:
        rows = [r for r in csv.DictReader(stream) if r["batch"] == "fresh_test"
                and r["reference"] == "historical_AHD" and r["analysis_role"] == "main"
                and r["scenario_id"] in {s for s, _ in CORES}]
    if not args.preview and len(rows) != 18:
        raise SystemExit("Final figure requires all 18 core draw/method pairs.")
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11,
                         "axes.spines.top": False, "axes.spines.right": False,
                         "svg.fonttype": "none", "savefig.facecolor": "white"})
    fig, axes = plt.subplots(1, 3, figsize=(11.4, 5.7), sharey=True)
    limits = [0.0]
    for ax, (scenario, title) in zip(axes, CORES):
        ax.axhline(0, color="#64748b", linewidth=1.1, linestyle="--")
        ax.grid(axis="y", color="#e2e8f0", linewidth=0.8)
        ax.set_axisbelow(True)
        for xpos, method in enumerate(["Baek-L1", "Baek-L2"]):
            group = sorted([r for r in rows if r["scenario_id"] == scenario and r["method"] == method],
                           key=lambda r: int(r["repeat"]))
            vals = []
            for r in group:
                draw = int(r["repeat"])
                value = float(r["improvement_pct"])
                lo, hi = json.loads(r["improvement_pct_ci"])
                limits.extend([lo, hi, value])
                vals.append(value)
                ax.errorbar(xpos + (draw - 2) * 0.15, value,
                            yerr=[[value - lo], [hi - value]], fmt="o", markersize=6,
                            color=COLORS[draw], elinewidth=1.6, capsize=3, zorder=3)
            if vals:
                ax.scatter([xpos + 0.29], [statistics.mean(vals)], marker="D", s=40,
                           color="#111827", zorder=4)
                ax.text(xpos, 0.015, f"{len(vals)}/3 draws", transform=ax.get_xaxis_transform(),
                        ha="center", va="bottom", fontsize=9, color="#64748b")
        ax.set_title(title, fontsize=13, fontweight="bold", pad=12)
        ax.set_xticks([0, 1], ["L1: instance", "L2: family"])
        ax.set_xlim(-0.4, 1.5)
    low, high = min(limits), max(limits)
    span = max(high - low, 0.1)
    axes[0].set_ylim(low - span * 0.15, high + span * 0.10)
    axes[0].set_ylabel("Cost reduction vs historical AHD (%)\nPositive values favor Baek")
    title = "Baek-style policy design: three independent draws"
    if args.preview:
        title += " (in progress)"
    fig.suptitle(title, x=0.5, y=0.97, fontsize=17, fontweight="bold")
    fig.text(0.5, 0.90, "Core scenarios: lead time 6, holding cost 1, lost-sales cost 2; 50 selling periods",
             ha="center", fontsize=10.5, color="#475569")
    handles = [Line2D([0], [0], marker="o", color=COLORS[d], label=f"Draw {d}", linestyle="none")
               for d in (1, 2, 3)]
    handles.append(Line2D([0], [0], marker="D", color="#111827", label="Draw mean", linestyle="none"))
    fig.legend(handles=handles, loc="lower center", bbox_to_anchor=(0.5, 0.09), ncol=4, frameon=False)
    fig.text(0.5, 0.045, "Intervals: paired 95% bootstrap over 1,000 new demand paths; they exclude generation uncertainty.",
             ha="center", fontsize=9, color="#475569")
    fig.text(0.5, 0.015, "Historical AHD used different models and information budgets. These are relative costs, not optimality gaps.",
             ha="center", fontsize=9, color="#475569")
    fig.subplots_adjust(left=0.105, right=0.975, bottom=0.25, top=0.79, wspace=0.10)
    base = Path("/tmp/baek-core-preview") if args.preview else ROOT / "figures/core_fresh_test_comparison"
    for suffix in (".png", ".svg"):
        fig.savefig(base.with_suffix(suffix), dpi=180)
    print(json.dumps({"core_pairs": len(rows), "png": str(base.with_suffix('.png'))}))


if __name__ == "__main__":
    main()
