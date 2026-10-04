"""Read-only report builder for frozen overnight scores; never runs policies/API.

Main input: RUN/test/<method>.json, with results[scenario] containing cost,
path_costs, metrics=[waste,lost,order], and theta. Importing this module reads no
result files. --self-test uses only a synthetic temporary directory.
"""
from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import tempfile

import numpy as np


REPO = Path(__file__).resolve().parents[3]
DEFAULT_RUN = REPO / "output/overnight_search/20260917"
ARMS = ("one_query", "best_of_n", "evolution", "baek")
PRINCIPAL = tuple(f"{arm}_r{r}" for arm in ARMS for r in (1, 2, 3))
BASELINES = tuple("baseline_" + x for x in (
    "constant", "base_stock", "capped_base_stock", "age_discount", "bsp_low_ew_mixed_l2"))
LABELS = {"one_query": "单次查询（4 个结构）", "best_of_n": "独立生成择优（8 个结构）",
          "evolution": "反馈演化（8 个结构）", "baek": "Baek-style L2 工具会话",
          "baseline_constant": "常量订货", "baseline_base_stock": "Base-stock",
          "baseline_capped_base_stock": "Capped base-stock", "baseline_age_discount": "年龄折扣",
          "baseline_bsp_low_ew_mixed_l2": "BSP-low-EW（混合 issuing 适配）"}


def grid():
    return [dict(name=f"perish_m{m}_L2_cv{cv:g}_f{f:g}", m=m, L=2, cv=cv, f=f,
                 split="discovery" if m in (3, 5) else "transfer")
            for m in (3, 4, 5) for cv in (1.5, 2.0) for f in (0.0, 0.5)]


def read_json(path):
    return json.loads(Path(path).read_text())


def write_json(path, value):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n")


def write_csv(path, rows, columns):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with Path(path).open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def load_scores(run):
    data, metadata, problems = {}, {}, []
    directory = run / "test"
    for path in sorted(directory.glob("*.json")):
        method = path.stem
        if method not in PRINCIPAL + BASELINES and not method.endswith("_without_tuning"):
            continue
        try:
            obj = read_json(path)
            if not isinstance(obj.get("results"), dict):
                raise ValueError("缺少 results 对象")
            rows = {}
            for spec in grid():
                name = spec["name"]
                if name not in obj["results"]:
                    problems.append(f"{method}/{name}: 缺少场景")
                    continue
                raw = obj["results"][name]
                try:
                    paths = np.asarray(raw["path_costs"], dtype=float)
                    cost = float(raw["cost"])
                    if paths.ndim != 1 or len(paths) < 1 or not np.isfinite(paths).all():
                        raise ValueError("path_costs 必须是一维、非空、有限值数组")
                    if not np.isfinite(cost) or cost < 0 or np.min(paths) < 0:
                        raise ValueError("费用必须非负且有限")
                    if not np.isclose(paths.mean(), cost, rtol=1e-9, atol=1e-8):
                        raise ValueError("cost 与 path_costs 均值不一致")
                    rows[name] = {**raw, "cost": cost, "paths": paths}
                except (ValueError, KeyError, TypeError) as error:
                    problems.append(f"{method}/{name}: {error}")
            data[method] = rows
            metadata[method] = {k: v for k, v in obj.items() if k != "results"}
        except (ValueError, KeyError, TypeError, OSError) as error:
            problems.append(f"{path.name}: {error}")
    for method in PRINCIPAL + BASELINES:
        if method not in data:
            problems.append(f"{method}: 缺少有效测试文件")
    return data, metadata, problems


def group_scores(data):
    groups = {baseline: {} for baseline in BASELINES}
    groups.update({arm: {} for arm in ARMS})
    for name in (x["name"] for x in grid()):
        for arm in ARMS:
            records = [data.get(f"{arm}_r{repeat}", {}).get(name) for repeat in (1, 2, 3)]
            if any(row is None for row in records):
                continue
            if len({len(row["paths"]) for row in records}) != 1:
                continue
            paths = np.stack([row["paths"] for row in records])
            means = paths.mean(axis=1)
            groups[arm][name] = dict(cost=float(means.mean()), paths=paths.mean(axis=0),
                                    generation_sd=float(means.std(ddof=1)), generation_costs=means.tolist(),
                                    generations=3, worst=float(means.max()), best=float(means.min()))
        for baseline in BASELINES:
            row = data.get(baseline, {}).get(name)
            if row is not None:
                groups[baseline][name] = dict(cost=row["cost"], paths=row["paths"],
                                             generation_sd=None, generation_costs=[row["cost"]],
                                             generations=1, worst=row["cost"], best=row["cost"])
    return groups


