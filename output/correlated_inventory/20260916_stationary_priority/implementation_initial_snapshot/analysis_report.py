"""Incremental, read-only analysis of frozen evaluations; never executes policies.

The 18 primary runs are identified by protocol metadata and exact run IDs, not
by their test results. Bootstrap units are whole paired trajectories. The mean
of generated repeats is formed within each path before resampling paths; it is
not an ensemble policy and its interval excludes generation uncertainty.
"""
from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import re
import subprocess
import sys

import numpy as np

from .data import scenario_specs
from ..baek_comparison.analysis import paired_statistics


VERSION = "correlated-inventory-report-v1"
HORIZONS = (50, 100, 200, 500)
BASELINES = ("constant_order", "base_stock", "capped_base_stock", "forecast_capped_base_stock",
             "conditional_pil", "forecast_adaptive_pil", "pil_cop_continuation")
LABELS = {"constant_order": "Constant order", "base_stock": "Base stock", "capped_base_stock": "Capped base stock",
          "forecast_capped_base_stock": "Forecast capped BS", "conditional_pil": "Conditional PIL",
          "forecast_adaptive_pil": "Adaptive PIL", "pil_cop_continuation": "PIL + COP continuation", "self_evolve": "Self-evolve + optimizer"}
SHORT_SCENARIOS = {"exp_iid_fixed6": "IID | L=6", "exp_ar_pos08_fixed6": "AR+ (latent 0.8) | L=6",
                   "exp_ar_neg06_fixed6": "AR- (latent -0.6) | L=6", "exp_regime095_fixed6": "Regime (stay 0.95) | L=6",
                   "exp_iid_random3_9": "IID | L=3 or 9", "exp_regime095_random3_9": "Regime | L=3 or 9"}
METRICS = ("mean_cost_per_period", "holding_per_period", "lost_units_per_period", "fill_rate", "orders_per_period")
NPZ_METRICS = ("total_cost", "holding_cost", "lost_units", "demand_units", "sales_units", "order_units")


def _read(path, default=None):
    return json.loads(path.read_text()) if path.exists() else default


def _write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n")
    temporary.replace(path)


def _write_csv(path, rows, columns=()):
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = list(dict.fromkeys([*columns, *(key for row in rows for key in row)]))
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: json.dumps(value, ensure_ascii=False) if isinstance(value, (dict, list, tuple)) else value
                             for key, value in row.items()})


def _hash_array(values):
    array = np.ascontiguousarray(values, dtype="<f8")
    return hashlib.sha256(array.tobytes()).hexdigest()


def _inside(root, relative):
    path = (root / relative).resolve()
    if not path.is_relative_to(root):
        raise ValueError("Artifact path escapes run directory")
    return path


def _scope(row):
    if row["family"] in BASELINES:
        return "baseline" if int(row["source_training_horizon"]) == 200 and row["policy_id"] == "baseline_h200_" + row["family"] else "baseline_extension"
    if row["family"] != "self_evolve":
        return "other"
    match = re.fullmatch(r"self_evolve_h200_r([123])", row["policy_id"])
    if match and row.get("full_protocol") is True and int(row["source_training_horizon"]) == 200 and row.get("repeat") == int(match[1]):
        return "primary"
    return "horizon_extension" if row.get("full_protocol") is True and int(row["source_training_horizon"]) != 200 else "pilot_or_nonprimary"


