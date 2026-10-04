"""Combine completed report tables without running policies, simulations or APIs.

The input boundary is report CSV/JSON plus resource_summary.json. This module
never opens raw test files. --self-test uses fabricated temporary fixtures only.
"""
from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import statistics
import tempfile


REPO = Path(__file__).resolve().parents[3]
DEFAULT_RUN = REPO / "output/overnight_search/20260917"
ARMS = ("one_query", "best_of_n", "evolution", "baek")
NUMERIC = ARMS[:3]
LABELS = {"one_query": "单次查询", "best_of_n": "独立生成择优", "evolution": "反馈演化", "baek": "Baek-style L2"}
METHODS = tuple(f"{arm}_r{repeat}" for arm in ARMS for repeat in (1, 2, 3))
EXPECTED_PATHS = 128


def grid(profile):
    return [dict(profile=profile, name=f"perish_m{m}_L2_cv{cv:g}_f{f:g}", m=m, cv=cv, f=f,
                 split="transfer" if m in (4, 8) else "discovery")
            for m in ((3, 4, 5) if profile == "primary" else (7, 8))
            for cv in (1.5, 2.) for f in (0., .5)]


def number(value):
    if isinstance(value, bool):
        raise ValueError("Boolean in numeric field")
    result = float(value)
    if not math.isfinite(result):
        raise ValueError("Nonfinite numeric field")
    return result


def close(x, y):
    return math.isclose(number(x), number(y), rel_tol=1e-9, abs_tol=1e-8)


def gain(candidate, reference):
    return 100. * (reference - candidate) / reference if reference > 0 else None


def fmt(value, places=2):
    return "缺" if value is None else f"{value:.{places}f}"


def dump(path, record):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(record, ensure_ascii=False, indent=2, allow_nan=False) + "\n")


def read_input(path, hashes, problems, *, csv_file=False, required=True):
    if not path.exists():
        if required:
            problems.append(f"缺少输入：{path}")
        return [] if csv_file else {}
    try:
        raw = path.read_bytes()
        hashes[str(path)] = hashlib.sha256(raw).hexdigest()
        if csv_file:
            return list(csv.DictReader(raw.decode("utf-8-sig").splitlines()))
        result = json.loads(raw)
        if not isinstance(result, dict):
            raise ValueError("Expected JSON object")
        return result
    except (OSError, UnicodeError, ValueError) as error:
        problems.append(f"无法读取 {path}: {error}")
        return [] if csv_file else {}


def index_rows(rows, fields, problems, label):
    result, duplicates = {}, set()
    for row in rows:
        key = tuple(row.get(field, "") for field in fields)
        if key in result or key in duplicates:
            problems.append(f"{label}: 重复记录 {key}")
            duplicates.add(key)
            result.pop(key, None)
        else:
            result[key] = row
    return result


def validate_pair(row, candidate_cost, reference_cost):
    expected = gain(candidate_cost, reference_cost)
    if expected is None or row is None:
        raise ValueError("Missing pair or nonpositive reference cost")
    if not (close(row["candidate_cost"], candidate_cost) and close(row["reference_cost"], reference_cost)
            and close(row["improvement_pct"], expected) and number(row["paths"]) == EXPECTED_PATHS):
        raise ValueError("Pair costs, percentage or path count do not match source groups")
    lo, hi = number(row["improvement_ci_low"]), number(row["improvement_ci_high"])
    if lo > hi:
        raise ValueError("Reversed confidence interval")
    return dict(candidate_cost=candidate_cost, reference_cost=reference_cost,
                improvement_pct=expected, improvement_ci_low=lo, improvement_ci_high=hi)