def paired_comparison(candidate, reference, *, key, draws=5000):
    """Conditional uncertainty across common demand paths, not generation CI."""
    x, y = candidate["paths"], reference["paths"]
    if len(x) != len(y) or len(x) < 2:
        return None
    delta = float(y.mean() - x.mean())
    gain = 100 * delta / float(y.mean()) if y.mean() > 0 else None
    seed = int.from_bytes(hashlib.sha256(key.encode()).digest()[:8], "little")
    rng = np.random.default_rng(seed)
    absolute, percentages = [], []
    # Bound memory independently of the number of requested resamples.
    for lo in range(0, draws, 256):
        indices = rng.integers(0, len(x), size=(min(256, draws - lo), len(x)))
        xmean, ymean = x[indices].mean(axis=1), y[indices].mean(axis=1)
        absolute.extend((ymean - xmean).tolist())
        valid = ymean > 0
        percentages.extend((100 * (ymean[valid] - xmean[valid]) / ymean[valid]).tolist())
    lo, hi = np.percentile(absolute, [2.5, 97.5]).tolist()
    plo, phi = (np.percentile(percentages, [2.5, 97.5]).tolist()
                 if percentages else (None, None))
    return dict(candidate_cost=candidate["cost"], reference_cost=reference["cost"],
                improvement_pct=gain, improvement_ci_low=plo, improvement_ci_high=phi,
                absolute_improvement=delta, absolute_ci_low=lo, absolute_ci_high=hi,
                paths=len(x), bootstrap_draws=draws,
                path_ci_excludes_zero=bool(lo > 0 or hi < 0))


def load_dp_test(path, scenario_name, expected_settings):
    """Validate the DP test score and its declared common-path protocol."""
    raw = read_json(path)
    if not isinstance(raw, dict) or raw.get("scenario") != scenario_name:
        raise ValueError("DP测试场景身份不一致")
    test = raw["test"]
    if not isinstance(test, dict) or not isinstance(expected_settings, dict) or any(
            key not in expected_settings or test.get(key) != expected_settings[key]
            for key in ("seed", "paths", "burnin", "horizon")):
        raise ValueError("DP测试设置与冻结protocol.json中的test设置不一致或缺失")
    paths = np.asarray(test["path_costs"], dtype=float)
    cost = float(test["mean"])
    if (paths.ndim != 1 or len(paths) < 2 or len(paths) != test["paths"]
            or not np.isfinite(paths).all() or np.min(paths) < 0
            or not np.isfinite(cost) or cost < 0):
        raise ValueError("DP逐路径成本或路径数无效")
    if not np.isclose(paths.mean(), cost, rtol=1e-9, atol=1e-8):
        raise ValueError("DP mean与逐路径成本均值不一致")
    return dict(cost=cost, paths=paths, seed=test["seed"], burnin=test["burnin"], horizon=test["horizon"])


def budget_summary(path, label, limit):
    if not path.exists():
        return dict(component=label, limit_usd=limit, available=False, known_cost_usd=None,
                    held_upper_usd=None, committed_upper_usd=None, requests=None)
    ledger = read_json(path)
    records = list(ledger.get("requests", {}).values())
    known = 0.0
    held = 0.0
    uncertain = 0
    for row in records:
        actual = row.get("actual_cost_usd")
        if isinstance(actual, (int, float)) and not isinstance(actual, bool) and np.isfinite(actual) and actual >= 0:
            known += actual
        else:
            held += float(row.get("reserved_usd", row.get("upper_usd", 0.0)))
            uncertain += 1
    return dict(component=label, limit_usd=float(ledger.get("limit_usd", limit)), available=True,
                known_cost_usd=known, held_upper_usd=held, committed_upper_usd=known + held,
                requests=len(records), uncertain_requests=uncertain)


def ledger_usage(run):
    """Only reads ledgers; no client initialization or ledger mutation."""
    components = [budget_summary(run / "framework_budget/api_budget.json", "结构搜索", 35),
                  budget_summary(run / "baek/budget.json", "Baek L2", 12)]
    available = all(row["available"] for row in components)
    known = sum(row["known_cost_usd"] or 0 for row in components)
    held = sum(row["held_upper_usd"] or 0 for row in components)
    return dict(components=components, both_ledgers_available=available,
                recorded_known_usd=known, recorded_held_usd=held,
                recorded_committed_usd=known + held, total_budget_usd=50,
                unallocated_usd=3, within_50_if_ledgers_complete=bool(available and known + held <= 50 + 1e-9))


