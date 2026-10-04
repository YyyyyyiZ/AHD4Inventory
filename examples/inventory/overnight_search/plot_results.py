"""Scientific figures from report CSVs only; no raw tests or policy execution.

Primary means include all three generations. The paired intervals imported from
the report condition on those fixed policies and describe demand-path uncertainty
only. Ablation intervals remain per generation; they are never averaged into a
purported generation-level or pooled confidence interval.

Usage after the root experiment opens its test and builds report.py tables:
  .venv/bin/python -m examples.inventory.overnight_search.plot_results --run-dir RUN
  .venv/bin/python -m examples.inventory.overnight_search.plot_results --run-dir RUN --profile extended
  .venv/bin/python -m examples.inventory.overnight_search.plot_results --self-test
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
from pathlib import Path
import sys
import tempfile

import numpy as np


ARMS = ("one_query", "best_of_n", "evolution", "baek")
NUMERIC_ARMS = ARMS[:3]
LABELS = {"one_query": "One query", "best_of_n": "Best of 8",
          "evolution": "Evolution", "baek": "Baek-style L2"}
COLORS = {"one_query": "#7A70A8", "best_of_n": "#4581A5",
          "evolution": "#168174", "baek": "#CF8041"}
MARKERS = ("o", "s", "^")
CSV_NAMES = ("group_summary.csv", "paired_comparisons.csv", "optimizer_ablation.csv")


def plotting_library():
    try:
        import matplotlib
    except ModuleNotFoundError:
        runtime = Path("/tmp/baek-plot-runtime-20260916")
        if not (runtime / "matplotlib").is_dir():
            raise RuntimeError("Matplotlib is unavailable; install it or supply its module directory via PYTHONPATH.")
        sys.path.append(str(runtime))
        import matplotlib
    matplotlib.use("Agg", force=True)
    import matplotlib.pyplot as plt
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10,
                         "axes.spines.top": False, "axes.spines.right": False,
                         "axes.labelcolor": "#303C45", "axes.titleweight": "bold",
                         "text.color": "#26343D", "xtick.color": "#47545C",
                         "ytick.color": "#47545C", "pdf.fonttype": 42,
                         "svg.fonttype": "none", "savefig.facecolor": "white"})
    return plt


def finite(value):
    try:
        x = float(value)
        return x if math.isfinite(x) else None
    except (ValueError, TypeError):
        return None


def read_csv(path):
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def primary_grid():
    return [dict(name=f"perish_m{m}_L2_cv{cv:g}_f{f:g}", m=m, L=2, cv=cv, f=f,
                 split="transfer" if m == 4 else "discovery")
            for m in (3, 4, 5) for cv in (1.5, 2.) for f in (0., .5)]


def scenario_specs(tables, profile, expected_count, warnings):
    if profile == "primary":
        expected = {x["name"]: x for x in primary_grid()}
    else:
        expected = {}
    for rows in tables.values():
        for row in rows:
            name = row.get("name")
            if not name:
                warnings.append("A CSV row without a scenario name was ignored.")
                continue
            if name not in expected:
                if profile == "primary":
                    raise ValueError(f"Unexpected primary scenario {name}; use the extended profile for a different grid.")
                expected[name] = {k: row.get(k, "") for k in ("name", "m", "L", "cv", "f", "split", "mean")}
    specs = list(expected.values())
    specs.sort(key=lambda r: tuple(finite(r.get(k)) if finite(r.get(k)) is not None else math.inf
                                  for k in ("m", "L", "mean", "cv", "f")) + (r["name"],))
    if len(specs) < expected_count:
        warnings.append(f"Only {len(specs)} of {expected_count} expected scenario names are present in the CSVs.")
        for i in range(expected_count - len(specs)):
            specs.append(dict(name=f"__missing_scenario_{i + 1}", missing=True))
    elif len(specs) != expected_count:
        warnings.append(f"CSV grid has {len(specs)} scenarios; expected-count setting is {expected_count}. Every supplied scenario is shown.")
    return specs


def unique_lookup(rows, keys):
    result = {}
    for row in rows:
        key = tuple(row.get(k, "") for k in keys)
        if key in result:
            raise ValueError(f"Duplicate CSV key {key}; refusing to select or average duplicate records.")
        result[key] = row
    return result


def label(spec):
    if spec.get("missing"):
        return "Missing scenario (absent from tables)"
    fields = []
    for key, display in (("m", "m"), ("mean", "mean"), ("cv", "CV"), ("f", "f")):
        value = finite(spec.get(key))
        if value is not None:
            fields.append(f"{display}={value:g}")
    if not fields:
        return spec["name"]
    if spec.get("split") == "transfer":
        fields.append("[transfer]")
    return ", ".join(fields)


def valid_group(row, profile):
    if row is None:
        return None
    cost, generations = finite(row.get("cost")), finite(row.get("generations"))
    sd = finite(row.get("generation_sd"))
    if cost is None or cost < 0 or generations is None or generations < 1 or int(generations) != generations:
        return None
    if profile == "primary" and generations != 3:
        return None
    if generations > 1 and (sd is None or sd < 0):
        return None
    return dict(cost=cost, generations=int(generations), sd=sd if generations > 1 else None)


def valid_pair(row):
    if row is None:
        return None
    keys = ("improvement_pct", "improvement_ci_low", "improvement_ci_high", "candidate_cost", "reference_cost")
    values = {k: finite(row.get(k)) for k in keys}
    if any(x is None for x in values.values()):
        return None
    if values["reference_cost"] <= 0 or values["candidate_cost"] < 0:
        return None
    if values["improvement_ci_low"] > values["improvement_ci_high"]:
        return None
    expected = 100 * (values["reference_cost"] - values["candidate_cost"]) / values["reference_cost"]
    if not np.isclose(expected, values["improvement_pct"], rtol=1e-7, atol=1e-6):
        return None
    return values


def style_rows(ax, specs, show_labels=True):
    n = len(specs)
    ax.set_ylim(n - .55, -.55)
    ax.set_yticks(np.arange(n))
    ax.set_yticklabels([label(s) for s in specs] if show_labels else [])
    ax.tick_params(axis="y", length=0, pad=8)
    ax.grid(axis="x", color="#E6EBEE", linewidth=.7)
    ax.set_axisbelow(True)
    for i, spec in enumerate(specs):
        if spec.get("split") == "transfer":
            ax.axhspan(i - .49, i + .49, color="#F1F4F5", zorder=0)


def save_figure(fig, out, stem):
    files = []
    for extension in ("png", "pdf", "svg"):
        path = out / f"{stem}.{extension}"
        fig.savefig(path, dpi=190, bbox_inches="tight", pad_inches=.16)
        files.append(path.name)
    return files


def comparison_figure(plt, specs, group_lookup, pair_lookup, profile, out, warnings, synthetic_fixture=False):
    fig, (left, right) = plt.subplots(1, 2, figsize=(14.6, max(6.8, .48 * len(specs) + 2.4)),
                                      gridspec_kw={"width_ratios": [1.35, 1.]})
    fig.subplots_adjust(left=.245, right=.98, bottom=.20, top=.82, wspace=.20)
    style_rows(left, specs)
    style_rows(right, specs, show_labels=False)
    offsets = np.linspace(-.25, .25, len(ARMS))
    valid_cells, plotted_pairs, all_costs, all_limits = {}, 0, [], []
    generation_counts = {arm: set() for arm in ARMS}
    for i, spec in enumerate(specs):
        missing = []
        for offset, arm in zip(offsets, ARMS):
            value = valid_group(group_lookup.get((spec["name"], arm)), profile)
            if value is None:
                missing.append(LABELS[arm])
                continue
            valid_cells[(spec["name"], arm)] = value
            generation_counts[arm].add(value["generations"])
            sd = value["sd"] or 0.
            all_costs.extend([value["cost"] - sd, value["cost"] + sd])
            left.errorbar(value["cost"], i + offset, xerr=sd if value["sd"] is not None else None,
                          fmt="o", color=COLORS[arm], markersize=4.5, linewidth=1.05, capsize=2, zorder=3)
        if missing:
            left.text(.01, i + .43, "Missing: " + ", ".join(missing), transform=left.get_yaxis_transform(),
                      fontsize=6.8, color="#9C5D51", va="center",
                      bbox=dict(facecolor="white", edgecolor="none", alpha=.8, pad=.4))
            warnings.append(f"{spec['name']}: missing or invalid principal cells: {', '.join(missing)}")
        pair = valid_pair(pair_lookup.get((spec["name"], "evolution", "baek")))
        evo, baek = valid_cells.get((spec["name"], "evolution")), valid_cells.get((spec["name"], "baek"))
        if pair and evo and baek:
            if not (np.isclose(pair["candidate_cost"], evo["cost"], rtol=1e-7, atol=1e-6)
                    and np.isclose(pair["reference_cost"], baek["cost"], rtol=1e-7, atol=1e-6)):
                pair = None
                warnings.append(f"{spec['name']}: comparison costs do not match group-summary costs.")
        else:
            pair = None
        if pair:
            low, high = pair["improvement_ci_low"], pair["improvement_ci_high"]
            right.hlines(i, low, high, color=COLORS["evolution"], linewidth=1.5, zorder=3)
            right.vlines([low, high], i - .055, i + .055, color=COLORS["evolution"], linewidth=1.1)
            right.plot(pair["improvement_pct"], i, "o", color=COLORS["evolution"], markersize=5, zorder=4)
            all_limits.extend([low, high, pair["improvement_pct"]])
            plotted_pairs += 1
        else:
            right.text(.5, i, "Unavailable", transform=right.get_yaxis_transform(), ha="center",
                       va="center", fontsize=8, color="#9C5D51",
                       bbox=dict(facecolor="white", edgecolor="none", pad=1.))
            warnings.append(f"{spec['name']}: evolution-vs-Baek paired comparison unavailable.")
    if all_costs:
        low, high = min(all_costs), max(all_costs)
        margin = max((high - low) * .13, high * .025, 1.)
        left.set_xlim(low - margin, high + margin)
    else:
        left.set_xlim(0, 1)
    extent = max([1.] + [abs(x) for x in all_limits]) * 1.16
    right.set_xlim(-extent, extent)
    right.axvline(0, color="#65747B", linestyle="--", linewidth=1.)
    left.set_title("Average cost across generated policies", loc="left", fontsize=11, pad=14)
    right.set_title("Evolution vs Baek-style L2", loc="left", fontsize=11, pad=14)
    left.set_xlabel("Cost per period (lower is better)")
    right.set_xlabel("Cost reduction (%)\nPositive values favor evolution")
    handles, labels = [], []
    for arm in ARMS:
        handles.append(plt.Line2D([], [], marker="o", linestyle="none", color=COLORS[arm], markersize=5))
        counts = generation_counts[arm]
        count_label = str(next(iter(counts))) if len(counts) == 1 else "/".join(str(x) for x in sorted(counts))
        labels.append(LABELS[arm] + (f" (n={count_label})" if count_label else " (unavailable)"))
    fig.legend(handles, labels, loc="upper center", bbox_to_anchor=(.6, .915), frameon=False, ncol=4, fontsize=9)
    fig.suptitle(("Primary" if profile == "primary" else "Extended") + " perishable-inventory comparison",
                 x=.245, y=.985, ha="left", fontsize=17, weight="bold")
    if synthetic_fixture:
        fig.text(.015, .985, "SYNTHETIC DATA / QA ONLY", color="#A3584A", fontsize=8, va="top")
    generation_note = ("Primary points average all 3 independent generations; cost whiskers show 1 generation SD."
                       if profile == "primary" else
                       "Points average all available generations shown in the legend; cost whiskers show 1 generation SD when n > 1.")
    fig.text(.245, .115, generation_note, fontsize=8.6)
    fig.text(.245, .082, "Right-hand intervals: paired 95% demand-path CIs, conditional on the fixed policies; they exclude generation uncertainty.", fontsize=8.6)
    fig.text(.245, .049, "All test generations are retained. Shading: withheld-feedback cases for numerical arms only; Baek knows the full family.", fontsize=8.6)
    files = save_figure(fig, out, "scenario_comparison")
    plt.close(fig)
    return dict(files=files, principal_cells=len(valid_cells), paired_comparisons=plotted_pairs,
                generation_counts={k: sorted(v) for k, v in generation_counts.items()})


def ablation_figure(plt, specs, lookup, out, warnings, synthetic_fixture=False):
    fig, axes = plt.subplots(1, 3, figsize=(16.2, max(6.8, .48 * len(specs) + 2.4)), sharey=True)
    fig.subplots_adjust(left=.225, right=.985, bottom=.20, top=.83, wspace=.14)
    limits, plotted_rows, group_means = [], 0, 0
    for column, (arm, ax) in enumerate(zip(NUMERIC_ARMS, axes)):
        style_rows(ax, specs, show_labels=column == 0)
        # Shared-axis label setters affect all siblings; restore the left labels
        # after configuring the panels below.
        ax.set_title(LABELS[arm], loc="left", fontsize=11, pad=14)
        ax.axvline(0, color="#65747B", linestyle="--", linewidth=1.)
        ax.set_xlabel("Tuning cost reduction (%)")
        for i, spec in enumerate(specs):
            complete = []
            for repeat, offset, marker in zip((1, 2, 3), (-.18, 0., .18), MARKERS):
                row = valid_pair(lookup.get((spec["name"], f"{arm}_r{repeat}")))
                if row is None:
                    continue
                complete.append(row)
                low, high = row["improvement_ci_low"], row["improvement_ci_high"]
                ax.hlines(i + offset, low, high, color=COLORS[arm], linewidth=.85, alpha=.65)
                ax.plot(row["improvement_pct"], i + offset, marker=marker, color=COLORS[arm],
                        markersize=3.5, linestyle="none", alpha=.9)
                limits.extend([low, high, row["improvement_pct"]])
                plotted_rows += 1
            if len(complete) == 3:
                reference = sum(r["reference_cost"] for r in complete)
                tuned = sum(r["candidate_cost"] for r in complete)
                group_gain = 100 * (reference - tuned) / reference
                ax.plot(group_gain, i + .33, "D", color="#26343D", markersize=3.8)
                limits.append(group_gain)
                group_means += 1
            else:
                ax.text(.98, i + .34, f"{len(complete)}/3 paired", transform=ax.get_yaxis_transform(),
                        ha="right", va="center", fontsize=7, color="#9C5D51")
                warnings.append(f"{spec['name']}/{arm}: ablation has {len(complete)}/3 complete generation pairs; no group diamond drawn.")
    axes[0].set_yticklabels([label(s) for s in specs])
    for ax in axes[1:]:
        ax.tick_params(labelleft=False)
    low = min([0.] + limits)
    high = max([1.] + limits)
    margin = max(1., .07 * (high - low))
    symlog = max(abs(low), abs(high)) > 150
    for ax in axes:
        ax.set_xlim(low - margin, high + margin)
        if symlog:
            ax.set_xscale("symlog", linthresh=5)
    handles = [plt.Line2D([], [], marker=marker, color="#60747B", linestyle="none", markersize=4)
               for marker in MARKERS]
    handles.append(plt.Line2D([], [], marker="D", color="#26343D", linestyle="none", markersize=4))
    fig.legend(handles, ["Generation 1", "Generation 2", "Generation 3", "Ratio of 3-generation means"],
               loc="upper center", bbox_to_anchor=(.6, .925), ncol=4, frameon=False, fontsize=9)
    fig.suptitle("Optimizer ablation: tuned parameters vs the same structure's defaults",
                 x=.225, y=.985, ha="left", fontsize=16, weight="bold")
    if synthetic_fixture:
        fig.text(.015, .985, "SYNTHETIC DATA / QA ONLY", color="#A3584A", fontsize=8, va="top")
    fig.text(.225, .115, "Colored markers retain every generation separately; their intervals are paired 95% demand-path CIs, not generation CIs.", fontsize=8.6)
    fig.text(.225, .082, "Black diamonds use all 3 generation means. No pooled interval is inferred from per-generation intervals; missing pairs remain missing.", fontsize=8.6)
    fig.text(.225, .049, "Positive values indicate lower cost after tuning. Tuning gains alone do not establish new-structure discovery."
             + (" Horizontal axes use a symmetric-log scale." if symlog else ""), fontsize=8.6)
    files = save_figure(fig, out, "optimizer_ablation")
    plt.close(fig)
    return dict(files=files, generation_pairs=plotted_rows, three_generation_means=group_means,
                symlog_axis=symlog, pooled_ci_created=False)


def build_figures(run, *, profile="primary", expected_count=None, output=None, synthetic_fixture=False):
    run = Path(run).resolve()
    out = Path(output).resolve() if output else run / "figures"
    out.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("MPLCONFIGDIR", str(out / ".matplotlib_cache"))
    tables = {name: read_csv(run / "tables" / name) for name in CSV_NAMES}
    warnings = []
    for name in CSV_NAMES:
        if not (run / "tables" / name).exists():
            warnings.append(f"Missing table: {name}")
    expected_count = expected_count if expected_count is not None else (12 if profile == "primary" else 8)
    specs = scenario_specs(tables, profile, expected_count, warnings)
    plt = plotting_library()
    comparison = comparison_figure(plt, specs, unique_lookup(tables[CSV_NAMES[0]], ("name", "method")),
                                   unique_lookup(tables[CSV_NAMES[1]], ("name", "candidate", "reference")),
                                   profile, out, warnings, synthetic_fixture)
    ablation = ablation_figure(plt, specs, unique_lookup(tables[CSV_NAMES[2]], ("name", "method")), out, warnings, synthetic_fixture)
    manifest = dict(profile=profile, scenarios=len(specs), expected_scenarios=expected_count,
                    comparison=comparison, optimizer_ablation=ablation, warnings=warnings,
                    raw_test_files_read=False, test_best_generation_selected=False,
                    synthetic_fixture=synthetic_fixture,
                    plot_source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                    matplotlib_version=sys.modules["matplotlib"].__version__, numpy_version=np.__version__,
                    input_sha256={name: hashlib.sha256((run / "tables" / name).read_bytes()).hexdigest()
                                  if (run / "tables" / name).exists() else None for name in CSV_NAMES})
    (out / "plot_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return manifest


def fixture_csv(path, rows, columns):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def self_test():
    """Invented fixtures only, all retained beneath /tmp for visual inspection."""
    root = Path(tempfile.mkdtemp(prefix="overnight_plot_selftest_", dir="/tmp"))
    summary = {}
    for profile in ("primary", "extended"):
        specs = primary_grid() if profile == "primary" else [dict(name=f"fictional_m{m}_cv{cv}_f{f}",
                  m=m, L=2, cv=cv, f=f, split="extension") for m in (7, 8) for cv in (1.5, 2.) for f in (0., .5)]
        group, pairs, ablations = [], [], []
        for i, spec in enumerate(specs):
            base = 100 + i * 4
            means = {"one_query": base + 4, "best_of_n": base + 2, "evolution": base,
                     "baek": base + 3 * math.sin(i * .7)}
            for arm, cost in means.items():
                generations = 1 if profile == "extended" and arm == "baek" else 3
                group.append(dict(**spec, method=arm, cost=cost, generation_sd=.6 if generations > 1 else "", generations=generations))
            gain = 100 * (means["baek"] - base) / means["baek"]
            pairs.append(dict(**spec, candidate="evolution", reference="baek", candidate_cost=base,
                              reference_cost=means["baek"], improvement_pct=gain,
                              improvement_ci_low=gain - .7, improvement_ci_high=gain + .7))
            for arm in NUMERIC_ARMS:
                for repeat in (1, 2, 3):
                    tuned, raw = means[arm] + repeat * .1, means[arm] * (1.07 + .01 * repeat)
                    gain = 100 * (raw - tuned) / raw
                    ablations.append(dict(**spec, method=f"{arm}_r{repeat}", candidate_cost=tuned,
                                          reference_cost=raw, improvement_pct=gain,
                                          improvement_ci_low=gain - .6, improvement_ci_high=gain + .6))
        run = root / profile
        for name, rows in zip(CSV_NAMES, (group, pairs, ablations)):
            fixture_csv(run / "tables" / name, rows, list(rows[0]))
        result = build_figures(run, profile=profile, synthetic_fixture=True)
        assert result["comparison"]["paired_comparisons"] == len(specs)
        assert result["comparison"]["principal_cells"] == 4 * len(specs)
        assert result["optimizer_ablation"]["three_generation_means"] == 3 * len(specs)
        assert not result["warnings"]
        for filename in result["comparison"]["files"] + result["optimizer_ablation"]["files"]:
            assert (run / "figures" / filename).stat().st_size > 1000
        summary[profile] = result
        if profile == "primary":
            # Drop a principal cell, supply the wrong generation count, and
            # remove one ablation repeat: no zero imputation or pooled diamond.
            bad = root / "incomplete"
            group = [r for r in group if not (r["name"] == specs[0]["name"] and r["method"] == "evolution")]
            next(r for r in group if r["name"] == specs[1]["name"] and r["method"] == "baek")["generations"] = 2
            ablations = [r for r in ablations if not (r["name"] == specs[2]["name"] and r["method"] == "evolution_r3")]
            for name, rows in zip(CSV_NAMES, (group, pairs, ablations)):
                fixture_csv(bad / "tables" / name, rows, list(rows[0]))
            incomplete = build_figures(bad, synthetic_fixture=True)
            assert incomplete["comparison"]["paired_comparisons"] == 10
            assert incomplete["optimizer_ablation"]["three_generation_means"] == 35
            assert incomplete["warnings"]
            summary["incomplete"] = incomplete
    empty = build_figures(root / "empty", synthetic_fixture=True)
    assert empty["scenarios"] == 12 and empty["comparison"]["principal_cells"] == 0
    assert empty["optimizer_ablation"]["three_generation_means"] == 0
    return dict(fixtures=str(root), complete_primary="passed", complete_extended="passed",
                incomplete_and_empty="passed", real_test_data_read=False,
                figures_created=24)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", type=Path)
    parser.add_argument("--profile", choices=("primary", "extended"), default="primary")
    parser.add_argument("--expected-scenarios", type=int)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        result = self_test()
    else:
        if args.run_dir is None:
            parser.error("--run-dir is required; the plotter never opens a default real experiment implicitly.")
        if args.expected_scenarios is not None and args.expected_scenarios < 1:
            parser.error("--expected-scenarios must be positive")
        result = build_figures(args.run_dir, profile=args.profile, expected_count=args.expected_scenarios,
                               output=args.output_dir)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