def load_profile(root, profile, hashes, problems):
    directory = root if profile == "primary" else root / "extended"
    summary = read_input(directory / "report_summary.json", hashes, problems)
    raw = {name: read_input(directory / "tables" / (name + ".csv"), hashes, problems, csv_file=True)
           for name in ("per_run", "group_summary", "paired_comparisons", "optimizer_ablation")}
    records = index_rows(raw["per_run"], ("name", "method"), problems, profile + "/per_run")
    groups = index_rows(raw["group_summary"], ("name", "method"), problems, profile + "/groups")
    pairs = index_rows(raw["paired_comparisons"], ("name", "candidate", "reference"), problems, profile + "/pairs")
    ablations = index_rows(raw["optimizer_ablation"], ("name", "method"), problems, profile + "/ablation")
    specs = grid(profile)
    accepted_runs, accepted_groups, accepted_pairs, accepted_ablations = {}, {}, {}, {}
    for spec in specs:
        name = spec["name"]
        for method in METHODS:
            try:
                row = records[name, method]
                cost = number(row["cost"])
                if cost < 0 or number(row["paths"]) != EXPECTED_PATHS:
                    raise ValueError("Cost or planned path count invalid")
                accepted_runs[name, method] = cost
            except (KeyError, TypeError, ValueError) as error:
                problems.append(f"{profile}/{name}/{method}: 缺失或无效逐次生成记录 ({error})")
        for arm in ARMS:
            try:
                costs = [accepted_runs[name, f"{arm}_r{repeat}"] for repeat in (1, 2, 3)]
                cost, sd = statistics.mean(costs), statistics.stdev(costs)
                row = groups[name, arm]
                if not (number(row["generations"]) == 3 and number(row["paths"]) == EXPECTED_PATHS
                        and close(row["cost"], cost) and close(row["generation_sd"], sd)
                        and close(row["best_generation_cost"], min(costs))
                        and close(row["worst_generation_cost"], max(costs))):
                    raise ValueError("Group summary does not match all three generated-policy costs")
                accepted_groups[name, arm] = dict(cost=cost, generation_sd=sd, generation_costs=costs,
                                                  best=min(costs), worst=max(costs))
            except (KeyError, TypeError, ValueError) as error:
                problems.append(f"{profile}/{name}/{arm}: 缺失或无效三重复汇总 ({error})")
        for reference in ("one_query", "best_of_n", "baek"):
            try:
                accepted_pairs[name, reference] = validate_pair(
                    pairs.get((name, "evolution", reference)), accepted_groups[name, "evolution"]["cost"],
                    accepted_groups[name, reference]["cost"])
            except (KeyError, TypeError, ValueError) as error:
                problems.append(f"{profile}/{name}/evolution vs {reference}: 配对记录不可用 ({error})")
        for arm in NUMERIC:
            checked = []
            for repeat in (1, 2, 3):
                method = f"{arm}_r{repeat}"
                try:
                    row = ablations[name, method]
                    reference = number(row["reference_cost"])
                    checked.append(validate_pair(row, accepted_runs[name, method], reference))
                except (KeyError, TypeError, ValueError):
                    pass
            if len(checked) == 3:
                tuned = statistics.mean(row["candidate_cost"] for row in checked)
                raw_cost = statistics.mean(row["reference_cost"] for row in checked)
                accepted_ablations[name, arm] = dict(tuned_cost=tuned, raw_cost=raw_cost,
                                                     improvement_pct=gain(tuned, raw_cost))
    n = len(specs)
    complete = (summary.get("complete_primary_comparison") is True and summary.get("n_scenarios") == n
                and len(accepted_runs) == n * 12 and len(accepted_groups) == n * 4 and len(accepted_pairs) == n * 3)
    if summary.get("complete_primary_comparison") is not True:
        problems.append(f"{profile}: 原始报告未标记完整")
    return dict(profile=profile, complete=complete, specs=specs, runs=accepted_runs, groups=accepted_groups,
                pairs=accepted_pairs, ablations=accepted_ablations, source_summary=summary)


def aggregate(values, planned):
    values = [value for value in values if value is not None]
    return dict(observed=len(values), planned=planned, mean_pct=statistics.mean(values) if values else None,
                median_pct=statistics.median(values) if values else None,
                minimum_pct=min(values) if values else None, maximum_pct=max(values) if values else None,
                positive=sum(value > 0 for value in values), nonpositive=sum(value <= 0 for value in values))


def screen_against_baek(candidate, baek):
    """Apply the descriptive screen to all three costs; do not select a draw."""
    if candidate is None or baek is None:
        return None
    improvement = gain(candidate["cost"], baek["cost"])
    if improvement is None:
        return None
    return dict(improvement_pct=improvement, candidate_mean_cost=candidate["cost"],
                baek_mean_cost=baek["cost"], candidate_worst_cost=candidate["worst"],
                baek_best_cost=baek["best"],
                robust_screen_candidate=candidate["worst"] < baek["best"] and improvement >= 1.)