def fmt(value, decimals=3):
    return "缺" if value is None else f"{value:.{decimals}f}"


def link(path, label):
    return f"[{label}]({Path(path).resolve()})"


def nested_note():
    directory = Path(__file__).with_name("nested_diagnostic")
    audit_path, synthetic_path = directory / "saved_audit.json", directory / "synthetic_summary.json"
    parts = []
    if audit_path.exists():
        audit = read_json(audit_path)
        record = audit.get("saved_records", {})
        if record:
            parts.append(f"公开修正后的 Sol L2 保存结果共 {record.get('n')} 个实例，"
                         f"其中 {record.get('within_0_1_percent')} 个在已记录参照的 0.1% 范围内或更好；"
                         f"收入比最低为 {fmt(record.get('minimum_ratio'), 9)}。")
        replay_path = directory / "replay_summary.json"
        replay = read_json(replay_path).get("replay", {}) if replay_path.exists() else {}
        checks = audit.get("saved_decision_checks", {})
        if replay:
            parts.append(f"独立重跑修正后的公开算法覆盖 {replay.get('n')} 个实例，"
                         f"{replay.get('within_0_1_percent')} 个仍在参照的 0.1% 范围内或更好。")
        elif checks:
            parts.append(f"另核对 {checks.get('n')} 个保存决策的可行性和收入。")
    if synthetic_path.exists():
        probe = read_json(synthetic_path)
        count = sum(row.get("within_0_1_percent", 0) for row in probe.get("groups", []))
        parts.append(f"固定新生成器的 {probe.get('n')} 个诊断实例中，{count} 个与精确 oracle 的差距不超过 0.1%。")
    if parts:
        parts.append("这轮 nested-logit 核查没有找到所期望的稳定失败区域；它是已有策略的复核，不能记作 AIPS 胜利。")
    else:
        parts.append("nested-logit 核查产物缺失，本报告不推断该方向已经发现困难实例。")
    return " ".join(parts)


