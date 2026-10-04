"""Incremental reporting for Adaptive-PIL-seeded evolution; never runs policies."""
from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import gzip
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import sys

import numpy as np

from .analysis_report import HORIZONS, NPZ_METRICS, load_evaluations, _write_csv, _write_json
from .data import scenario_specs
from ..baek_comparison.analysis import paired_statistics


PIL_FAMILIES = ("forecast_adaptive_pil", "conditional_pil", "pil_cop_continuation")
REFERENCES = (*PIL_FAMILIES, "capped_evolve", "unrestricted_evolve")
LABELS = {"forecast_adaptive_pil": "Adaptive PIL（原起点）", "conditional_pil": "Conditional PIL",
          "pil_cop_continuation": "PIL + COP", "capped_evolve": "原 base-stock 起点，有参数上限",
          "unrestricted_evolve": "base-stock 起点，无参数上限"}
MODES = ("steady", "cold_start")
BOOTSTRAP_SEED = 2026091611
VERSION = "adaptive-pil-report-v1"
DEFAULT_PRIOR_COMMITMENT = 1.82576175


def _read(path, default=None):
    return json.loads(path.read_text()) if path.exists() else default


def _sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _finite(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def _load(root, label):
    records, problems = load_evaluations(root)
    issues = [{"run": label, **item} for item in problems]
    kept, baseline_cache = [], {}
    for item in records:
        row = item["row"]
        if row["source_training_horizon"] != 200:
            continue
        if row["scope"] != "primary" and not (row["scope"] == "baseline" and row["family"] in PIL_FAMILIES):
            continue
        try:
            if not row["provenance_verified"]:
                raise ValueError("Evaluation lacks dataset or policy provenance")
            sid, pid = row["scenario_id"], row["policy_id"]
            if row["family"] == "self_evolve":
                directory = root / "training" / sid / pid
                completion = _read(directory / "completed.json", {})
                if (completion.get("status") not in {"complete", "completed"}
                        or completion.get("full_protocol") is not True
                        or completion.get("scenario_id") != sid or completion.get("policy_id") != pid
                        or completion.get("source_training_horizon") != 200
                        or completion.get("repeat") != row["repeat"]
                        or completion.get("code_sha256") != row["code_sha256"]
                        or _sha(directory / "policy.py") != row["code_sha256"]):
                    raise ValueError("Evaluation differs from frozen generated source/completion")
            else:
                if sid not in baseline_cache:
                    baseline_cache[sid] = _read(root / "baselines" / sid / "h200/records.json", {})
                record = baseline_cache[sid][row["family"]]
                digest = hashlib.sha256(json.dumps(record, sort_keys=True).encode()).hexdigest()
                if row.get("record_sha256") != digest:
                    raise ValueError("Evaluation differs from fitted baseline record")
            kept.append(item)
        except (KeyError, OSError, TypeError, ValueError) as exc:
            issues.append(dict(run=label, scenario_id=row["scenario_id"], policy_id=row["policy_id"], error=str(exc)))
    return kept, issues


def _average_three(items):
    """Return no estimate until all three planned generated policies are present."""
    if len(items) != 3 or {x["row"]["repeat"] for x in items} != {1, 2, 3}:
        return None
    items = sorted(items, key=lambda item: item["row"]["repeat"])
    first = items[0]
    for item in items[1:]:
        if (item["row"]["dataset_arrays_sha256"] != first["row"]["dataset_arrays_sha256"]
                or not np.array_equal(item["arrays"]["demand_units"], first["arrays"]["demand_units"])):
            raise ValueError("Generated repeats do not share ordered demand paths")
    arrays = {name: np.mean(np.stack([item["arrays"][name] for item in items]), axis=0) for name in NPZ_METRICS}
    arrays["demand_units"] = first["arrays"]["demand_units"].copy()
    means = [item["row"]["mean_cost_per_period"] for item in items]
    return dict(row=first["row"], arrays=arrays, mean=float(np.mean(means)),
                generation_sd=float(np.std(means, ddof=1)), n_repeats=3)


def _pair(candidate, reference):
    if (candidate["row"]["dataset_arrays_sha256"] != reference["row"]["dataset_arrays_sha256"]
            or candidate["arrays"]["total_cost"].shape != reference["arrays"]["total_cost"].shape
            or not np.array_equal(candidate["arrays"]["demand_units"], reference["arrays"]["demand_units"])):
        raise ValueError("Reference and candidate lack identical ordered demand paths")


def _stats(candidate, reference, horizon, root, n_bootstrap):
    cand, ref = candidate["arrays"]["total_cost"] / horizon, reference["arrays"]["total_cost"] / horizon
    key = dict(version=VERSION, seed=BOOTSTRAP_SEED, n_bootstrap=n_bootstrap,
               candidate=hashlib.sha256(np.ascontiguousarray(cand, dtype="<f8").tobytes()).hexdigest(),
               reference=hashlib.sha256(np.ascontiguousarray(ref, dtype="<f8").tobytes()).hexdigest())
    target = root / "adaptive_pil_analysis_cache" / (hashlib.sha256(json.dumps(key, sort_keys=True).encode()).hexdigest() + ".json")
    result = _read(target)
    if result is None:
        result = paired_statistics(cand, ref, seed=BOOTSTRAP_SEED, n_bootstrap=n_bootstrap)
        _write_json(target, result)
    return result


def training_progress(root):
    """Original baseline, automatic generation-zero retuning, then generations 1–10."""
    curves, improvements, issues = [], [], []
    for spec in scenario_specs():
        sid = spec.scenario_id
        baseline = _read(root / "baselines" / sid / "h200/records.json", {}).get("forecast_adaptive_pil", {})
        seed_cost = baseline.get("training", {}).get("mean_cost_per_period")
        seed_cost = float(seed_cost) if _finite(seed_cost) else None
        for repeat in (1, 2, 3):
            directory = root / "training" / sid / f"self_evolve_h200_r{repeat}"
            common = dict(scenario_id=sid, repeat=repeat, policy_id=directory.name, training_horizon=200)
            if seed_cost is not None:
                curves.append(dict(**common, stage="original_adaptive_pil", generation=-1,
                                   mean_train_cost_per_period=seed_cost))
            zero_cost = None
            path = directory / "pops/population_generation_0.json"
            if path.exists():
                try:
                    population = _read(path)
                    individual = population[0] if isinstance(population, list) else population
                    value = individual["objective"]
                    if not _finite(value):
                        raise ValueError("Non-finite generation-zero training objective")
                    zero_cost = float(value) / 200
                    curves.append(dict(**common, stage="automatically_retuned_gen0", generation=0,
                                       mean_train_cost_per_period=zero_cost))
                except (KeyError, IndexError, TypeError, ValueError, OSError) as exc:
                    issues.append(dict(file=str(path.relative_to(root)), error=str(exc)))
            for path in sorted((directory / "checkpoints").glob("g*.json.gz")):
                try:
                    with gzip.open(path, "rt") as handle:
                        saved = json.load(handle)
                    generation, value = saved["generation"], saved["best_train_cost"]
                    if not isinstance(generation, int) or not 1 <= generation <= 10 or not _finite(value):
                        raise ValueError("Invalid training checkpoint")
                    if path.name != f"g{generation:03d}.json.gz":
                        raise ValueError("Checkpoint filename/generation mismatch")
                    curves.append(dict(**common, stage="evolved", generation=generation,
                                       mean_train_cost_per_period=float(value) / 200))
                except (KeyError, TypeError, ValueError, OSError, EOFError) as exc:
                    issues.append(dict(file=str(path.relative_to(root)), error=str(exc)))
            final = _read(directory / "completed.json", {})
            value = final.get("best_train_cost")
            final_cost = float(value) / 200 if final.get("status") in {"complete", "completed"} and _finite(value) else None
            row = dict(**common, original_adaptive_train_cost_per_period=seed_cost,
                       optimized_gen0_train_cost_per_period=zero_cost, final_train_cost_per_period=final_cost,
                       final_available=final_cost is not None)
            row["seed_to_final_cost_reduction"] = seed_cost-final_cost if seed_cost is not None and final_cost is not None else None
            row["seed_to_final_improvement_pct"] = 100*(seed_cost-final_cost)/seed_cost if seed_cost and final_cost is not None else None
            row["gen0_to_final_cost_reduction"] = zero_cost-final_cost if zero_cost is not None and final_cost is not None else None
            improvements.append(row)
    return curves, improvements, issues


def budget_accounting(root, unrestricted_root):
    config = _read(root / "protocol.json", {}).get("configuration", {})
    raw = config.get("shared_budget_run_dir")
    shared = Path(raw).expanduser() if raw else unrestricted_root
    if not shared.is_absolute():
        shared = root / shared
    shared = shared.resolve()
    ledger = _read(shared / "api_budget.json")
    prior = config.get("previous_committed_upper_usd", DEFAULT_PRIOR_COMMITMENT)
    if not _finite(prior) or prior < 0:
        raise ValueError("Invalid prior experiment commitment")
    result = dict(available=ledger is not None, shared_budget_run_dir=str(shared),
                  previous_committed_upper_usd=prior, previous_commitment_added_once=True,
                  session_limit_usd=config.get("session_budget_usd", 20.), buckets={}, issues=[])
    if ledger is None:
        return result
    def empty():
        return dict(requests=0, known_cost_usd=0., uncertain_requests=0, uncertain_held_upper_usd=0.,
                    pending_requests=0, pending_upper_usd=0.)
    buckets = {key: empty() for key in ("this_run", "other_runs", "unattributed", "shared_global")}
    for request in ledger.get("requests", {}).values():
        chain = request.get("metadata", {}).get("chain_dir")
        category = "unattributed"
        if chain:
            chain_path = Path(chain).expanduser()
            if not chain_path.is_absolute():
                chain_path = shared / chain_path
            category = "this_run" if chain_path.resolve().is_relative_to(root) else "other_runs"
        state = request.get("state")
        known = request.get("actual_cost_usd")
        known = 0. if known is None else known
        reserved = request.get("reserved_usd", 0.)
        if (state not in {"complete", "unknown_charge", "missing_cost", "pending"}
                or not all(_finite(x) and x >= 0 for x in (known, reserved))):
            result["issues"].append("Invalid request accounting state/amount")
            result["available"] = False
            continue
        for target in (buckets[category], buckets["shared_global"]):
            target["requests"] += 1
            target["known_cost_usd"] += known
            target["uncertain_requests"] += int(state in {"unknown_charge", "missing_cost"})
            target["uncertain_held_upper_usd"] += reserved if state in {"unknown_charge", "missing_cost"} else 0.
            target["pending_requests"] += int(state == "pending")
            target["pending_upper_usd"] += reserved if state == "pending" else 0.
    for bucket in buckets.values():
        bucket["committed_upper_usd"] = bucket["known_cost_usd"] + bucket["uncertain_held_upper_usd"] + bucket["pending_upper_usd"]
    result.update(buckets=buckets, shared_limit_usd=ledger.get("limit_usd"),
                  session_committed_upper_usd=prior+buckets["shared_global"]["committed_upper_usd"])
    return result


def report(run_dir, capped_run, unrestricted_run, *, n_bootstrap=5000, make_plots=True, plot_runtime=None):
    if isinstance(n_bootstrap, bool) or not isinstance(n_bootstrap, int) or n_bootstrap < 1:
        raise ValueError("n_bootstrap must be a positive integer")
    root = Path(run_dir).resolve()
    roots = dict(warmstart=root, capped=Path(capped_run).resolve(), unrestricted=Path(unrestricted_run).resolve())
    loaded, issues, groups, baseline_lookup = {}, [], {}, {}
    for label, directory in roots.items():
        loaded[label], problems = _load(directory, label)
        issues.extend(problems)
        for item in loaded[label]:
            r = item["row"]
            key = (label, r["scenario_id"], r["mode"], r["horizon"])
            if r["family"] == "self_evolve":
                groups.setdefault(key, []).append(item)
            elif label == "warmstart":
                baseline_lookup[(*key[1:], r["family"])] = item
    averages = {}
    for key, items in groups.items():
        try:
            averages[key] = _average_three(items)
        except ValueError as exc:
            averages[key] = None
            issues.append(dict(run=key[0], scenario_id=key[1], mode=key[2], horizon=key[3], error=str(exc)))
    windows, comparisons, coverage = [], [], []
    for spec in scenario_specs():
        sid = spec.scenario_id
        for repeat in (1, 2, 3):
            present = {(x["row"]["mode"], x["row"]["horizon"]) for x in loaded["warmstart"]
                       if x["row"]["family"] == "self_evolve" and x["row"]["scenario_id"] == sid and x["row"]["repeat"] == repeat}
            coverage.append(dict(scenario_id=sid, repeat=repeat, available_windows=len(present), expected_windows=8, complete=len(present)==8))
        for mode in MODES:
            for horizon in HORIZONS:
                candidate = averages.get(("warmstart", sid, mode, horizon))
                row = dict(scenario_id=sid, mode=mode, horizon=horizon,
                           new_n_repeats=len(groups.get(("warmstart", sid, mode, horizon), [])),
                           new_planned_repeats=3, new_mean_cost_per_period=candidate["mean"] if candidate else None,
                           new_generation_sd=candidate["generation_sd"] if candidate else None,
                           primary_ready=False)
                primary_ready = candidate is not None
                for name in REFERENCES:
                    reference = (baseline_lookup.get((sid, mode, horizon, name)) if name in PIL_FAMILIES
                                 else averages.get((name.removesuffix("_evolve"), sid, mode, horizon)))
                    comparison = dict(scenario_id=sid, mode=mode, horizon=horizon, reference=name,
                                      status="pending", candidate_repeats=3,
                                      reference_repeats=1 if name in PIL_FAMILIES else 3)
                    row[name + "_mean_cost_per_period"] = (reference["row"]["mean_cost_per_period"] if name in PIL_FAMILIES
                                                            else reference["mean"]) if reference else None
                    row[name + "_generation_sd"] = reference.get("generation_sd") if reference else None
                    if candidate is not None and reference is not None:
                        try:
                            _pair(candidate, reference)
                            comparison.update(_stats(candidate, reference, horizon, root, n_bootstrap), status="complete",
                                              candidate_generation_sd=candidate["generation_sd"],
                                              reference_generation_sd=reference.get("generation_sd"),
                                              dataset_arrays_sha256=candidate["row"]["dataset_arrays_sha256"])
                        except ValueError as exc:
                            comparison.update(status="pairing_error", error=str(exc))
                            issues.append(dict(run="warmstart" if name in PIL_FAMILIES else name,
                                               scenario_id=sid, mode=mode, horizon=horizon, error=str(exc)))
                    row[name + "_status"] = comparison["status"]
                    if name in PIL_FAMILIES:
                        primary_ready &= comparison["status"] == "complete"
                    comparisons.append(comparison)
                row["primary_ready"] = bool(primary_ready)
                windows.append(row)
    curves, improvements, training_issues = training_progress(root)
    account = budget_accounting(root, roots["unrestricted"])
    completed_primary = all(r["primary_ready"] for r in windows) and all(r["complete"] for r in coverage) and not any(x["run"] == "warmstart" for x in issues)
    all_complete = completed_primary and all(r["status"] == "complete" for r in comparisons) and not issues
    summary = dict(version=VERSION, created_utc=datetime.now(timezone.utc).isoformat(),
                   status="completed_all_comparisons" if all_complete else "completed_primary" if completed_primary else "pending_primary",
                   completed_primary=completed_primary, completed_all_comparisons=all_complete,
                   expected_primary_runs=18, completed_primary_runs=sum(r["complete"] for r in coverage),
                   expected_windows=48, primary_ready_windows=sum(r["primary_ready"] for r in windows),
                   expected_comparisons=240, completed_comparisons=sum(r["status"] == "complete" for r in comparisons),
                   old_comparison_pending=any(r["status"] != "complete" for r in comparisons if r["reference"] not in PIL_FAMILIES),
                   roots={name: str(path) for name, path in roots.items()}, windows=windows, coverage=coverage,
                   comparisons=comparisons, training_improvements=improvements, training_issues=training_issues,
                   accounting=account, issues=issues,
                   uncertainty="paired whole-path 95% intervals; excludes generation variation; no multiplicity adjustment",
                   selection="exactly all three repeats; no partial-repeat mean and no test-best selection")
    tables = root / "tables"
    for name, rows in (("all_results", [dict(run=label, **x["row"]) for label, items in loaded.items() for x in items]),
                       ("windows", windows), ("paired", comparisons), ("coverage", coverage),
                       ("training_curves", curves), ("training_improvement", improvements),
                       ("accounting", [dict(scope=name, **value) for name, value in account["buckets"].items()])):
        _write_csv(tables / f"adaptive_pil_{name}.csv", rows)
    _write_json(root / "adaptive_pil_summary.json", summary)
    if make_plots:
        runtime = plot_runtime or ("/tmp/baek-plot-runtime-20260916" if Path("/tmp/baek-plot-runtime-20260916").exists() else None)
        env = dict(os.environ)
        if runtime:
            env["PYTHONPATH"] = str(Path(runtime).resolve()) + (os.pathsep+env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
        command = [sys.executable, "-m", "examples.inventory.correlated_benchmark.adaptive_pil_report", "--run-dir", str(root), "--plots-only"]
        result = subprocess.run(command, cwd=Path(__file__).resolve().parents[3], env=env, capture_output=True, text=True, timeout=120)
        if result.returncode:
            summary["plot_error"] = result.stderr[-1500:]
    _write_report(root, summary)
    _write_json(root / "adaptive_pil_summary.json", summary)
    return summary


def _fmt(value, digits=3):
    return "—" if value is None else f"{value:.{digits}f}"


def _ci(values):
    return "—" if values is None else "[" + ", ".join(_fmt(x) for x in values) + "]"


def _write_report(root, summary):
    lines = ["# 从 Adaptive PIL 出发的策略演化", "", f"更新时间：{summary['created_utc']}", "",
             f"**主实验：{'完成' if summary['completed_primary'] else '尚未完成'}（{summary['completed_primary_runs']}/18 条链，完整评分窗口 {summary['primary_ready_windows']}/48）。旧起点比较：{'待完成' if summary['old_comparison_pending'] else '完成'}。**", "",
             "每个环境的三次生成全部齐全后，先在每条共同测试路径上平均三个冻结策略的成本，再与参考方法配对；未齐三次时不报告不完整均值。所有成本均为每期成本，生成样本 SD 使用 n−1 分母。95% 区间重采样完整路径，只描述路径抽样不确定性，不含生成变异，未作多重比较校正；1,000 条路径不是 1,000 次模型训练。",
             "策略以 B=500、H=200 的训练目标优化，同一冻结规则评价四个 H；需求严格平稳，有限预热后的库存只近似稳态，冷启动单列。旧测试结果已经查看，此轮复用同一测试集作探索比较，不是新的未见留出验证。三次编号不代表两轮共用模型随机种子。", "",
             "## 主结果：预热后 H=200", "",
             "| 场景 | 新策略均值 | 生成 SD | Adaptive PIL 原起点 | Conditional PIL | PIL + COP | 原有上限均值（SD） | 原无上限均值（SD） |",
             "|---|---:|---:|---:|---:|---:|---:|---:|"]
    for row in summary["windows"]:
        if row["mode"] == "steady" and row["horizon"] == 200:
            values = [_fmt(row["new_mean_cost_per_period"]), _fmt(row["new_generation_sd"])]
            values += [_fmt(row[name+"_mean_cost_per_period"]) for name in PIL_FAMILIES]
            values += [f"{_fmt(row[name+'_mean_cost_per_period'])}（{_fmt(row[name+'_generation_sd'])}）"
                       if row[name+"_mean_cost_per_period"] is not None else "—"
                       for name in ("capped_evolve", "unrestricted_evolve")]
            lines.append("| " + row["scenario_id"] + " | " + " | ".join(values) + " |")
    lines += ["", "| 场景 | 参考 | 新−参考绝对差（95% CI） | 成本改善 %（95% CI） |", "|---|---|---:|---:|"]
    for row in summary["comparisons"]:
        if row["mode"] != "steady" or row["horizon"] != 200:
            continue
        difference = f"{_fmt(row['mean_cost_difference'])} {_ci(row['cost_difference_ci'])}" if row["status"] == "complete" else "待完成"
        improvement = f"{_fmt(row['improvement_pct'])} {_ci(row['improvement_pct_ci'])}" if row["status"] == "complete" else "—"
        lines.append(f"| {row['scenario_id']} | {LABELS[row['reference']]} | {difference} | {improvement} |")
    lines += ["", "绝对差为新策略减参考，负数有利；改善百分比为正数有利。全部冷启动/预热、H=50/100/200/500 的比较见[窗口表](tables/adaptive_pil_windows.csv)和[配对差值及区间](tables/adaptive_pil_paired.csv)。", "",
             "## 训练过程", "", "![Training trajectories](figures/adaptive_pil_training_curves.png)", "",
             "曲线区分原 Adaptive PIL 的训练成本、EOH 自动优化后的 generation 0，以及随后十代的训练优胜成本。原起点取 baseline record，不能以自动优化后的 generation 0 冒充原起点；优化前后差异仅是训练结果，不保证测试改善。", "",
             "| 场景 | 重复 | 原起点 | 自动优化后 g0 | 最终训练成本 | 原起点→最终训练改善 % |", "|---|---:|---:|---:|---:|---:|"]
    for row in summary["training_improvements"]:
        lines.append(f"| {row['scenario_id']} | {row['repeat']} | {_fmt(row['original_adaptive_train_cost_per_period'])} | {_fmt(row['optimized_gen0_train_cost_per_period'])} | {_fmt(row['final_train_cost_per_period'])} | {_fmt(row['seed_to_final_improvement_pct'])} |")
    lines += ["", "## API 费用归属", ""]
    account = summary["accounting"]
    if account["available"]:
        lines += ["| 范围 | 请求数 | 已知费用 $ | 未决保留上限 $ | 在途预留 $ | 占用预算上界 $ |", "|---|---:|---:|---:|---:|---:|"]
        for name, label in (("this_run", "本 Adaptive-PIL-seed 实验"), ("other_runs", "共享账本内其他实验"), ("unattributed", "未归属／预检"), ("shared_global", "共享全局（上述之和）")):
            b = account["buckets"][name]
            lines.append(f"| {label} | {b['requests']} | {b['known_cost_usd']:.6f} | {b['uncertain_held_upper_usd']:.6f} | {b['pending_upper_usd']:.6f} | {b['committed_upper_usd']:.6f} |")
        lines += ["", f"会话累计预算占用上界 = 共享全局上界 + 首轮已知与保留合计 ${account['previous_committed_upper_usd']:.8f}（仅加入一次）= **${account['session_committed_upper_usd']:.8f}**。本实验费用已经包含于共享全局，不能再加一次；未决保留不是已确认收费。", ""]
    else:
        lines += ["共享账本尚未提供或账务记录待核对，费用暂不汇总。", ""]
    lines += ["## 记录", "", "- [机器可读状态](adaptive_pil_summary.json)", "- [18 条链覆盖](tables/adaptive_pil_coverage.csv)",
              "- [逐代训练成本](tables/adaptive_pil_training_curves.csv)", "- [各轮原始指标](tables/adaptive_pil_all_results.csv)", ""]
    if summary["issues"] or summary["training_issues"] or account["issues"]:
        lines += ["待核对记录见机器可读状态；存在错误的比较不会标为完成。", ""]
    if summary.get("plot_error"):
        lines += ["训练图尚未生成：" + summary["plot_error"], ""]
    (root / "adaptive_pil_report.md").write_text("\n".join(lines))


def render_plots(run_dir):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    root = Path(run_dir)
    with (root / "tables/adaptive_pil_training_curves.csv").open() as handle:
        rows = list(csv.DictReader(handle))
    fig, axes = plt.subplots(2, 3, figsize=(14, 8))
    colors = ("#4477AA", "#228833", "#EE6677")
    for spec, ax in zip(scenario_specs(), axes.flat):
        local = [row for row in rows if row["scenario_id"] == spec.scenario_id]
        baseline = next((float(row["mean_train_cost_per_period"]) for row in local if row["stage"] == "original_adaptive_pil"), None)
        if baseline is not None:
            ax.axhline(baseline, color="0.3", linestyle="--", linewidth=1, label="Original Adaptive PIL")
        for repeat, color in zip((1, 2, 3), colors):
            curve = sorted((r for r in local if int(r["repeat"]) == repeat and int(r["generation"]) >= 0), key=lambda r: int(r["generation"]))
            if curve:
                ax.plot([int(r["generation"]) for r in curve], [float(r["mean_train_cost_per_period"]) for r in curve],
                        marker="o", markersize=3, color=color, label=f"Repeat {repeat}")
        if not any(int(row["generation"]) >= 0 for row in local):
            ax.text(.5, .5, "Training results pending", transform=ax.transAxes, ha="center")
        ax.set(title=spec.scenario_id.replace("exp_", ""), xlabel="Generation (0 = automatic seed retuning)", ylabel="Training cost per period", xlim=(-.3, 10.3))
        ax.grid(alpha=.2)
    handles = {}
    for ax in axes.flat:
        h, l = ax.get_legend_handles_labels()
        for handle, label in zip(h, l):
            handles[label] = handle
    if handles:
        fig.legend(handles.values(), handles.keys(), loc="lower center", ncol=4)
    fig.suptitle("Adaptive-PIL-seeded evolution | Train N=50, B=500, H=200", fontsize=15)
    fig.tight_layout(rect=(0, .055, 1, .95))
    (root / "figures").mkdir(exist_ok=True)
    fig.savefig(root / "figures/adaptive_pil_training_curves.png", dpi=160)
    plt.close(fig)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--capped-run", type=Path)
    parser.add_argument("--unrestricted-run", type=Path)
    parser.add_argument("--bootstrap", type=int, default=5000)
    parser.add_argument("--no-plots", action="store_true")
    parser.add_argument("--plot-runtime", type=Path)
    parser.add_argument("--plots-only", action="store_true")
    args = parser.parse_args()
    if args.plots_only:
        render_plots(args.run_dir)
    else:
        if args.capped_run is None or args.unrestricted_run is None:
            parser.error("--capped-run and --unrestricted-run are required")
        answer = report(args.run_dir, args.capped_run, args.unrestricted_run, n_bootstrap=args.bootstrap,
                        make_plots=not args.no_plots, plot_runtime=args.plot_runtime)
        print(json.dumps({key: answer[key] for key in ("status", "completed_primary", "old_comparison_pending", "completed_comparisons")}))