def resources(root, hashes, problems):
    record = read_input(root / "resource_summary.json", hashes, problems)
    try:
        fees = record["budget"]
        components = []
        for name, allocation in (("framework", 35.), ("baek", 12.)):
            row = fees[name]
            known, held = number(row["known_usd"]), number(row["held_usd"])
            if min(known, held) < 0 or number(row["allocated_usd"]) != allocation:
                raise ValueError("Unexpected ledger allocation or negative cost")
            components.append(dict(component=name, known_usd=known, held_usd=held, allocated_usd=allocation))
        known, held = sum(x["known_usd"] for x in components), sum(x["held_usd"] for x in components)
        if not (close(record["total_known_usd"], known) and close(record["total_held_usd"], held)):
            raise ValueError("Cumulative totals disagree with the two shared ledgers")
        budget = dict(available=True, components=components, known_usd=known, held_usd=held,
                      committed_usd=known + held, user_limit_usd=50., within_50=known + held <= 50.000001,
                      accounting="One cumulative framework ledger plus one cumulative Baek ledger; phases are never summed again.")
    except (KeyError, TypeError, ValueError) as error:
        problems.append(f"资源账本不可确认：{error}")
        budget = dict(available=False, known_usd=None, held_usd=None, committed_usd=None, within_50=None)
    rows = record.get("numeric", []) + record.get("baek", [])
    indexed = index_rows(rows, ("profile", "arm", "repeat"), problems, "resources")
    totals, all_complete = [], True
    fields = ("api_requests", "api_known_usd", "api_held_usd", "input_tokens", "output_tokens")
    for profile in ("primary", "extended"):
        for arm in ARMS:
            found = [indexed.get((profile, arm, repeat)) for repeat in (1, 2, 3)]
            if any(row is None or row.get("completed") is not True for row in found):
                all_complete = False
            def summed(field):
                try:
                    values = [number(row[field]) for row in found]
                    if min(values) < 0:
                        raise ValueError("Negative resource count")
                    return sum(values)
                except (KeyError, TypeError, ValueError):
                    return None
            total = dict(profile=profile, arm=arm, **{field: summed(field) for field in fields},
                         recorded_compute_seconds=summed("python_seconds" if arm == "baek" else "fit_worker_wall_seconds"),
                         compute_scope="tool wall seconds" if arm == "baek" else "successful candidate fitting worker seconds",
                         objective_or_tool_calls=summed("tool_calls" if arm == "baek" else "fit_objective_calls"))
            if any(total[key] is None for key in fields + ("recorded_compute_seconds", "objective_or_tool_calls")):
                all_complete = False
            totals.append(total)
    return dict(available=bool(record), complete=budget["available"] and all_complete,
                budget=budget, groups=totals, notes=record.get("notes", []))