def build_report(run: Path, *, draws=5000):
    run = Path(run).resolve()
    data, metadata, problems = load_scores(run)
    groups = group_scores(data)
    specs = grid()
    complete = all(len(data.get(method, {})) == 12 for method in PRINCIPAL)
    complete = complete and all(len(groups[arm]) == 12 for arm in ARMS)
    incompatible_paths = [spec["name"] for spec in specs
                          if all(spec["name"] in groups[arm] for arm in ARMS)
                          and len({len(groups[arm][spec["name"]]["paths"]) for arm in ARMS}) != 1]
    complete = complete and not incompatible_paths
    missing_main = [method for method in PRINCIPAL if len(data.get(method, {})) != 12]
    if not missing_main and not complete:
        problems.append("主方法逐路径数组长度不一致，无法合并三个独立生成重复")
    for name in incompatible_paths:
        problems.append(f"{name}: 主方法之间路径数不同，主比较不能标记为完成")
    output = run / "tables"
    run_rows, group_rows, comparison_rows, robust_rows, ablation_rows, dp_rows, dp_paired_rows = [], [], [], [], [], [], []
    dp_test_settings = None
    if any((run / "dp" / spec["name"] / "test.json").exists() for spec in specs):
        try:
            protocol = read_json(run / "protocol.json")
            if not isinstance(protocol, dict):
                raise ValueError("protocol.json必须是JSON对象")
            dp_test_settings = protocol.get("test")
        except (OSError, ValueError, TypeError) as error:
            problems.append(f"DP配对缺少有效冻结测试设置：{error}")
    for spec in specs:
        name = spec["name"]
        for method, rows in data.items():
            if name not in rows:
                continue
            row = rows[name]
            metrics = row.get("metrics", [])
            metrics = metrics if isinstance(metrics, (list, tuple)) else []
            run_rows.append(dict(**spec, method=method, cost=row["cost"], paths=len(row["paths"]),
                                 parameter_count=len(row.get("theta", [])),
                                 waste=metrics[0] if len(metrics) > 0 else None,
                                 lost=metrics[1] if len(metrics) > 1 else None,
                                 order=metrics[2] if len(metrics) > 2 else None))
        for group, rows in groups.items():
            if name in rows:
                row = rows[name]
                group_rows.append(dict(**spec, method=group, cost=row["cost"],
                                       generation_sd=row["generation_sd"], generations=row["generations"],
                                       best_generation_cost=row["best"], worst_generation_cost=row["worst"],
                                       paths=len(row["paths"])))
        evo = groups["evolution"].get(name)
        if evo is not None:
            for reference in ("baek", "one_query", "best_of_n") + BASELINES:
                ref = groups[reference].get(name)
                if ref is None:
                    continue
                paired = paired_comparison(evo, ref, key=name + reference, draws=draws)
                if paired is None:
                    problems.append(f"{name}/evolution vs {reference}: 路径数不匹配或少于 2")
                    continue
                comparison_rows.append(dict(**spec, candidate="evolution", reference=reference, **paired))
                if reference == "baek":
                    repeat_separated = evo["worst"] < ref["best"]
                    gain_enough = paired["improvement_pct"] is not None and paired["improvement_pct"] >= 1.0
                    robust_rows.append(dict(**spec, mean_improvement_pct=paired["improvement_pct"],
                                            evolution_worst_cost=evo["worst"], baek_best_cost=ref["best"],
                                            all_repeat_costs_separated=repeat_separated,
                                            robust_screen_candidate=bool(repeat_separated and gain_enough),
                                            paired_ci_low=paired["improvement_ci_low"],
                                            paired_ci_high=paired["improvement_ci_high"]))
        for method, rows in data.items():
            if not method.endswith("_without_tuning") or name not in rows:
                continue
            tuned_method = method.removesuffix("_without_tuning")
            tuned = data.get(tuned_method, {}).get(name)
            if tuned is None:
                problems.append(f"{method}/{name}: 缺少对应 tuned 方法")
                continue
            paired = paired_comparison(tuned, rows[name], key=name + method, draws=draws)
            if paired:
                ablation_rows.append(dict(**spec, method=tuned_method, **paired))
        dp_path = run / "dp" / name / "result.json"
        if dp_path.exists():
            raw = read_json(dp_path)
            certificate = raw.get("certificate", {})
            lo, hi = certificate.get("gain_lower"), certificate.get("gain_upper")
            for group in ARMS:
                row = groups[group].get(name)
                if row and lo is not None and hi is not None and hi > 0:
                    dp_rows.append(dict(**spec, method=group, simulated_cost=row["cost"],
                                        dp_gain_lower=lo, dp_gain_upper=hi,
                                        bellman_span=certificate.get("bellman_span"),
                                        empirical_gap_pct=100 * (row["cost"] - (lo + hi) / 2) / ((lo + hi) / 2)))
        dp_test_path = run / "dp" / name / "test.json"
        if dp_test_path.exists():
            try:
                dp_test = load_dp_test(dp_test_path, name, dp_test_settings)
                for group in ARMS:
                    row = groups[group].get(name)
                    if row is None:
                        continue
                    paired = paired_comparison(row, dp_test, key=name + group + "exact_dp_test", draws=draws)
                    if paired is None:
                        problems.append(f"{name}/{group} vs exact_dp: 路径数不匹配或少于2")
                        continue
                    dp_paired_rows.append(dict(**spec, candidate=group, reference="exact_dp", **paired,
                        excess_cost_pct=None if paired["improvement_pct"] is None else -paired["improvement_pct"],
                        excess_cost_ci_low=None if paired["improvement_ci_high"] is None else -paired["improvement_ci_high"],
                        excess_cost_ci_high=None if paired["improvement_ci_low"] is None else -paired["improvement_ci_low"],
                        candidate_generations=row["generations"], reference_policies=1,
                        seed=dp_test["seed"], burnin=dp_test["burnin"], horizon=dp_test["horizon"],
                        inference="Demand-path CI conditional on three fixed candidate policies and one fixed DP policy; not a long-run optimality certificate"))
            except (OSError, ValueError, KeyError, TypeError) as error:
                problems.append(f"{name}/exact_dp: 无效DP测试记录 ({error})")
    scenario_columns = ["name", "m", "L", "cv", "f", "split"]
    write_csv(output / "per_run.csv", run_rows, scenario_columns + ["method", "cost", "paths", "parameter_count", "waste", "lost", "order"])
    write_csv(output / "group_summary.csv", group_rows, scenario_columns + ["method", "cost", "generation_sd", "generations", "best_generation_cost", "worst_generation_cost", "paths"])
    pair_columns = ["candidate_cost", "reference_cost", "improvement_pct", "improvement_ci_low", "improvement_ci_high",
                    "absolute_improvement", "absolute_ci_low", "absolute_ci_high", "paths", "bootstrap_draws", "path_ci_excludes_zero"]
    write_csv(output / "paired_comparisons.csv", comparison_rows, scenario_columns + ["candidate", "reference"] + pair_columns)
    write_csv(output / "robust_candidates.csv", robust_rows, scenario_columns + ["mean_improvement_pct", "evolution_worst_cost", "baek_best_cost", "all_repeat_costs_separated", "robust_screen_candidate", "paired_ci_low", "paired_ci_high"])
    write_csv(output / "optimizer_ablation.csv", ablation_rows, scenario_columns + ["method"] + pair_columns)
    write_csv(output / "dp_comparison.csv", dp_rows, scenario_columns + ["method", "simulated_cost", "dp_gain_lower", "dp_gain_upper", "bellman_span", "empirical_gap_pct"])
    write_csv(output / "dp_paired_comparisons.csv", dp_paired_rows,
              scenario_columns + ["candidate", "reference"] + pair_columns +
              ["excess_cost_pct", "excess_cost_ci_low", "excess_cost_ci_high", "candidate_generations", "reference_policies",
               "seed", "burnin", "horizon", "inference"])
    budget = ledger_usage(run)
    write_csv(output / "budget.csv", budget["components"], ["component", "limit_usd", "available", "known_cost_usd", "held_upper_usd", "committed_upper_usd", "requests", "uncertain_requests"])
    robust = [row for row in robust_rows if row["robust_screen_candidate"]]
    summary = dict(generated_utc=datetime.now(timezone.utc).isoformat(), complete_primary_comparison=complete,
                   missing_main_methods=missing_main, problems=problems, n_scenarios=12,
                   robust_candidates=robust if complete else [], provisional_robust_candidates=robust if not complete else [],
                   baseline_coverage={key: len(data.get(key, {})) for key in BASELINES},
                   optimizer_ablation_rows=len(ablation_rows), dp_paired_comparison_rows=len(dp_paired_rows), budget=budget,
                   inference="Path CIs condition on all three generated policies; generation SD is separate. No test-selected best method.")
    write_json(run / "report_summary.json", summary)

    lines = ["# 易腐库存实例筛查：" + ("完整主比较" if complete else "尚未完成"), ""]
    if complete:
        if robust:
            lines.append(f"完整 12 个实例中，{len(robust)} 个满足预设的稳健筛查条件：反馈演化三个重复中最差的平均成本，仍低于 Baek-style 三个重复中最好的平均成本，且三重复均值改善至少 1%。")
            lines.append("这些候选为：" + "、".join(f"`{row['name']}`" for row in robust) + "。")
        else:
            lines.append("完整 12 个实例均已比较，本轮没有实例满足预设的稳健筛查条件。不能把较有利的单次生成或个别需求路径当作成功实例。")
    else:
        lines.append("主比较尚未完成，不据现有部分结果宣布发现或未发现成功实例。需要全部 9 个结构搜索重复、3 个 Baek-style 重复，每个均覆盖全部 12 场景并有可配对的逐路径费用。")
        lines.append("缺少完整主方法：" + ("、".join(f"`{method}`" for method in missing_main) if missing_main else "逐路径数组尚不一致") + "。")
    lines += ["", "## 全部实例", "",
              "每个单元格是三个独立生成重复的平均每期成本 ± 生成间样本标准差；费用越低越好。所有重复都计入，未按测试表现挑选最佳重复。对三个数值结构搜索组，m=3、5 用于结构发现，m=4 仅用于未提供搜索反馈的迁移检查；这不限制 Baek L2 的设计阶段计算。", "",
              "| 场景 | 单次查询 | 独立生成择优 | 反馈演化 | Baek L2 | 演化相对 Baek 改善 % [95% 路径区间] | 稳健筛查 |",
              "|---|---:|---:|---:|---:|---:|---|"]
    paired_lookup = {(row["name"], row["reference"]): row for row in comparison_rows}
    robust_lookup = {row["name"]: row for row in robust_rows}
    for spec in specs:
        name = spec["name"]
        cells = []
        for arm in ARMS:
            row = groups[arm].get(name)
            cells.append("缺" if row is None else f"{row['cost']:.3f} ± {row['generation_sd']:.3f}")
        comparison = paired_lookup.get((name, "baek"))
        effect = "缺" if comparison is None else f"{fmt(comparison['improvement_pct'],2)} [{fmt(comparison['improvement_ci_low'],2)}, {fmt(comparison['improvement_ci_high'],2)}]"
        signal = robust_lookup.get(name)
        flag = "缺" if signal is None else ("候选" if signal["robust_screen_candidate"] else "未达条件")
        lines.append(f"| m={spec['m']}, CV={spec['cv']:g}, f={spec['f']:g} | " + " | ".join(cells + [effect, flag]) + " |")
    lines += ["", "正改善率定义为 `100×(参照成本−演化成本)/参照成本`。区间通过相同需求路径索引的配对 bootstrap 得到，每条路径先平均三个生成重复；因此它只反映给定这三份策略后的需求抽样误差，**不是生成不确定性的置信区间**。生成间标准差单列。配对依赖冻结协议中的共用测试路径，输入文件未包含路径哈希时无法仅凭费用数组重新证明路径身份。",
              "", "稳健筛查条件是可复查的经验门槛，并非统计显著性的定义。这里检查了多个实例和多个参照，区间没有做多重比较调整；后续仍需新的独立实例、需求种子和生成重复确认。", "", "## 结构搜索与 optimizer", "",
              "同一数值搜索器及每候选 objective-call 上限用于三个结构搜索组；独立生成择优与反馈演化都产生 8 个候选，单次查询产生 4 个，故单次查询并不具有相同总数值预算。反馈演化的输入提示更长，token 与实际美元开销也并不严格相同。Baek-style L2 可以使用通用 Python/SciPy 工具及设计阶段计算，是单独记录资源的强对照。",
              "", "所有方法预先知道完整有限参数族。Baek L2 可在工具会话中自行模拟全部 12 个组合、重新采样、针对每个实例拟合或在设计程序中写入系数；这符合 design(params) 接口，不能仅因针对实例适配便判为无效。因此 m=4 只是三个数值结构搜索组未获得反馈的迁移场景，并非所有方法共同的未知参数 holdout。公开模型和训练 helper 相同，不代表实际训练查询、额外工具计算或实例适配相同；应结合各方法实际资源记录解释比较。"]
    for reference in ("one_query", "best_of_n", "baek"):
        values = [row["improvement_pct"] for row in comparison_rows if row["reference"] == reference and row["improvement_pct"] is not None]
        if values:
            lines.append(f"相对{LABELS[reference]}：现有 {len(values)}/12 场景的等权平均改善 {np.mean(values):.2f}%，中位数 {np.median(values):.2f}%；此汇总包含不利结果。")
    lines.append("")
    if ablation_rows:
        lines.append(f"optimizer 消融已取得 {len(ablation_rows)} 个方法×场景配对，见 {link(output/'optimizer_ablation.csv', 'optimizer_ablation.csv')}。正值表示同一已冻结结构调参后优于未调参；它衡量该结构上的调参收益，不能单独证明演化发现新结构。")
    else:
        lines.append("缺少 `*_without_tuning.json` 配对结果，尚不能分离 optimizer 收益与结构搜索收益。")
    lines += ["", "## 经典策略与精确 DP", "",
              "全部五种经典策略逐一报告，不按测试成本选一个最弱参照。BSP-low-EW 使用文献公式，估计报废按本模型混合 FIFO/LIFO 的均值需求递推适配；未把它称为 PIL/APIL。", "",
              "| 场景 | 常量 | Base-stock | Capped BS | 年龄折扣 | BSP-low-EW |", "|---|---:|---:|---:|---:|---:|"]
    for spec in specs:
        values = [fmt(groups[method].get(spec["name"], {}).get("cost")) for method in BASELINES]
        lines.append(f"| m={spec['m']}, CV={spec['cv']:g}, f={spec['f']:g} | " + " | ".join(values) + " |")
    if dp_rows:
        lines += ["", f"m=3 的有限状态 DP 比较见 {link(output/'dp_comparison.csv', 'dp_comparison.csv')}。DP 表示共同库存容量约束下的最优长期平均成本及 Bellman 残差证书；策略的测试均值存在模拟误差，偶然低于证书值不能解释为突破最优值。它是 OR 基线，不能算作 AIPS 的效果。"]
    else:
        lines += ["", "精确 DP 证书或对应策略测试结果尚不齐全，此处不报告最优性差距。"]
    if dp_paired_rows:
        lines += ["", f"同一最终需求路径上的DP策略配对比较已有 {len(dp_paired_rows)}/16 个主方法×m=3场景记录，见 {link(output/'dp_paired_comparisons.csv', 'dp_paired_comparisons.csv')}。各主方法先按路径平均三次生成，再与一份冻结DP策略比较；区间仅衡量这些固定策略的需求路径误差。",
                  "", "配对表的improvement为100×(DP−方法)/DP，excess_cost为相反数，正excess表示方法成本更高。有限样本成本低于DP测试均值或理论证书均不能解释为低于长期最优成本；这张表不能替代Bellman证书。路径配对依赖一致的冻结场景、种子、路径数和计分设置，未由需求数组哈希重新验证。"]
    lines += ["", "## 费用", "", "| 分项 | 分配上限 $ | 已知实付 $ | 未决请求保守预留 $ | 已知+预留 $ |", "|---|---:|---:|---:|---:|"]
    for row in budget["components"]:
        lines.append(f"| {row['component']} | {row['limit_usd']:.2f} | {fmt(row['known_cost_usd'],4)} | {fmt(row['held_upper_usd'],4)} | {fmt(row['committed_upper_usd'],4)} |")
    lines.append(f"\n两本账中已记录实付合计 ${budget['recorded_known_usd']:.4f}，未决费用上界 ${budget['recorded_held_usd']:.4f}，合计占用 ${budget['recorded_committed_usd']:.4f}。总授权上限 $50，另有 $3 未分配；未决费用不能当作免费。")
    if not budget["both_ledgers_available"]:
        lines.append("至少一本账缺失，上述只是可见记录合计，不能据此确认全部实际开销。")
    elif not budget["within_50_if_ledgers_complete"]:
        lines.append("**账本占用已超过 $50，需要核对费用；本报告不会掩盖该异常。**")
    lines += ["", "## 模型口径与另一条路线", "",
              "本次主模型采用实际 CV=1.5/2 和 m+L 期需求的 newsvendor 容量分位数。公开 DynaPlex 代码使用的 `cvr` 实际是 √(方差/均值)，且容量累计 m+L+1 期需求。因此这是明确标注的论文文字口径实验，不能直接称为原论文数值复现。完整来源、需求分布、事件顺序和验证见 " + link(REPO / "docs/overnight_perishable_spec.md", "实例定义") + "。",
              "", nested_note(), "",
              "当前结果仍属于有限预算下的探索筛查。没有强制寻找胜例，也不把新增计算或人工整理本身算作搜索算法的优势。尚未实现的 PIL/APIL 或 DCL 基线不得被描述为已经击败。", "", "## 可复查文件", "",
              "- " + link(output / "per_run.csv", "全部独立生成和每场景费用"),
              "- " + link(output / "group_summary.csv", "组均值与生成标准差"),
              "- " + link(output / "paired_comparisons.csv", "全部配对改善与区间"),
              "- " + link(output / "robust_candidates.csv", "固定筛查门槛核对"),
              "- " + link(output / "optimizer_ablation.csv", "optimizer 消融"),
              "- " + link(output / "dp_paired_comparisons.csv", "主方法与冻结DP策略的同路径配对比较"),
              "- " + link(run / "report_summary.json", "机器可读完整性和预算记录")]
    if problems:
        lines += ["", "## 未完成或无效记录", ""] + ["- " + problem for problem in problems]
    (run / "report.md").write_text("\n".join(lines) + "\n")
    return summary


