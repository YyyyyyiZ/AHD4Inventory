"""Offline report for Flash: three repeats, ten generations, ten proposals.

Only saved JSON artifacts are read. No simulator, runner, policy, or API client
is imported. The self-test builds temporary synthetic artifacts, including a
synthetic historical summary; it never reads real test results.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import math
from pathlib import Path
import re
import statistics
import tempfile
import json

from .model_comparison_reporting import (
    _api_accounting, _cell, _diagnostic_fmt, _dump, _escape, _fmt,
    _load_results, _model_api_diagnostics, _number, _read,
    _selection_diagnostics, _three,
)


REPEATS = (1, 2, 3)
GENERATIONS = 10
PROPOSALS = 10
METRIC = "mean_training_cost_ratio_to_common_baseline"
DEFAULT_HISTORY = Path(__file__).resolve().parents[3] / "output/overnight_search/20260917/night_summary.json"


def _catalog(model_file, scenario_file, protocol, issues):
    model = None
    try:
        entries = model_file["models"]
        if not isinstance(entries, list) or len(entries) != 1:
            raise ValueError("本报告要求恰好一个Flash模型，不要求新Sol对照")
        model = {key: entries[0][key] for key in ("slug", "label", "model", "role")}
        if not all(isinstance(value, str) and value for value in model.values()):
            raise ValueError("模型元数据必须为非空字符串")
        if not re.fullmatch(r"[A-Za-z0-9_-]+", model["slug"]):
            raise ValueError("非法模型slug")
    except (KeyError, TypeError, ValueError) as error:
        issues.append({"input": "models.json", "error": str(error)})
        model = None
    scenarios, seen = [], set()
    for row in scenario_file or []:
        try:
            if not isinstance(row, dict) or not isinstance(row["name"], str) or not row["name"] or row["name"] in seen:
                raise ValueError("场景条目/名称无效或重复")
            for key in ("m", "L", "cv", "f"):
                _number(row[key])
            seen.add(row["name"])
            scenarios.append(row)
        except (KeyError, TypeError, ValueError) as error:
            issues.append({"input": "scenarios.json", "error": str(error)})
    expected = {(m, 2, cv, f) for m in (3, 4, 5, 7, 8) for cv in (1.5, 2.) for f in (0., .5)}
    if len(scenarios) != 20 or {(s["m"], s["L"], s["cv"], s["f"]) for s in scenarios} != expected:
        issues.append({"input": "scenarios.json", "error": "未完整覆盖指定20场景网格"})
    for key, required in (("generations", 10), ("proposals_per_generation", 10),
                          ("generated_candidates_per_repetition", 100)):
        if not protocol or type(protocol.get(key)) is not int or protocol[key] != required:
            issues.append({"input": "protocol.json", "error": f"{key}必须为{required}"})
    return model, scenarios


def _best_point(value, *, allow_none=False):
    if value is None and allow_none:
        return None
    if not isinstance(value, dict) or not isinstance(value.get("origin"), str):
        raise ValueError("训练最佳点的来源无效")
    origin, kind = value["origin"], value.get("source_kind")
    if kind not in ("common_seed", "generated") or (kind == "common_seed") != origin.startswith("common:"):
        raise ValueError("训练最佳点的来源分类不一致")
    score = _number(value["score"])
    if score < 0:
        raise ValueError("训练成本比例不能为负")
    return {"origin": origin, "score": score, "source_kind": kind}


def _trajectories(root, slug, fingerprints):
    issues, repeats = [], []
    for repeat in REPEATS:
        points = []
        for generation in range(GENERATIONS):
            relative = f"runs/{slug}/r{repeat}/generations/{generation:02d}/summary.json"
            row = _read(root, relative, dict, issues, fingerprints)
            point = {"generation_number": generation + 1, "complete": False, "status": "unknown",
                     "valid": None, "invalid": None, "proposals_recorded": None,
                     "best_before": None, "best_after": None, "best_generated_so_far": None}
            if row is not None:
                try:
                    if row.get("generation_index") != generation or row.get("generation_number") != generation + 1:
                        raise ValueError("代编号不匹配")
                    if row.get("metric") != METRIC or row.get("proposals_expected") != PROPOSALS:
                        raise ValueError("训练指标或计划每代候选数不匹配")
                    for key in ("valid", "invalid", "proposals_recorded"):
                        if type(row.get(key)) is not int or not 0 <= row[key] <= PROPOSALS:
                            raise ValueError(f"{key}计数无效")
                    if row["valid"] + row["invalid"] != row["proposals_recorded"]:
                        raise ValueError("有效/无效计数与已记录数不一致")
                    candidates = row.get("candidates")
                    if not isinstance(candidates, list) or len(candidates) != row["proposals_recorded"]:
                        raise ValueError("候选记录与计数不一致")
                    indices = [candidate.get("index") for candidate in candidates if isinstance(candidate, dict)]
                    if len(indices) != len(candidates) or any(type(index) is not int for index in indices):
                        raise ValueError("候选编号无效")
                    allowed = set(range(generation * PROPOSALS, (generation + 1) * PROPOSALS))
                    if len(set(indices)) != len(indices) or not set(indices) <= allowed:
                        raise ValueError("候选编号重复或不属于本代")
                    if (sum(candidate.get("valid") is True for candidate in candidates) != row["valid"] or
                            sum(candidate.get("valid") is False for candidate in candidates) != row["invalid"]):
                        raise ValueError("候选valid状态与汇总不匹配")
                    before, after = _best_point(row["best_before"]), _best_point(row["best_after"])
                    generated = _best_point(row.get("best_generated_so_far"), allow_none=True)
                    if after["score"] > before["score"] + 1e-10:
                        raise ValueError("累计训练最佳值异常变差")
                    if generated is not None and generated["source_kind"] != "generated":
                        raise ValueError("生成候选最佳值却标记为共享策略")
                    full = row.get("status") == "complete" and row["proposals_recorded"] == PROPOSALS
                    point.update(complete=full, status=str(row.get("status", "unknown")),
                        valid=row["valid"], invalid=row["invalid"], proposals_recorded=row["proposals_recorded"],
                        best_before=before, best_after=after, best_generated_so_far=generated,
                        input_sha256=row.get("input_sha256"))
                    if not full:
                        issues.append({"input": relative, "error": "本代尚未完整记录10个候选"})
                except (KeyError, TypeError, ValueError) as error:
                    issues.append({"input": relative, "error": str(error)})
            points.append(point)
        full = all(point["complete"] for point in points)
        repeats.append({"repeat": repeat, "complete": full, "generations": points,
            "valid_count": sum(point["valid"] for point in points) if full else None,
            "invalid_count": sum(point["invalid"] for point in points) if full else None,
            "known_recorded_count": sum(point["proposals_recorded"] or 0 for point in points)})
    return {"complete": not issues, "metric": METRIC, "lower_is_better": True,
            "planned_candidates_per_repeat": 100, "repeats": repeats, "issues": issues}


def _historical(path, scenarios, flash_rows, fingerprints):
    result = {"enabled": path is not None, "complete": False, "source": str(path) if path else None,
              "rows": [], "equal_scenario_mean_cost_gap_pct": {}, "issues": [],
              "paired_statistics": False, "causal_backbone_comparison": False}
    if path is None:
        return result
    path = Path(path).expanduser().resolve()
    local_hashes = {}
    old = _read(path.parent, path.name, dict, result["issues"], local_hashes)
    fingerprints.update({str(path.parent / name): digest for name, digest in local_hashes.items()})
    if old is None:
        return result
    try:
        if old.get("comparison_complete") is not True:
            raise ValueError("历史汇总未标记主比较完整")
        old_rows = old["scenarios"]
        if not isinstance(old_rows, list) or len(old_rows) != 20:
            raise ValueError("历史汇总不是20场景")
        indexed = {row["name"]: row for row in old_rows}
        if len(indexed) != 20 or set(indexed) != {spec["name"] for spec in scenarios}:
            raise ValueError("历史与本轮场景名称集合不同")
        for spec in scenarios:
            old_row = indexed[spec["name"]]
            if any(old_row[key] != spec[key] for key in ("m", "cv", "f")):
                raise ValueError("历史场景参数不同")
            flash = flash_rows[spec["name"]]["cost"]["mean"]
            record = {"name": spec["name"], "flash_cost": flash, "references": {}}
            for arm in ("evolution", "baek"):
                group = old_row["groups"][arm]
                mean = _number(group["cost"])
                draws = [_number(value) for value in group["generation_costs"]]
                sd = _number(group["generation_sd"])
                if (mean <= 0 or len(draws) != 3 or any(value < 0 for value in draws) or
                        not math.isclose(mean, statistics.mean(draws), rel_tol=1e-9, abs_tol=1e-8) or
                        not math.isclose(sd, statistics.stdev(draws), rel_tol=1e-9, abs_tol=1e-8)):
                    raise ValueError("历史三重复成本均值/SD不一致")
                record["references"][arm] = {"cost": mean, "sample_sd": sd,
                    "flash_cost_gap_pct": 100 * (flash / mean - 1) if flash is not None else None}
            result["rows"].append(record)
        result["complete"] = True
        for arm in ("evolution", "baek"):
            values = [row["references"][arm]["flash_cost_gap_pct"] for row in result["rows"]]
            result["equal_scenario_mean_cost_gap_pct"][arm] = statistics.mean(values) if len(values) == 20 and all(value is not None for value in values) else None
    except (KeyError, TypeError, ValueError) as error:
        result["rows"] = []
        result["issues"].append({"input": str(path), "error": str(error)})
    return result


def build_report(run, historical_summary=DEFAULT_HISTORY):
    """Write only report.md/report_summary.json in the specified Flash run."""
    root = Path(run).expanduser().resolve()
    if not root.is_dir():
        raise ValueError(f"运行目录不存在：{root}")
    issues, fingerprints = [], {}
    protocol = _read(root, "protocol.json", dict, issues, fingerprints)
    model_source = _read(root, "models.json", dict, issues, fingerprints)
    scenario_source = _read(root, "scenarios.json", list, issues, fingerprints)
    api_source = _read(root, "api_summary.json", dict, issues, fingerprints)
    model, scenarios = _catalog(model_source, scenario_source, protocol, issues)
    accounting = _api_accounting(api_source, issues)
    names = [spec["name"] for spec in scenarios]
    files = {kind: {repeat: None for repeat in REPEATS} for kind in ("tuned", "raw")}
    if model:
        for repeat in REPEATS:
            for kind, filename in (("tuned", "test.json"), ("raw", "test_raw.json")):
                files[kind][repeat] = _load_results(root, f"runs/{model['slug']}/r{repeat}/{filename}", names, issues, fingerprints)
    rows = {}
    for spec in scenarios:
        cost, raw_cost, reduction, counts = [], [], [], []
        for repeat in REPEATS:
            tuned, raw = (_cell(files[kind][repeat], spec["name"]) for kind in ("tuned", "raw"))
            cost.append(tuned["cost"] if tuned else None)
            raw_cost.append(raw["cost"] if raw else None)
            reduction.append(100 * (1 - tuned["cost"] / raw["cost"]) if tuned and raw and raw["cost"] > 0 else None)
            counts.append({"tuned": tuned["path_count"] if tuned else None, "raw": raw["path_count"] if raw else None})
            if raw and raw["cost"] <= 0:
                issues.append({"input": f"r{repeat}/test_raw.json", "scenario": spec["name"], "error": "raw成本不为正，无法计算百分比降本"})
        rows[spec["name"]] = {"scenario": spec, "split": "transfer" if spec["m"] in (4, 8) else "discovery",
            "cost": _three(cost), "raw_cost": _three(raw_cost), "optimizer_reduction_pct": _three(reduction), "path_counts": counts}
    test_complete = not issues
    grid_valid = not any(issue["input"] == "scenarios.json" for issue in issues)
    aggregates = {}
    for group, selected in (("all_20", names), ("transfer_8", [s["name"] for s in scenarios if s["m"] in (4, 8)])):
        aggregates[group] = {"scenario_count": len(selected)}
        for key in ("cost", "raw_cost", "optimizer_reduction_pct"):
            values = []
            for index in range(3):
                observations = [rows[name][key]["repeat_values"][index] for name in selected]
                values.append(statistics.mean(observations) if grid_valid and observations and all(value is not None for value in observations) else None)
            aggregates[group][key] = _three(values)
    optional_warnings, origin_issues = [], []
    api = _model_api_diagnostics(root, [model] if model else [], optional_warnings, fingerprints)
    origins = [_selection_diagnostics(root, model["slug"], repeat, origin_issues, fingerprints) for repeat in REPEATS] if model else []
    trajectory = _trajectories(root, model["slug"], fingerprints) if model else {"complete": False, "repeats": [], "issues": []}
    source_counts = {kind: sum(row["category"] == kind for row in origins) for kind in ("common_seed", "generated", "unknown")}
    source_counts["unknown"] += 3 - len(origins)
    historical = _historical(historical_summary, scenarios, rows, fingerprints)
    complete = test_complete and trajectory["complete"] and not origin_issues and model is not None
    summary = {"schema_version": 1, "generated_utc": datetime.now(timezone.utc).isoformat(),
        "complete": complete, "test_results_complete": test_complete, "generation_schedule_complete": trajectory["complete"],
        "run_directory": str(root), "model": model, "planned_repeats": 3, "planned_scenarios": 20,
        "planned_generations": 10, "planned_proposals_per_generation": 10, "planned_proposals_total": 300,
        "scenario_results": list(rows.values()), "aggregates": aggregates,
        "selected_origins": origins, "selected_origin_counts": source_counts,
        "training_trajectories": trajectory, "api_accounting": accounting, "model_api_accounting": api,
        "historical_reference": historical, "issues": issues, "origin_issues": origin_issues,
        "optional_warnings": optional_warnings, "input_sha256": fingerprints,
        "inference": "Descriptive three-repeat Flash experiment. No causal backbone comparison, paired historical inference, noninferiority, or novel-structure claim.",
        "optimizer_ablation_scope": "Literal defaults versus fitted parameters of the same already-selected structure; conditional only",
        "winner_conclusion": None}
    _dump(root / "report_summary.json", summary)
    (root / "report.md").write_text(render_markdown(summary), encoding="utf-8")
    return summary


def render_markdown(summary):
    model = summary["model"]
    status = "完整" if summary["complete"] else "INCOMPLETE：不按剩余成功结果补齐结论"
    lines = ["# Flash 易腐库存实验", "", f"状态：**{status}**。", "",
        f"模型：{_escape(model['label']) if model else '未知'}；API model ID：`{_escape(model['model']) if model else '未知'}`。计划3次独立重复，每次10代、每代10个提案，共300个提案；最终在20场景测试。没有新增同流程Sol对照。", "",
        "下表均值与样本SD来自3次完整重复；缺少一次就不取成功者平均。模拟路径不被当作独立生成重复。成本越低越好；不从测试集挑选最佳重复。", "",
        "## 最终20场景成本", "",
        "| 场景 | 分组 | r1 / r2 / r3成本 | 均值 ± SD | raw均值 ± SD | 调参降本均值 (%) |", "|---|---|---|---|---|---|"]
    for row in summary["scenario_results"]:
        costs = " / ".join(_fmt(value) for value in row["cost"]["repeat_values"])
        lines.append(f"| {_escape(row['scenario']['name'])} | {row['split']} | {costs} | {_fmt(row['cost']['mean'])} ± {_fmt(row['cost']['sample_sd'])} | {_fmt(row['raw_cost']['mean'])} ± {_fmt(row['raw_cost']['sample_sd'])} | {_fmt(row['optimizer_reduction_pct']['mean'])} |")
    lines += ["", "## 固定已选结构的optimizer条件消融", "",
        "raw使用同一已选策略的字面默认参数，tuned使用最终拟合参数。每次重复先对场景等权平均 `100 × (raw − tuned) / raw`，再汇总3次；正数表示降本。结构的生成与选择已经用到optimizer，因此这不是重新运行完全无optimizer搜索，也不能识别optimizer对整个工作流的独立因果贡献。", "",
        "| 场景组 | 等权平均成本 ± SD | r1 / r2 / r3调参降本 (%) | 降本均值 ± SD (%) |", "|---|---|---|---|"]
    for group, record in summary["aggregates"].items():
        reduction = record["optimizer_reduction_pct"]
        values = " / ".join(_fmt(value) for value in reduction["repeat_values"])
        lines.append(f"| {group} | {_fmt(record['cost']['mean'])} ± {_fmt(record['cost']['sample_sd'])} | {values} | {_fmt(reduction['mean'])} ± {_fmt(reduction['sample_sd'])} |")
    lines += ["", "## 所选策略来源", "",
        "共享初始策略也是可被选中的候选。若最终回退到common:来源，得到的是共享策略加数值调参的表现，不能据此称Flash演化出同样好的新结构。生成来源本身也不证明结构新颖，更不意味着100个提案都好。", "",
        "| 重复 | freeze所选来源 | 分类 |", "|---|---|---|"]
    for row in summary["selected_origins"]:
        label = {"common_seed": "共享初始策略", "generated": "Flash生成候选", "unknown": "未知"}[row["category"]]
        lines.append(f"| r{row['repeat']} | {_escape(row['origin']) if row['origin'] else '未知'} | {label} |")
    counts = summary["selected_origin_counts"]
    lines += ["", f"已确认来源：共享初始策略{counts['common_seed']}次，生成候选{counts['generated']}次，未知{counts['unknown']}次。", "",
        "## 逐代训练轨迹", "",
        "训练指标是各发现类场景成本相对共同基准成本的平均比例，越低越好；它不是最终测试成本。有效只表示候选通过程序与数值评估，不表示优于基准。累计训练最佳值包含共享初始策略；另列生成候选的最佳值。训练改进受搜索选择影响，不能替代独立测试验证。", "",
        "| 重复 | 代 | 状态 | 有效 / 无效 | 代前最佳 | 代后最佳 | 累计生成候选最佳 | 代后最佳来源 |", "|---|---|---|---|---|---|---|---|"]
    for repeat in summary["training_trajectories"]["repeats"]:
        for point in repeat["generations"]:
            values = [_diagnostic_fmt(point[key]["score"] if point[key] else None, 6) for key in ("best_before", "best_after", "best_generated_so_far")]
            origin = point["best_after"]["origin"] if point["best_after"] else "未知"
            lines.append(f"| r{repeat['repeat']} | {point['generation_number']} | {_escape(point['status'])} | {_diagnostic_fmt(point['valid'])} / {_diagnostic_fmt(point['invalid'])} | {' | '.join(values)} | {_escape(origin)} |")
    lines += ["", "## API费用", ""]
    fees = summary["api_accounting"]
    if fees:
        lines.append(f"共享总账：已确认 ${_diagnostic_fmt(fees.get('actual_cost_usd'), 7)}；估计费用上限 ${_diagnostic_fmt(fees.get('estimated_upper_usd'), 7)}；仍预留上限 ${_diagnostic_fmt(fees.get('held_upper_usd'), 7)}；合计保守上限 ${_diagnostic_fmt(fees.get('committed_upper_usd'), 7)}；预算 ${_diagnostic_fmt(fees.get('limit_usd'), 2)}。请求数 {_diagnostic_fmt(fees.get('requests'))}。")
    else:
        lines.append("费用摘要未知。")
    attributed = summary["model_api_accounting"]["models"].get(model["slug"]) if model else None
    if attributed:
        lines.append(f"按请求metadata.slug归属本模型：已确认 ${_diagnostic_fmt(attributed['actual_cost_usd'], 7)}；估计上限 ${_diagnostic_fmt(attributed['estimated_upper_usd'], 7)}；仍预留 ${_diagnostic_fmt(attributed['held_upper_usd'], 7)}；请求数 {_diagnostic_fmt(attributed['requests'])}。")
    lines += ["", "估计费用和预留上限不是已确认实扣；API费用不包含本地CPU。费用来源缺失时显示未知，不假定为零。", "",
        "## 历史参考（不同工作流）", "",
        "旧Sol evolution与Baek-style L2仅为历史参考。生成次数、搜索/调参流程及测试随机样本不同；这里比较冻结的三重复平均成本，不配对新旧重复、不重建路径置信区间、不做非劣检验，也不把差异归因于backbone。正的成本差表示本轮Flash成本更高。"]
    history = summary["historical_reference"]
    if history["complete"]:
        lines += ["", "| 场景 | Flash平均成本 | 历史Sol evolution成本 | 成本差 (%) | 历史Baek-style L2成本 | 成本差 (%) |", "|---|---|---|---|---|---|"]
        for row in history["rows"]:
            evo, baek = (row["references"][key] for key in ("evolution", "baek"))
            lines.append(f"| {_escape(row['name'])} | {_fmt(row['flash_cost'])} | {_fmt(evo['cost'])} | {_fmt(evo['flash_cost_gap_pct'])} | {_fmt(baek['cost'])} | {_fmt(baek['flash_cost_gap_pct'])} |")
        gaps = history["equal_scenario_mean_cost_gap_pct"]
        lines += ["", f"20场景等权平均成本差：相对历史Sol evolution {_fmt(gaps['evolution'])}%；相对历史Baek-style L2 {_fmt(gaps['baek'])}%。仅作描述。"]
    else:
        lines += ["", "历史参考未提供或未通过汇总校验；未用缺失参考构造比较。"]
    problems = summary["issues"] + summary["origin_issues"] + summary["training_trajectories"]["issues"]
    if problems:
        lines += ["", "## 未完成或无效输入", ""]
        for issue in problems:
            lines.append(f"- `{_escape(issue['input'])}`：{_escape(issue['error'])}")
    lines += ["", "本报告仅读取已保存结果；原始结果、策略和参数保持不变。详细统计、历史/账本可选诊断及输入SHA-256见report_summary.json。", ""]
    return "\n".join(lines)


def self_test():
    with tempfile.TemporaryDirectory(prefix="flash-report-fixture-") as temporary:
        root = Path(temporary)
        specs = [{"name": f"perish_m{m}_L2_cv{cv:g}_f{f:g}", "m": m, "L": 2, "cv": cv, "f": f}
                 for m in (3, 4, 5, 7, 8) for cv in (1.5, 2.) for f in (0., .5)]
        _dump(root / "protocol.json", {"generations": 10, "proposals_per_generation": 10, "generated_candidates_per_repetition": 100})
        _dump(root / "models.json", {"models": [{"slug": "flash", "label": "Synthetic Flash", "model": "fixture-flash", "role": "candidate"}]})
        _dump(root / "scenarios.json", specs)
        _dump(root / "api_summary.json", {"limit_usd": 50, "actual_cost_usd": 1, "estimated_upper_usd": .2,
            "held_upper_usd": .3, "committed_upper_usd": 1.5, "remaining_usd": 48.5, "requests": 3, "paused_reason": None})
        for repeat in REPEATS:
            folder = root / "runs/flash" / f"r{repeat}"
            folder.mkdir(parents=True)
            _dump(folder / "freeze.json", {"slug": "flash", "repeat": repeat,
                  "origin": "common:flexible_age_weights" if repeat == 1 else f"flash/r{repeat}/97"})
            for raw, filename in ((False, "test.json"), (True, "test_raw.json")):
                results = {}
                for index, spec in enumerate(specs):
                    cost = (100. + index + repeat) * (1.25 if raw else 1.)
                    results[spec["name"]] = {"cost": cost, "path_costs": [cost - 1, cost + 1], "theta": []}
                _dump(folder / filename, {"valid": True, "results": results})
            for generation in range(10):
                target = folder / "generations" / f"{generation:02d}"
                target.mkdir(parents=True)
                before = {"origin": "common:seed", "score": 1. - generation * .001, "source_kind": "common_seed"} if generation == 0 else {
                    "origin": f"flash/r{repeat}/{generation * 10 - 3:02d}", "score": 1. - generation * .001, "source_kind": "generated"}
                after = {"origin": f"flash/r{repeat}/{generation * 10 + 7:02d}", "score": 1. - (generation + 1) * .001, "source_kind": "generated"}
                _dump(target / "summary.json", {"generation_index": generation, "generation_number": generation + 1,
                    "status": "complete", "metric": METRIC, "proposals_expected": 10, "proposals_recorded": 10,
                    "valid": 8, "invalid": 2, "best_before": before, "best_after": after, "best_generated_so_far": after,
                    "candidates": [{"index": generation * 10 + index, "valid": index < 8} for index in range(10)]})
        history_path = root / "synthetic_history.json"
        historical_rows = []
        for index, spec in enumerate(specs):
            groups = {}
            for arm, shift in (("evolution", 0.), ("baek", 1.)):
                mean = 100. + index + shift
                groups[arm] = {"cost": mean, "generation_costs": [mean - 1, mean, mean + 1], "generation_sd": 1.}
            historical_rows.append({**spec, "groups": groups})
        _dump(history_path, {"comparison_complete": True, "scenarios": historical_rows})
        result = build_report(root, history_path)
        assert result["complete"] and len(result["scenario_results"]) == 20
        assert result["aggregates"]["transfer_8"]["scenario_count"] == 8
        assert math.isclose(result["aggregates"]["all_20"]["cost"]["mean"], 111.5)
        assert math.isclose(result["aggregates"]["all_20"]["cost"]["sample_sd"], 1.)
        assert math.isclose(result["aggregates"]["all_20"]["optimizer_reduction_pct"]["mean"], 20.)
        assert result["selected_origin_counts"] == {"common_seed": 1, "generated": 2, "unknown": 0}
        assert result["training_trajectories"]["repeats"][0]["invalid_count"] == 20
        assert result["historical_reference"]["complete"] and result["historical_reference"]["paired_statistics"] is False
        expected_gap = statistics.mean(100 * (2. / (100. + index)) for index in range(20))
        assert math.isclose(result["historical_reference"]["equal_scenario_mean_cost_gap_pct"]["evolution"], expected_gap)
        assert result["model_api_accounting"]["models"]["flash"]["actual_cost_usd"] is None
        assert (root / "report.md").exists() and (root / "report_summary.json").exists()
        generation_path = root / "runs/flash/r1/generations/09/summary.json"
        saved_generation = generation_path.read_text()
        generation_path.unlink()
        result = build_report(root, None)
        assert result["test_results_complete"] and not result["complete"]
        generation_path.write_text(saved_generation)
        test_path = root / "runs/flash/r2/test.json"
        saved_test = test_path.read_text()
        test_path.unlink()
        result = build_report(root, None)
        assert not result["complete"] and result["aggregates"]["all_20"]["cost"]["mean"] is None
        test_path.write_text(saved_test)
        raw_path = root / "runs/flash/r3/test_raw.json"
        raw = json.loads(raw_path.read_text())
        raw["valid"] = False
        _dump(raw_path, raw)
        result = build_report(root, None)
        assert not result["complete"] and result["aggregates"]["all_20"]["optimizer_reduction_pct"]["mean"] is None
        return {"ok": True, "synthetic_only": True, "checks": ["20 cases / 3 repeats", "8 transfer cases",
            "cost mean and SD", "conditional optimizer reduction", "common seed fallback", "30 generation summaries",
            "historical descriptive comparison without pairing", "missing generation/test/raw gates", "unknown optional ledger"]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--run", type=Path)
    mode.add_argument("--self-test", action="store_true")
    parser.add_argument("--historical-summary", type=Path, default=DEFAULT_HISTORY)
    parser.add_argument("--no-history", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        print(json.dumps(self_test(), ensure_ascii=False))
    else:
        result = build_report(args.run, None if args.no_history else args.historical_summary)
        print(json.dumps({"complete": result["complete"], "test_results_complete": result["test_results_complete"],
                          "report": str(args.run / "report.md")}, ensure_ascii=False))


if __name__ == "__main__":
    main()