def build_report(root, *, synthetic=False):
    root = Path(root).resolve()
    hashes, problems = {}, []
    phases = [load_profile(root, profile, hashes, problems) for profile in ("primary", "extended")]
    comparison_complete = all(phase["complete"] for phase in phases)
    resource = resources(root, hashes, problems)
    scenarios, robust, optimizer, contrasts, secondary_screens = [], [], [], [], []
    secondary_candidates = {arm: [] for arm in NUMERIC}
    for phase in phases:
        for spec in phase["specs"]:
            name = spec["name"]
            groups = {arm: phase["groups"].get((name, arm)) for arm in ARMS}
            pairs = {arm: phase["pairs"].get((name, arm)) for arm in ("one_query", "best_of_n", "baek")}
            evo, baek = groups["evolution"], groups["baek"]
            screen = None
            if evo and baek and pairs["baek"]:
                screen = bool(evo["worst"] < baek["best"] and pairs["baek"]["improvement_pct"] >= 1.)
            row = dict(**spec, groups=groups, comparisons=pairs, robust_screen_candidate=screen)
            scenarios.append(row)
            if comparison_complete and screen:
                robust.append(dict(**spec, improvement_pct=pairs["baek"]["improvement_pct"],
                                   evolution_worst_cost=evo["worst"], baek_best_cost=baek["best"]))
            for arm in NUMERIC:
                secondary = screen_against_baek(groups[arm], baek)
                entry = dict(**spec, method=arm, reference="baek", comparison=secondary,
                             robust_screen_candidate=(secondary["robust_screen_candidate"]
                                                      if comparison_complete and secondary else None))
                secondary_screens.append(entry)
                if entry["robust_screen_candidate"]:
                    secondary_candidates[arm].append(dict(**spec, method=arm, **secondary))
    for scope in ("primary", "extended", "combined"):
        selected = [phase for phase in phases if scope == "combined" or phase["profile"] == scope]
        planned = sum(len(phase["specs"]) for phase in selected)
        for arm in NUMERIC:
            values = [row["improvement_pct"] for phase in selected
                      for (name, method), row in phase["ablations"].items() if method == arm]
            optimizer.append(dict(scope=scope, arm=arm, **aggregate(values, planned)))
        for reference in ("one_query", "best_of_n", "baek"):
            rows = [row for phase in selected for (name, method), row in phase["pairs"].items() if method == reference]
            contrasts.append(dict(scope=scope, reference=reference,
                                  **aggregate([row["improvement_pct"] for row in rows], planned),
                                  path_ci_above_zero=sum(row["improvement_ci_low"] > 0 for row in rows),
                                  path_ci_below_zero=sum(row["improvement_ci_high"] < 0 for row in rows)))
    optimizer_complete = sum(len(phase["ablations"]) for phase in phases) == 60
    summary = dict(generated_utc=datetime.now(timezone.utc).isoformat(), synthetic_fixture=synthetic,
                   complete=comparison_complete and optimizer_complete and resource["complete"],
                   comparison_complete=comparison_complete, optimizer_complete=optimizer_complete,
                   resource_summary_complete=resource["complete"], planned_scenarios=20,
                   validated_principal_runs=sum(len(phase["runs"]) for phase in phases), expected_principal_runs=240,
                   validated_three_draw_groups=sum(len(phase["groups"]) for phase in phases), expected_three_draw_groups=80,
                   robust_candidates=robust,
                   robust_counts_by_phase={profile:sum(row["profile"] == profile for row in robust)
                                           if comparison_complete else None for profile in ("primary", "extended")},
                   secondary_method_screens=secondary_screens,
                   secondary_robust_candidates_by_method=secondary_candidates,
                   secondary_robust_counts_by_phase={arm: {
                       profile: sum(row["profile"] == profile for row in secondary_candidates[arm])
                       if comparison_complete else None for profile in ("primary", "extended")}
                       for arm in NUMERIC},
                   secondary_selection_inference="Parallel secondary screens use each method's three fixed draws and the same worst-vs-best plus 1% mean-gain rule. Selection among methods is exploratory, without multiplicity correction; only evolution retains the original primary criterion. No confidence intervals are reconstructed from aggregate costs.",
                   evolution_specific_advantage_claimed=False,
                   scenarios=scenarios, optimizer_aggregates=optimizer,
                   evolution_comparisons=contrasts, resources=resource, problems=problems, input_sha256=hashes,
                   inference="Exploratory full-family screen; three-draw means; path CIs conditional on fixed generated policies; no test-selected best draw.")
    lines = ["# 今晚的实例筛查：" + ("两阶段完整汇总" if summary["complete"] else "两阶段汇总（尚未完成）"), ""]
    if synthetic:
        lines += ["**合成数据自检；不是研究结果。**", ""]
    if not comparison_complete:
        lines += [f"主比较尚未完成：通过校验的逐次生成记录 {summary['validated_principal_runs']}/240，三重复汇总 {summary['validated_three_draw_groups']}/80。不得据部分结果宣布找到或未找到目标实例。"]
    elif robust:
        lines += [f"全部 20 个场景中，{len(robust)} 个满足固定筛查条件：最差演化重复的成本仍低于最好 Baek 重复，且三重复均值降本至少 1%。这是待独立确认的候选，不是普遍优越性的证明。",
                  "", "候选：" + "；".join(f"m={x['m']}, CV={x['cv']:g}, f={x['f']:g}（{x['improvement_pct']:.2f}%）" for x in robust) + "。"]
    else:
        lines += ["全部 20 个场景均已比较，本轮没有实例满足原先针对反馈演化的固定稳健筛查条件。单次查询与独立生成择优的次要筛查另列，不能把它们的结果归为演化获胜。"]
    if not summary["complete"]:
        lines += ["", f"交付完整性：主比较{'完整' if comparison_complete else '未完整'}；optimizer 消融{'完整' if optimizer_complete else '仍有缺失'}；资源汇总{'完整' if resource['complete'] else '仍有缺失或待核对'}。"]
    lines += ["", "## 全部 20 个场景", "",
              "每格为三次生成的平均每期成本 ± 生成间样本标准差，成本越低越好。改善为100×(Baek−演化)/Baek；负值也保留。†仅标记数值结构搜索组未获搜索反馈的迁移场景。", "",
              "| 阶段/场景 | 单次查询 | 独立生成择优 | 反馈演化 | Baek-style L2 | 演化对Baek改善% [95%路径区间] | 固定筛查 |",
              "|---|---:|---:|---:|---:|---:|---|"]
    for row in scenarios:
        cells = ["缺" if row["groups"][arm] is None else f"{row['groups'][arm]['cost']:.3f} ± {row['groups'][arm]['generation_sd']:.3f}" for arm in ARMS]
        pair = row["comparisons"]["baek"]
        effect = "缺" if pair is None else f"{fmt(pair['improvement_pct'])} [{fmt(pair['improvement_ci_low'])}, {fmt(pair['improvement_ci_high'])}]"
        flag = "待完整" if not comparison_complete else ("候选" if row["robust_screen_candidate"] else "未达条件")
        label = f"{'一期' if row['profile']=='primary' else '二期'} m={row['m']}, CV={row['cv']:g}, f={row['f']:g}" + (" †" if row["split"] == "transfer" else "")
        lines.append("| " + " | ".join([label, *cells, effect, flag]) + " |")
    lines += ["", "路径区间是在固定这三份生成策略后，对共同需求路径索引进行配对bootstrap得到的条件区间；不是模型生成不确定性的区间。生成标准差单列。没有对多个实例/参照作多重比较校正，固定筛查门槛也不等同于统计显著性。", "",
              "## 三种数值结构搜索方法的平行次要筛查", "",
              "保留上面的演化主判据，同时分别对单次查询、独立生成择优和反馈演化沿用相同门槛：该方法最差的生成重复成本严格低于最好Baek重复，且三重复平均成本降低至少1%。这里没有选择测试集上最好的生成重复。**在多种方法中挑选胜者属于探索性选择，未作多重比较校正；单次查询或独立生成择优通过条件不能被称为AIPS反馈演化获胜。**", "",
              "| 方法 | 一期候选/12 | 二期候选/8 | 全部候选/20 |",
              "|---|---:|---:|---:|"]
    for arm in NUMERIC:
        counts = summary["secondary_robust_counts_by_phase"][arm]
        total = str(len(secondary_candidates[arm])) if comparison_complete else "待完整"
        lines.append(f"| {LABELS[arm]} | {counts['primary'] if comparison_complete else '待完整'} | {counts['extended'] if comparison_complete else '待完整'} | {total} |")
    lines += ["", "全部场景的每格为相对Baek三次生成均值的改善百分比及是否通过门槛。完整候选名单按方法分开保存在JSON中。此表是描述性筛查，不从已汇总均值重建单次查询/独立生成对Baek的配对路径区间。", "",
              "| 阶段/场景 | 单次查询：改善% / 筛查 | 独立生成择优：改善% / 筛查 | 反馈演化：改善% / 筛查 |",
              "|---|---:|---:|---:|"]
    secondary_lookup = {(row["profile"], row["name"], row["method"]): row for row in secondary_screens}
    for row in scenarios:
        label = f"{'一期' if row['profile']=='primary' else '二期'} m={row['m']}, CV={row['cv']:g}, f={row['f']:g}" + (" †" if row["split"] == "transfer" else "")
        cells = []
        for arm in NUMERIC:
            screen = secondary_lookup[row["profile"], row["name"], arm]
            flag = "待完整" if screen["robust_screen_candidate"] is None else ("候选" if screen["robust_screen_candidate"] else "未达条件")
            value = None if screen["comparison"] is None else screen["comparison"]["improvement_pct"]
            cells.append(f"{fmt(value)} / {flag}")
        lines.append("| " + " | ".join([label, *cells]) + " |")
    lines += ["", "## optimizer 与结构搜索贡献", "",
              "下表按场景等权：每个场景先分别平均三次生成的原始参数成本与调参成本，再计算降本率；仅纳入三份配对都齐全的场景。均值/中位数/范围是描述性汇总，没有把不同场景或生成重复当作独立路径拼接置信区间。", "",
              "| 范围 | 方法 | 完整场景 | optimizer平均改善% | 中位数% | 最小–最大% | 改善/未改善场景 |",
              "|---|---|---:|---:|---:|---:|---:|"]
    for row in optimizer:
        lines.append(f"| {row['scope']} | {LABELS[row['arm']]} | {row['observed']}/{row['planned']} | {fmt(row['mean_pct'])} | {fmt(row['median_pct'])} | {fmt(row['minimum_pct'])}–{fmt(row['maximum_pct'])} | {row['positive']}/{row['nonpositive']} |")
    lines += ["", "这项消融固定了由优化管线选出的结构，只比较其原始常数与拟合常数。因此收益是**以优化后结构选择为条件的调参收益**；并非移除optimizer后重新搜索的完整消融，也不能单独证明演化发现新结构。", "",
              "| 范围 | 演化的参照 | 完整场景 | 演化平均改善% | 中位数% | 路径区间全正/全负场景 |",
              "|---|---|---:|---:|---:|---:|"]
    for row in contrasts:
        lines.append(f"| {row['scope']} | {LABELS[row['reference']]} | {row['observed']}/{row['planned']} | {fmt(row['mean_pct'])} | {fmt(row['median_pct'])} | {row['path_ci_above_zero']}/{row['path_ci_below_zero']} |")
    lines += ["", "本汇总不把对Baek的优势自动解释为反馈演化独有。即使相对Baek通过筛查，若单次查询或独立生成择优得到相近或更好的成本，也不能把优势专门归因于多轮反馈演化。这里列出三个参照的全部结果，不通过挑选较弱参照宣布演化获胜。", "",
              "## 实际资源与费用", ""]
    budget = resource["budget"]
    if budget["available"]:
        lines += [f"两阶段共用的两本账累计已知实付 **${budget['known_usd']:.4f}**，未决预留上界 **${budget['held_usd']:.4f}**，合计占用 **${budget['committed_usd']:.4f}** / $50。这里只计一次累计账本；没有把两份阶段报告中的累计费用相加。框架分配$35、Baek分配$12，另有$3未分配。"]
        if not budget["within_50"]:
            lines += ["", "**已知费用加预留超过用户$50上限，必须保留这一预算异常。**"]
    else:
        lines += ["资源汇总缺失或不一致，当前不能确认总费用；不会把未知费用写成零。"]
    lines += ["", "| 阶段 | 方法 | API请求 | 已知$ | 未决$ | 输入/输出token | 已记录计算秒 | objective/工具调用 |",
              "|---|---|---:|---:|---:|---:|---:|---:|"]
    for row in resource["groups"]:
        lines.append(f"| {row['profile']} | {LABELS[row['arm']]} | {fmt(row['api_requests'],0)} | {fmt(row['api_known_usd'],4)} | {fmt(row['api_held_usd'],4)} | {fmt(row['input_tokens'],0)}/{fmt(row['output_tokens'],0)} | {fmt(row['recorded_compute_seconds'],1)} | {fmt(row['objective_or_tool_calls'],0)} |")
    lines += ["", "数值组计算秒仅包含已记录的成功候选拟合worker时间，objective数不包含共用基线、验证、最终重拟合和测试；无计时的失败及归档旧尝试不能被当作零成本。Baek列为工具执行时间/工具调用数，口径不同。并行worker时间相加也不等于整晚历时，以上不是完整CPU消耗审计。", "",
              "一期单次查询产生4候选，独立生成/演化各8；二期三组均为8候选并获得同一初始基线信息。同一候选优化上限不代表相同实际总计算，LLM次数、token、美元与时间也未匹配。Baek保留通用Python/SciPy工具，最多50次工具调用、3600秒工具时间及每场景600秒设计阶段上限；二期各方法均受1 GiB worker内存监测。比较是同模型、明确资源条件下的工作流比较，不是CPU或LLM预算完全匹配的算法对决。", "",
              "## 解释边界与可复查材料", "",
              "m=4/m=8仅对三个数值结构搜索组是不提供搜索反馈的结构迁移场景，之后仍按实例重新拟合系数。Baek预先知道完整公开参数族，可自行模拟和适配所有组合；它们不是双方共同的未知参数holdout。二期是在一期和规模诊断之后提出的探索性协议修订，更高年龄维度不自动意味着经济问题更难。", "",
              "m=3小实例的精确DP是共同库存容量下的经典OR参考与最优性证书，不能记作AIPS生成的成果；模拟均值偶然低于长期DP证书也不是突破最优值。修正后的nested-logit公开策略复核没有发现期待的稳定失败区域，这条阴性结果也保留。", "",
              "这里比较的是Baek-style L2适配，不是原论文数值复现：需求CV与容量采用已经披露的论文文字口径，和公开DynaPlex代码口径存在差异。仅击败当前基线不能声称已击败尚未实现的PIL/APIL或DCL。训练机制备忘录只提出假设，不能替代最终结果或机制因果消融。", ""]
    links = [(root / "report.md", "一期完整报告"), (root / "extended/report.md", "二期完整报告"),
             (root / "tables/paired_comparisons.csv", "一期全部配对结果"),
             (root / "extended/tables/paired_comparisons.csv", "二期全部配对结果"),
             (root / "tables/dp_comparison.csv", "小实例DP参考"), (root / "resource_summary.json", "累计资源记录"),
             (REPO / "docs/overnight_perishable_spec.md", "实例定义与模型口径"),
             (REPO / "docs/overnight_implementation_audit.md", "实现审计与中性兼容修复"),
             (REPO / "docs/overnight_policy_mechanisms.md", "机制备忘录：仅训练与源码"),
             (REPO / "docs/overnight_nested_diagnostic.md", "修正后nested-logit阴性复核"),
             (root / "night_summary.json", "本汇总的校验记录与输入SHA256")]
    lines += [f"- [{label}]({path})" for path, label in links]
    if problems:
        lines += ["", "## 缺失或不一致输入", ""] + ["- " + problem for problem in problems]
    dump(root / "night_summary.json", summary)
    (root / "night_summary.md").write_text("\n".join(lines) + "\n")
    return summary