def self_test():
    """Uses invented score fixtures only; never opens the real test directory."""
    from unittest.mock import patch
    with tempfile.TemporaryDirectory(prefix="overnight_report_test_") as temporary, patch(
            __name__ + ".nested_note", return_value="Synthetic fixture; no external diagnostic files read."):
        run = Path(temporary)
        incomplete = build_report(run, draws=100)
        assert not incomplete["complete_primary_comparison"]
        assert len(incomplete["missing_main_methods"]) == 12
        for method in PRINCIPAL + BASELINES:
            rows = {}
            repeat = int(method[-1]) if method[-1] in "123" else 1
            base = 100 if method.startswith("evolution") else 110
            for spec in grid():
                paths = np.arange(8, dtype=float) + base + repeat
                rows[spec["name"]] = dict(cost=float(paths.mean()), path_costs=paths.tolist(), metrics=[1, 2, 3], theta=[])
            write_json(run / "test" / (method + ".json"), dict(results=rows))
        write_json(run / "test/evolution_r1_without_tuning.json",
                   read_json(run / "test/baek_r1.json"))
        write_json(run / "framework_budget/api_budget.json", dict(limit_usd=35, requests={
            "a": dict(state="complete", actual_cost_usd=1.25, reserved_usd=2),
            "b": dict(state="unknown_charge", reserved_usd=.3)}))
        write_json(run / "baek/budget.json", dict(limit_usd=12, requests={
            "a": dict(state="known", actual_cost_usd=.75, upper_usd=1),
            "b": dict(state="pending", upper_usd=.4)}))
        summary = build_report(run, draws=100)
        assert summary["complete_primary_comparison"]
        assert len(summary["robust_candidates"]) == 12
        assert summary["optimizer_ablation_rows"] == 12
        assert abs(summary["budget"]["recorded_known_usd"] - 2) < 1e-12
        assert abs(summary["budget"]["recorded_held_usd"] - .7) < 1e-12
        dp_settings = dict(seed=951951, paths=8, burnin=2, horizon=20)
        write_json(run / "protocol.json", dict(test=dp_settings))
        for spec in grid():
            if spec["m"] != 3:
                continue
            costs = np.arange(8, dtype=float) + 95
            write_json(run / "dp" / spec["name"] / "test.json",
                       dict(scenario=spec["name"], test=dict(**dp_settings, mean=float(costs.mean()), path_costs=costs.tolist())))
            write_json(run / "dp" / spec["name"] / "result.json",
                       dict(certificate=dict(gain_lower=98.49, gain_upper=98.51, bellman_span=.02)))
        paired_dp = build_report(run, draws=100)
        assert paired_dp["dp_paired_comparison_rows"] == 16
        with (run / "tables/dp_paired_comparisons.csv").open(encoding="utf-8-sig") as handle:
            dp_records = list(csv.DictReader(handle))
        assert len(dp_records) == 16 and {row["candidate"] for row in dp_records} == set(ARMS)
        assert all(row["reference"] == "exact_dp" and row["paths"] == "8" for row in dp_records)
        for row in dp_records:
            delta = -7 if row["candidate"] == "evolution" else -17
            assert float(row["absolute_improvement"]) == delta
            assert float(row["absolute_ci_low"]) == float(row["absolute_ci_high"]) == delta
            assert np.isclose(float(row["excess_cost_pct"]), -float(row["improvement_pct"]))
            assert np.isclose(float(row["excess_cost_ci_low"]), -float(row["improvement_ci_high"]))
        with (run / "tables/dp_comparison.csv").open(encoding="utf-8-sig") as handle:
            assert len(list(csv.DictReader(handle))) == 16  # Existing certificate table is retained.
        first_dp = run / "dp" / grid()[0]["name"] / "test.json"
        correct_dp = read_json(first_dp)
        wrong_seed = read_json(first_dp)
        wrong_seed["test"]["seed"] += 1
        write_json(first_dp, wrong_seed)
        assert build_report(run, draws=100)["dp_paired_comparison_rows"] == 12
        wrong_mean = read_json(first_dp)
        wrong_mean["test"]["seed"] = dp_settings["seed"]
        wrong_mean["test"]["mean"] += 1
        write_json(first_dp, wrong_mean)
        assert build_report(run, draws=100)["dp_paired_comparison_rows"] == 12
        high_dp = dict(scenario=grid()[0]["name"], test=dict(**dp_settings,
                      mean=123.5, path_costs=(np.arange(8, dtype=float) + 120).tolist()))
        write_json(first_dp, high_dp)
        assert build_report(run, draws=100)["dp_paired_comparison_rows"] == 16
        assert "不能解释为低于长期最优成本" in (run / "report.md").read_text()
        write_json(first_dp, correct_dp)
        bad = read_json(run / "test/baek_r3.json")
        bad["results"][grid()[0]["name"]]["cost"] = -1
        write_json(run / "test/baek_r3.json", bad)
        broken = build_report(run, draws=100)
        assert not broken["complete_primary_comparison"]
        assert not broken["robust_candidates"]
    return dict(empty_input="incomplete", complete_fixture="passed", invalid_fixture="rejected",
                optimizer_ablation="passed", known_and_held_budget="passed", dp_paired_all_four_arms="passed",
                dp_paired_sign_and_ci="passed", dp_wrong_seed_and_mean="rejected",
                dp_certificate_table="preserved", below_dp_sample_mean="not_claimed_below_optimum",
                real_test_data_read=False)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", type=Path, default=DEFAULT_RUN)
    parser.add_argument("--bootstrap-draws", type=int, default=5000)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.bootstrap_draws < 100:
        parser.error("At least 100 bootstrap draws are required")
    result = self_test() if args.self_test else build_report(args.run_dir, draws=args.bootstrap_draws)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