def load_evaluations(run_dir):
    """Read arrays and recompute every reported metric, rejecting inconsistencies."""
    root = Path(run_dir).resolve()
    manifest = _read(root / "dataset_manifest.json", {})
    datasets = {(x["scenario_id"], x["split"]): x for x in manifest.get("files", [])}
    specs = {s.scenario_id: s for s in scenario_specs()}
    records, issues, seen = [], [], set()
    for source in sorted((root / "evaluation").glob("*/*/test.json")):
        try:
            rows = _read(source)
            if not isinstance(rows, list):
                raise ValueError("Expected a list of evaluation rows")
        except (ValueError, OSError) as exc:
            issues.append({"file": str(source.relative_to(root)), "error": str(exc)})
            continue
        for index, raw in enumerate(rows):
            try:
                row = dict(raw)
                scenario = specs[row["scenario_id"]]
                if row.get("status", "ok") != "ok":
                    raise ValueError("Evaluation status is not ok: " + str(row.get("status")))
                if row["split"] != "test" or row["mode"] not in {"steady", "cold_start"} or row["horizon"] not in HORIZONS:
                    raise ValueError("Unexpected split, mode, or horizon")
                if source.parent.name != row["policy_id"] or source.parent.parent.name != row["scenario_id"]:
                    raise ValueError("Evaluation directory does not match row identity")
                key = (row["scenario_id"], row["policy_id"], row["split"], row["mode"], row["horizon"])
                if key in seen:
                    raise ValueError("Duplicate evaluation key; no result selected")
                seen.add(key)
                path = _inside(root, row["costs_path"])
                cost_sha = hashlib.sha256(path.read_bytes()).hexdigest()
                supplied_sha = row.get("costs_sha256") or row.get("costs_file_sha256")
                if supplied_sha and supplied_sha != cost_sha:
                    raise ValueError("Cost archive hash mismatch")
                with np.load(path, allow_pickle=False) as archive:
                    arrays = {name: np.asarray(archive[row["array_prefix"] + "_" + name], dtype=float).copy() for name in NPZ_METRICS}
                shapes = {a.shape for a in arrays.values()}
                if len(shapes) != 1 or arrays["total_cost"].ndim != 1 or len(arrays["total_cost"]) == 0:
                    raise ValueError("Per-path arrays have incompatible shapes")
                if any(not np.isfinite(a).all() or (a < 0).any() for a in arrays.values()):
                    raise ValueError("Invalid per-path quantities")
                if not np.allclose(arrays["total_cost"], arrays["holding_cost"] + scenario.lost_sales_cost * arrays["lost_units"], rtol=1e-10, atol=1e-7):
                    raise ValueError("Total cost decomposition mismatch")
                if not np.allclose(arrays["demand_units"], arrays["sales_units"] + arrays["lost_units"], rtol=1e-10, atol=1e-7):
                    raise ValueError("Demand balance mismatch")
                n = len(arrays["total_cost"])
                dataset = datasets.get((row["scenario_id"], "test"), {})
                if dataset.get("n_paths", n) != n:
                    raise ValueError("Test path count differs from manifest")
                tape_hash = row.get("dataset_arrays_sha256")
                if tape_hash and dataset.get("arrays_sha256") != tape_hash:
                    raise ValueError("Evaluation dataset hash differs from manifest")
                horizon = row["horizon"]
                total_demand = float(arrays["demand_units"].sum())
                computed = {"mean_cost_per_period": float(arrays["total_cost"].mean() / horizon),
                            "holding_per_period": float(arrays["holding_cost"].mean() / horizon),
                            "lost_units_per_period": float(arrays["lost_units"].mean() / horizon),
                            "fill_rate": float(arrays["sales_units"].sum() / total_demand) if total_demand else 1.0,
                            "orders_per_period": float(arrays["order_units"].mean() / horizon)}
                for metric, value in computed.items():
                    if metric not in row or not math.isclose(float(row[metric]), value, rel_tol=1e-9, abs_tol=1e-7):
                        raise ValueError("Evaluation metric mismatch: " + metric)
                policy_hash = row.get("code_sha256") or row.get("record_sha256")
                row.update(computed, scope=_scope(row), n_paths=n, costs_sha256=cost_sha,
                           path_fill_rate_mean=float(np.divide(arrays["sales_units"], arrays["demand_units"],
                                                              out=np.ones(n), where=arrays["demand_units"] > 0).mean()),
                           provenance_verified=bool(tape_hash and policy_hash),
                           evaluation_file=str(source.relative_to(root)))
                records.append({"row": row, "arrays": arrays})
            except (KeyError, TypeError, ValueError, OSError) as exc:
                issues.append({"file": str(source.relative_to(root)), "row_index": index, "error": str(exc)})
    # A conflicting duplicate invalidates every version, not just the later one.
    duplicate_files = {x["file"] for x in issues if "Duplicate evaluation key" in x["error"]}
    if duplicate_files:
        records = [x for x in records if x["row"]["evaluation_file"] not in duplicate_files]
    identities = {}
    for item in records:
        row = item["row"]
        key = (row["scenario_id"], row["policy_id"])
        identities.setdefault(key, set()).add(row.get("code_sha256") or row.get("record_sha256"))
    changed = {key for key, hashes in identities.items() if len(hashes) > 1}
    for key in sorted(changed):
        issues.append({"scenario_id": key[0], "policy_id": key[1], "error": "Policy source hash changed across evaluation windows"})
    records = [x for x in records if (x["row"]["scenario_id"], x["row"]["policy_id"]) not in changed]
    return records, issues