def write_csv(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def synthetic_fixture(root, *, wins=True, means_by_arm=None):
    """Fabricate already-aggregated tables; never create/read real test tapes."""
    for profile in ("primary", "extended"):
        directory = root if profile == "primary" else root / "extended"
        runs, groups, pairs, ablations = [], [], [], []
        for spec in grid(profile):
            name, means = spec["name"], {}
            for arm in ARMS:
                mean = (110. if wins else 98.) if arm == "baek" else 100.
                mean = (means_by_arm or {}).get(arm, mean)
                costs = [mean - .2, mean, mean + .2]
                means[arm] = mean
                for repeat, cost in enumerate(costs, 1):
                    method = f"{arm}_r{repeat}"
                    runs.append(dict(name=name, method=method, cost=cost, paths=128))
                    if arm in NUMERIC:
                        raw = cost * (1.2 if spec["f"] == 0 else .98)
                        pct = gain(cost, raw)
                        ablations.append(dict(name=name, method=method, candidate_cost=cost, reference_cost=raw,
                                              improvement_pct=pct, improvement_ci_low=pct-.1, improvement_ci_high=pct+.1, paths=128))
                groups.append(dict(name=name, method=arm, cost=mean, generation_sd=statistics.stdev(costs),
                                   generations=3, best_generation_cost=min(costs), worst_generation_cost=max(costs), paths=128))
            for reference in ("one_query", "best_of_n", "baek"):
                pct = gain(means["evolution"], means[reference])
                pairs.append(dict(name=name, candidate="evolution", reference=reference,
                                  candidate_cost=means["evolution"], reference_cost=means[reference], improvement_pct=pct,
                                  improvement_ci_low=pct-.1, improvement_ci_high=pct+.1, paths=128))
        for filename, rows in (("per_run", runs), ("group_summary", groups), ("paired_comparisons", pairs), ("optimizer_ablation", ablations)):
            write_csv(directory / "tables" / (filename + ".csv"), rows)
        # Deliberately impossible phase budget values prove they are not summed.
        dump(directory / "report_summary.json", dict(complete_primary_comparison=True,
             n_scenarios=len(grid(profile)), budget=dict(recorded_known_usd=999.)))
    numeric, baek = [], []
    for profile in ("primary", "extended"):
        for arm in ARMS:
            for repeat in (1, 2, 3):
                row = dict(profile=profile, arm=arm, repeat=repeat, completed=True, api_requests=1,
                           api_known_usd=.5, api_held_usd=0., input_tokens=100, output_tokens=100)
                if arm == "baek":
                    baek.append(dict(row, tool_calls=1, python_seconds=1.))
                else:
                    numeric.append(dict(row, fit_worker_wall_seconds=1., fit_objective_calls=10))
    dump(root / "resource_summary.json", dict(budget={"framework":dict(known_usd=15.,held_usd=.5,allocated_usd=35.),
         "baek":dict(known_usd=5.,held_usd=.5,allocated_usd=12.)}, total_known_usd=20.,total_held_usd=1.,numeric=numeric,baek=baek,notes=[]))


def self_test():
    with tempfile.TemporaryDirectory(prefix="overnight_combined_synthetic_") as temporary:
        root = Path(temporary)
        empty = build_report(root, synthetic=True)
        assert not empty["complete"] and not empty["robust_candidates"]
        synthetic_fixture(root)
        complete = build_report(root, synthetic=True)
        assert complete["complete"] and complete["validated_principal_runs"] == 240
        assert complete["validated_three_draw_groups"] == 80 and len(complete["robust_candidates"]) == 20
        assert len(complete["secondary_method_screens"]) == 60
        assert all(len(rows) == 20 for rows in complete["secondary_robust_candidates_by_method"].values())
        assert {row["name"] for row in complete["robust_candidates"]} == {
            row["name"] for row in complete["secondary_robust_candidates_by_method"]["evolution"]}
        assert complete["resources"]["budget"]["committed_usd"] == 21.
        assert all(row["mean_pct"] == 0. for row in complete["evolution_comparisons"] if row["reference"] != "baek")
        assert all(row["nonpositive"] > 0 for row in complete["optimizer_aggregates"])
        file = root / "extended/tables/per_run.csv"
        rows = list(csv.DictReader(file.open()))
        write_csv(file, rows[:-1])
        missing = build_report(root, synthetic=True)
        assert not missing["comparison_complete"] and not missing["robust_candidates"]
        assert not any(missing["secondary_robust_candidates_by_method"].values())
        write_csv(file, rows + [rows[0]])
        duplicate = build_report(root, synthetic=True)
        assert not duplicate["comparison_complete"] and not duplicate["robust_candidates"]
        synthetic_fixture(root, wins=False)
        no_wins = build_report(root, synthetic=True)
        assert no_wins["complete"] and not no_wins["robust_candidates"]
        assert not any(no_wins["secondary_robust_candidates_by_method"].values())
        file = root / "tables/group_summary.csv"
        rows = list(csv.DictReader(file.open()))
        rows[0]["generation_sd"] = "999"
        write_csv(file, rows)
        mismatch = build_report(root, synthetic=True)
        assert not mismatch["comparison_complete"]
        synthetic_fixture(root, means_by_arm=dict(one_query=100., best_of_n=105., evolution=112., baek=110.))
        secondary_only = build_report(root, synthetic=True)
        assert secondary_only["complete"] and not secondary_only["robust_candidates"]
        assert len(secondary_only["secondary_robust_candidates_by_method"]["one_query"]) == 20
        assert len(secondary_only["secondary_robust_candidates_by_method"]["best_of_n"]) == 20
        assert not secondary_only["secondary_robust_candidates_by_method"]["evolution"]
        assert not secondary_only["evolution_specific_advantage_claimed"]
        boundary = screen_against_baek(dict(cost=99., worst=99.5), dict(cost=100., best=99.8))
        assert boundary["robust_screen_candidate"] and boundary["improvement_pct"] == 1.
        assert not screen_against_baek(dict(cost=99., worst=99.8), dict(cost=100., best=99.8))["robust_screen_candidate"]
        assert not screen_against_baek(dict(cost=99.01, worst=99.5), dict(cost=100., best=99.8))["robust_screen_candidate"]
        synthetic_fixture(root)
        (root / "resource_summary.json").unlink()
        no_budget = build_report(root, synthetic=True)
        assert no_budget["comparison_complete"] and not no_budget["complete"]
    return dict(complete_240_run_fixture="passed", negative_result="passed", missing_and_duplicate_runs="rejected",
                mismatched_generation_sd="rejected", conditional_ablation="passed", tied_other_arms="preserved",
                single_cumulative_budget="21, not sum of phase summaries", missing_budget="incomplete",
                parallel_secondary_screens="all three methods, no best-draw selection",
                secondary_only_wins="kept separate from evolution primary", screen_boundaries="passed",
                real_final_data_read=False, policy_evaluations=0, api_calls=0)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path, default=DEFAULT_RUN)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        print(json.dumps(self_test(), ensure_ascii=False, indent=2))
    else:
        result = build_report(args.run_dir)
        print(json.dumps({key:result[key] for key in ("complete", "comparison_complete", "validated_principal_runs", "robust_candidates")},ensure_ascii=False,indent=2))


if __name__ == "__main__":
    main()