def summarize_repeats(records):
    groups = {}
    for item in records:
        row = item["row"]
        if row["scope"] == "primary":
            groups.setdefault((row["scenario_id"], row["mode"], row["horizon"]), []).append(item)
    summaries, averaged = [], []
    for key, items in sorted(groups.items()):
        items = sorted(items, key=lambda x: x["row"]["repeat"])
        row = dict(scenario_id=key[0], mode=key[1], horizon=key[2], family="self_evolve",
                   source_training_horizon=200, n_valid_repeats=len(items), n_planned_repeats=3,
                   repeats=[x["row"]["repeat"] for x in items],
                   selection="all primary repeats; no test-based best selection")
        for metric in METRICS:
            values = [x["row"][metric] for x in items]
            row[metric + "_mean"] = float(np.mean(values))
            row[metric + "_sd"] = float(np.std(values, ddof=1)) if len(values) > 1 else None
        summaries.append(row)
        first = items[0]
        if all(x["row"].get("dataset_arrays_sha256") == first["row"].get("dataset_arrays_sha256")
               and np.array_equal(x["arrays"]["demand_units"], first["arrays"]["demand_units"]) for x in items):
            average = dict(first["row"], policy_id="self_evolve_mean_of_available_repeats", repeat=None,
                           n_repeats=len(items), aggregate="mean_of_available_repeats")
            average["provenance_verified"] = all(x["row"]["provenance_verified"] for x in items)
            means = {name: np.mean(np.stack([x["arrays"][name] for x in items]), axis=0) for name in NPZ_METRICS}
            # Identical exogenous totals must remain bit-identical for pairing;
            # adding the same floating-point value three times can round it.
            means["demand_units"] = first["arrays"]["demand_units"].copy()
            averaged.append({"row": average, "arrays": means})
    return summaries, averaged


def paired_comparisons(records, averaged, *, run_dir, n_bootstrap=5000):
    cache_dir = Path(run_dir) / "analysis_cache"
    references = {}
    for item in records:
        row = item["row"]
        if row["scope"] == "baseline":
            references.setdefault((row["scenario_id"], row["mode"], row["horizon"]), []).append(item)
    results, issues = [], []
    for candidate in [x for x in records if x["row"]["scope"] in {"primary", "horizon_extension"}] + averaged:
        row, arrays = candidate["row"], candidate["arrays"]
        for reference in references.get((row["scenario_id"], row["mode"], row["horizon"]), []):
            ref, ref_arrays = reference["row"], reference["arrays"]
            if arrays["total_cost"].shape != ref_arrays["total_cost"].shape or not np.array_equal(arrays["demand_units"], ref_arrays["demand_units"]):
                issues.append({"candidate": row["policy_id"], "reference": ref["policy_id"], "error": "Paired path demand totals or shapes differ"})
                continue
            tape_hash = row.get("dataset_arrays_sha256")
            if tape_hash and ref.get("dataset_arrays_sha256") and tape_hash != ref["dataset_arrays_sha256"]:
                issues.append({"candidate": row["policy_id"], "reference": ref["policy_id"], "error": "Paired dataset hashes differ"})
                continue
            cand = arrays["total_cost"] / row["horizon"]
            baseline = ref_arrays["total_cost"] / row["horizon"]
            key = {"candidate_array": _hash_array(cand), "reference_array": _hash_array(baseline),
                   "seed": 2026091603, "n_bootstrap": n_bootstrap, "version": VERSION}
            cache_path = cache_dir / (hashlib.sha256(json.dumps(key, sort_keys=True).encode()).hexdigest() + ".json")
            stats = _read(cache_path)
            if stats is None:
                stats = paired_statistics(cand, baseline, seed=key["seed"], n_bootstrap=n_bootstrap)
                _write_json(cache_path, stats)
            results.append({"scenario_id": row["scenario_id"], "candidate_policy_id": row["policy_id"],
                            "reference_policy_id": ref["policy_id"], "reference_family": ref["family"],
                            "repeat": row.get("repeat"), "n_repeats": row.get("n_repeats", 1),
                            "aggregate": row.get("aggregate", "single_repeat"), "scope": row["scope"],
                            "source_training_horizon": row["source_training_horizon"],
                            "mode": row["mode"], "horizon": row["horizon"],
                            "pairing_provenance_verified": bool(row["provenance_verified"] and ref["provenance_verified"] and tape_hash), **stats})
    return results, issues


def coverage(records):
    lookup = {(x["row"]["scenario_id"], x["row"]["policy_id"], x["row"]["mode"], x["row"]["horizon"]): x["row"] for x in records}
    rows = []
    for scenario in scenario_specs():
        for repeat in (1, 2, 3):
            policy = f"self_evolve_h200_r{repeat}"
            present = [lookup.get((scenario.scenario_id, policy, mode, horizon)) for mode in ("steady", "cold_start") for horizon in HORIZONS]
            valid = [x for x in present if x and x["scope"] == "primary"]
            main = lookup.get((scenario.scenario_id, policy, "steady", 200))
            rows.append({"scenario_id": scenario.scenario_id, "policy_id": policy, "repeat": repeat,
                         "evaluated_windows": len(valid), "expected_windows": 8,
                         "main_h200_available": bool(main and main["scope"] == "primary"),
                         "all_windows_available": len(valid) == 8,
                         "provenance_complete": len(valid) == 8 and all(x["provenance_verified"] for x in valid),
                         "status": "complete" if len(valid) == 8 else "partial" if valid else "pending_or_failed"})
    return rows


def best_training_baselines(run_dir):
    selections = []
    for scenario in scenario_specs():
        path = Path(run_dir) / "baselines" / scenario.scenario_id / "h200" / "records.json"
        fitted = _read(path, {})
        valid = [(name, record) for name, record in fitted.items() if name in BASELINES
                 and isinstance(record.get("training", {}).get("mean_cost_per_period"), (int, float))
                 and math.isfinite(record["training"]["mean_cost_per_period"])]
        if valid:
            name, record = min(valid, key=lambda x: (x[1]["training"]["mean_cost_per_period"], x[0]))
            selections.append({"scenario_id": scenario.scenario_id, "reference_family": name,
                               "train_cost_per_period": record["training"]["mean_cost_per_period"],
                               "available_families": len(valid), "expected_families": 7,
                               "selection_complete": len(valid) == 7,
                               "selection_rule": "minimum frozen training cost; never test cost",
                               "record_file_sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
    return selections


def _format(value, digits=3):
    return "—" if value is None else f"{value:.{digits}f}"


def _main_table(records, repeats, mode):
    lines = ["| 场景 | 方法 | 单位期成本 | 三次样本 SD | 有效/计划 | 满足率 |", "|---|---|---:|---:|---:|---:|"]
    for spec in scenario_specs():
        selected = [x["row"] for x in records if x["row"]["scenario_id"] == spec.scenario_id
                    and x["row"]["scope"] == "baseline" and x["row"]["mode"] == mode and x["row"]["horizon"] == 200]
        for row in sorted(selected, key=lambda x: BASELINES.index(x["family"])):
            lines.append(f"| {spec.scenario_id} | {LABELS[row['family']]} | {_format(row['mean_cost_per_period'])} | — | 1/1 | {100*row['fill_rate']:.2f}% |")
        summary = next((r for r in repeats if (r["scenario_id"], r["mode"], r["horizon"]) == (spec.scenario_id, mode, 200)), None)
        if summary:
            lines.append(f"| {spec.scenario_id} | self-evolve + optimizer | {_format(summary['mean_cost_per_period_mean'])} | {_format(summary['mean_cost_per_period_sd'])} | {summary['n_valid_repeats']}/3 | {100*summary['fill_rate_mean']:.2f}% |")
        else:
            lines.append(f"| {spec.scenario_id} | self-evolve + optimizer | — | — | 0/3 | — |")
    return lines


def report(run_dir, *, n_bootstrap=5000, make_plots=True, plot_runtime=None):
    if isinstance(n_bootstrap, bool) or not isinstance(n_bootstrap, int) or n_bootstrap < 1:
        raise ValueError("n_bootstrap must be a positive integer")
    root = Path(run_dir).resolve()
    records, issues = load_evaluations(root)
    repeats, averaged = summarize_repeats(records)
    pairs, pairing_issues = paired_comparisons(records, averaged, run_dir=root, n_bootstrap=n_bootstrap)
    issues.extend(pairing_issues)
    cover = coverage(records)
    selected_refs = best_training_baselines(root)
    main_selected_pairs = [p for p in pairs if p["mode"] == "steady" and p["horizon"] == 200
                           and p["aggregate"] == "mean_of_available_repeats" and p["scope"] == "primary"
                           and any(r["selection_complete"] and (r["scenario_id"], r["reference_family"]) == (p["scenario_id"], p["reference_family"]) for r in selected_refs)]
    diagnostics = [r for r in _read(root / "dataset_diagnostics.json", []) if r["split"] == "train"]
    baseline_rows = sum(x["row"]["scope"] == "baseline" for x in records)
    summary = {"version": VERSION, "created_utc": datetime.now(timezone.utc).isoformat(),
               "expected_primary_runs": 18, "primary_h200_available": sum(x["main_h200_available"] for x in cover),
               "primary_fully_evaluated": sum(x["all_windows_available"] for x in cover),
               "primary_provenance_complete": sum(x["provenance_complete"] for x in cover),
               "expected_primary_windows": 144, "primary_windows": sum(x["row"]["scope"] == "primary" for x in records),
               "baseline_windows": baseline_rows, "expected_baseline_windows": 336,
               "baseline_provenance_windows": sum(x["row"]["scope"] == "baseline" and x["row"]["provenance_verified"] for x in records),
               "total_rows": len(records), "pilot_or_nonprimary_rows": sum(x["row"]["scope"] == "pilot_or_nonprimary" for x in records),
               "extension_rows": sum(x["row"]["scope"] == "horizon_extension" for x in records),
               "repeat_rows": len(repeats), "paired_rows": len(pairs), "bootstrap_replicates": n_bootstrap,
               "issues": issues, "coverage": cover, "selected_training_references": selected_refs,
               "uncertainty": "whole-path bootstrap conditional on frozen policies; generation SD reported separately"}
    summary["complete"] = summary["primary_fully_evaluated"] == 18 and summary["primary_provenance_complete"] == 18 and baseline_rows == 336 and summary["baseline_provenance_windows"] == 336 and not issues
    summary["status"] = "complete" if summary["complete"] else "incomplete"
    tables = root / "tables"
    _write_csv(tables / "all_results.csv", [x["row"] for x in records], ("scenario_id", "policy_id", "family", "repeat", "scope", "mode", "horizon"))
    _write_csv(tables / "repeats.csv", repeats, ("scenario_id", "mode", "horizon", "n_valid_repeats", "n_planned_repeats"))
    _write_csv(tables / "paired.csv", pairs, ("scenario_id", "candidate_policy_id", "reference_family", "mode", "horizon", "aggregate"))
    _write_csv(tables / "coverage.csv", cover)
    _write_csv(tables / "best_training_baselines.csv", selected_refs, ("scenario_id", "reference_family"))
    _write_csv(tables / "main_vs_best_training_baseline.csv", main_selected_pairs, ("scenario_id", "reference_family", "n_repeats", "improvement_pct"))
    _write_csv(tables / "training_diagnostics.csv", diagnostics, ("scenario_id", "marginal_mean", "marginal_std", "acf_demand"))
    _write_json(root / "analysis_summary.json", summary)
    if make_plots:
        if plot_runtime is not None:
            env = dict(os.environ)
            env["PYTHONPATH"] = str(Path(plot_runtime).resolve()) + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
            result = subprocess.run([sys.executable, "-m", "examples.inventory.correlated_benchmark.analysis_report", "--run-dir", str(root), "--plots-only"],
                                    env=env, cwd=Path(__file__).resolve().parents[3], capture_output=True, text=True, timeout=120)
            if result.returncode:
                summary["plot_error"] = result.stderr[-2000:]
        else:
            try:
                render_plots(root)
            except ImportError as exc:
                summary["plot_error"] = str(exc) + "; provide --plot-runtime or use --no-plots"
    lines = ["# 平稳自相关需求库存实验", "", f"更新时间：{summary['created_utc']}", "",
             f"**状态：{'完整' if summary['complete'] else '尚未完成'}。主实验 H=200 已有 {summary['primary_h200_available']}/18 组；两种初始化和四个窗口全部评价 {summary['primary_fully_evaluated']}/18 组。**",
             f"已读主实验窗口 {summary['primary_windows']}/144，基线窗口 {baseline_rows}/336。pilot/非主实验行 {summary['pilot_or_nonprimary_rows']}，另有 horizon-refit 扩展行 {summary['extension_rows']}；均不补足主实验分母。", "",
             "## 比较口径", "",
             "主策略在真实需求预热 500 期后，以 H=200 的训练成本优化；冻结同一策略评价 H=50/100/200/500。四个窗口共享同一路径前缀，不能当作独立重复。稳态需求从不变分布初始化；库存仅经过有限预热，属于近似稳态。冷启动从空库存与空 pipeline 开始，没有免费零需求备货期。",
             "所有方法观察同样的上一期完整需求、当前库存、按到货日期分桶的 pipeline 与当前交货报价；不观察当前/未来需求或未来报价。随机交货期允许跨单到货。所有边际为连续 Exponential(mean=100)，潜在 AR 系数不等于需求 Pearson 自相关。",
             "完整 self-evolve 的三个重复全部报告，不按测试成本选最好一轮；样本 SD 使用 n−1 分母。下表满足率为总销售量/总需求量。按训练成本选取的参考基线只有在七个族都完成时才用于 best-of-7 摘要，全部基线仍分别保留。",
             "配对置信区间重采样完整路径，不重采样单个 period。跨重复的区间先在每条路径上平均各冻结策略成本，再重采样路径，描述这些策略的平均表现，既不是实际组合策略，也不包含生成不确定性；生成差异另以三次 SD 展示。逐格区间未作多重比较校正。", "",
             "## 需求诊断（仅训练集）", "", "![Training demand diagnostics](figures/dataset_diagnostics.png)", "",
             "需求分布及相关结构在查看策略测试收益前固定；不得因为某些环境没有赢而删除。", "",
             "## 主表：预热后 H=200", "", *_main_table(records, repeats, "steady"), "",
             "![Steady H200 cost comparison](figures/steady_h200.png)", "",
             "## 四个评价窗口", "", "![Horizon curves](figures/horizon_curves.png)", "",
             "曲线阴影为已完成生成重复之间的 ±1 样本 SD，不是路径抽样 CI。缺失重复不补值。若库存和需求都恰处稳态，stationary 策略的期望单位期成本不因 H 改变；有限样本和近似预热会造成曲线差异。", "",
             "## 冷启动：H=200（独立口径）", "", *_main_table(records, repeats, "cold_start"), "",
             "![Cold-start H200 cost comparison](figures/cold_start_h200.png)", "",
             "## 完整结果与核查", "",
             "- [全部策略与逐重复指标](tables/all_results.csv)", "- [三次生成均值与样本 SD](tables/repeats.csv)",
             "- [各重复及重复均值的逐基线配对比较](tables/paired.csv)", "- [18 个主实验组覆盖情况](tables/coverage.csv)",
             "- [按训练成本选择的基线](tables/best_training_baselines.csv)", "- [主表与完整训练选定参考的比较](tables/main_vs_best_training_baseline.csv)",
             "- [可机读状态及检查问题](analysis_summary.json)", "",
             "PIL 为投影库存水平策略的数值适配。随机交货期下 committed-only 与 COP continuation 的投影假设不同，不能视为同一个精确策略；本实验不声称最优性证明。", ""]
    if issues:
        lines += ["### 尚待解决的记录问题", "", *("- " + json.dumps(x, ensure_ascii=False) for x in issues), ""]
    if summary.get("plot_error"):
        lines += ["图形尚未全部更新：" + summary["plot_error"], ""]
    (root / "report.md").write_text("\n".join(lines))
    _write_json(root / "analysis_summary.json", summary)
    return summary


def render_plots(run_dir):
    """Plot saved train demand and saved summary tables only; no policy calls."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    root = Path(run_dir)
    destination = root / "figures"
    destination.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False,
                         "figure.facecolor": "white", "axes.facecolor": "white", "savefig.facecolor": "white"})
    specs = scenario_specs()
    colors = ("#4477AA", "#EE6677", "#228833", "#CCBB44")
    fig, axes = plt.subplots(2, 3, figsize=(14, 7.8))
    trace_axes = [axes[0, 0], axes[0, 1], axes[0, 2], axes[1, 0]]
    for spec, color, ax in zip(specs[:4], colors, trace_axes):
        path = root / "datasets" / spec.scenario_id / "train.npz"
        if not path.exists():
            ax.text(.5, .5, "Training tape pending", ha="center", transform=ax.transAxes)
            continue
        with np.load(path, allow_pickle=False) as archive:
            demand = np.asarray(archive["demands"])
        ax.plot(np.arange(150), demand[0, :150], color=color, linewidth=1.3)
        ax.axhline(100, color="0.65", linewidth=.8, linestyle="--")
        ax.set(title=SHORT_SCENARIOS[spec.scenario_id], xlabel="Period (first training path)", ylabel="Demand")
        axes[1, 1].hist(demand.ravel(), bins=np.linspace(0, 600, 61), density=False,
                        weights=np.full(demand.size, 1 / demand.size / 10), histtype="step", color=color,
                        label=SHORT_SCENARIOS[spec.scenario_id].split(" | ")[0], linewidth=1.3)
        centered = demand - demand.mean()
        acf = [np.mean(centered[:, :-k] * centered[:, k:]) / demand.var() for k in range(1, 31)]
        axes[1, 2].plot(range(1, 31), acf, color=color, label=SHORT_SCENARIOS[spec.scenario_id].split(" | ")[0])
    x = np.linspace(0, 600, 300)
    axes[1, 1].plot(x, np.exp(-x / 100) / 100, color="black", linestyle="--", linewidth=1.2, label="Exponential(100)")
    axes[1, 1].set(title="Same marginal law", xlabel="Demand (display 0–600)", ylabel="Density")
    axes[1, 1].legend(fontsize=8)
    axes[1, 2].axhline(0, color="0.65", linewidth=.8)
    axes[1, 2].set(title="Observed demand autocorrelation", xlabel="Lag", ylabel="Pearson ACF")
    axes[1, 2].legend(fontsize=8)
    fig.suptitle("Stationary demand: matched exponential margins, different dependence", fontsize=16, y=.99)
    fig.text(.5, .015, "Training data only. Random-lead arms reuse IID/regime demand paths; quoted lead is 3 or 9 with equal probability.", ha="center", fontsize=10)
    fig.tight_layout(rect=(0, .04, 1, .955))
    fig.savefig(destination / "dataset_diagnostics.png", dpi=180)
    plt.close(fig)

    with (root / "tables" / "all_results.csv").open(newline="") as handle:
        rows = list(csv.DictReader(handle))
    with (root / "tables" / "repeats.csv").open(newline="") as handle:
        repeats = list(csv.DictReader(handle))
    palette = dict(zip(BASELINES, ("#4477AA", "#66CCEE", "#228833", "#CCBB44", "#AA3377", "#EE6677", "#999999")))
    for mode in ("steady", "cold_start"):
        fig, axs = plt.subplots(2, 3, figsize=(15, 8.5), sharex=False)
        for spec, ax in zip(specs, axs.flat):
            subset = [r for r in rows if r["scenario_id"] == spec.scenario_id and r["mode"] == mode and r["horizon"] == "200"]
            positions, values, labels, paint = [], [], [], []
            for index, family in enumerate(BASELINES):
                item = next((r for r in subset if r["family"] == family and r["scope"] == "baseline"), None)
                if item:
                    positions.append(index); values.append(float(item["mean_cost_per_period"])); labels.append(LABELS[family]); paint.append(palette[family])
            if values:
                ax.barh(positions, values, color=paint, alpha=.8)
            own = [r for r in subset if r["scope"] == "primary"]
            if own:
                costs = [float(r["mean_cost_per_period"]) for r in own]
                ax.barh([7], [np.mean(costs)], color="black", alpha=.7)
                ax.scatter(costs, np.linspace(6.88, 7.12, len(costs)), color="white", edgecolor="black", zorder=4, s=24)
            ax.set_yticks(range(8), [LABELS[x] for x in BASELINES] + [f"Self-evolve ({len(own)}/3)"])
            ax.invert_yaxis()
            ax.set(title=SHORT_SCENARIOS[spec.scenario_id], xlabel="Mean cost per period (lower is better)")
            if not subset:
                ax.text(.5, .5, "Evaluation pending", transform=ax.transAxes, ha="center", color="0.45")
        fig.suptitle(("After 500-period burn-in" if mode == "steady" else "Cold start, no free preparation") + " | Evaluation H=200", fontsize=16, y=.99)
        fig.text(.5, .012, "All primary rules trained at H=200; self-evolve bar averages available independent repeats, dots show each repeat. No best-test selection.", ha="center", fontsize=10)
        fig.tight_layout(rect=(0, .035, 1, .955))
        fig.savefig(destination / (mode + "_h200.png"), dpi=170)
        plt.close(fig)
    fig, axs = plt.subplots(2, 3, figsize=(14, 8), sharex=True)
    for spec, ax in zip(specs, axs.flat):
        for family in BASELINES:
            sub = sorted((r for r in rows if r["scenario_id"] == spec.scenario_id and r["mode"] == "steady" and r["family"] == family and r["scope"] == "baseline"), key=lambda r: int(r["horizon"]))
            if sub:
                ax.plot([int(r["horizon"]) for r in sub], [float(r["mean_cost_per_period"]) for r in sub], marker=".", color=palette[family], label=LABELS[family])
        own = sorted((r for r in repeats if r["scenario_id"] == spec.scenario_id and r["mode"] == "steady"), key=lambda r: int(r["horizon"]))
        if own:
            h = np.array([int(r["horizon"]) for r in own]); means = np.array([float(r["mean_cost_per_period_mean"]) for r in own])
            sd = np.array([float(r["mean_cost_per_period_sd"]) if r["mean_cost_per_period_sd"] else np.nan for r in own])
            ax.plot(h, means, "o-", color="black", linewidth=2, label="Self-evolve mean")
            ax.fill_between(h, means-sd, means+sd, color="black", alpha=.12)
        ax.set(title=SHORT_SCENARIOS[spec.scenario_id], xlabel="Evaluation horizon", ylabel="Mean cost per period")
        ax.set_xscale("log"); ax.set_xticks(HORIZONS, list(map(str, HORIZONS))); ax.grid(alpha=.15)
    handles, labels = [], []
    for ax in axs.flat:
        h, l = ax.get_legend_handles_labels()
        for handle, label in zip(h, l):
            if label not in labels:
                handles.append(handle); labels.append(label)
    if handles:
        fig.legend(handles, labels, loc="lower center", ncol=4, frameon=False, fontsize=9)
    fig.suptitle("Frozen H=200 policies across nested evaluation horizons", fontsize=16, y=.99)
    fig.text(.5, .07, "500-period burn-in. Shading: ±1 sample SD across generated repeats, not a confidence interval. Horizons share paths.", ha="center", fontsize=10)
    fig.tight_layout(rect=(0, .105, 1, .955))
    fig.savefig(destination / "horizon_curves.png", dpi=180)
    plt.close(fig)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--bootstrap", type=int, default=5000)
    parser.add_argument("--no-plots", action="store_true")
    parser.add_argument("--plot-runtime", type=Path)
    parser.add_argument("--plots-only", action="store_true")
    args = parser.parse_args()
    if args.plots_only:
        render_plots(args.run_dir)
    else:
        result = report(args.run_dir, n_bootstrap=args.bootstrap, make_plots=not args.no_plots, plot_runtime=args.plot_runtime)
        print(json.dumps({key: result[key] for key in ("status", "primary_h200_available", "primary_fully_evaluated", "total_rows", "paired_rows", "issues")}, ensure_ascii=False))
