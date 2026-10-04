"""Read-only comparison of frozen capped/unrestricted parameter experiments.

Only comparison artifacts under --output-dir are written. No policies, training,
provider clients, or existing report writers are invoked.
"""
from __future__ import annotations

import argparse
import ast
from collections import Counter
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path
import re
import sys
import tokenize

import numpy as np

from .analysis_report import HORIZONS, load_evaluations, _write_csv, _write_json
from .data import scenario_specs
from ..baek_comparison.analysis import paired_statistics


REFERENCES = ("conditional_pil", "forecast_adaptive_pil")
MODES = ("steady", "cold_start")
SEED = 2026091607
EXPLORATORY = ("旧轮测试结果已经查看，本轮是随后开展的参数数量限制消融／探索比较；"
               "两轮复用同一测试集，不是新的未见留出验证，也不能仅凭差异作因果归因。")


def _read(path):
    return json.loads(Path(path).read_text())


def _sha(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def _source_from_response(content):
    """Extract final response source using the evolution parser's convention."""
    if not isinstance(content, str):
        raise ValueError("No final response content")
    fences = re.findall(r"```(?:python)?\s*\n(.*?)```", content, re.S)
    if fences:
        return fences[0].strip()
    text = content.split("{{", 1)[0]
    start = re.search(r"^(?:import |from |def )", text, re.M)
    if start is None:
        raise ValueError("No source in final response")
    return text[start.start():].strip()


def count_opt_params(code):
    """Count distinct annotated scalar assignments, never function arguments.

    This is a source statistic, not an assertion that a candidate passed the
    execution whitelist or optimizer validation. Ambiguous declarations fail
    explicitly instead of being silently counted as zero.
    """
    tree = ast.parse(code)
    functions = [node for node in tree.body if isinstance(node, ast.FunctionDef)
                 and node.name == "compute_order_amount"]
    if len(functions) != 1:
        raise ValueError("Expected one compute_order_amount function")
    function = functions[0]
    arguments = {node.arg for node in (*function.args.posonlyargs, *function.args.args,
                                       *function.args.kwonlyargs)}
    assignments = {}
    for node in ast.walk(function):
        if isinstance(node, ast.Assign):
            assignments.setdefault(node.lineno, []).append(node)
    names = set()
    for token in tokenize.generate_tokens(io.StringIO(code).readline):
        if token.type != tokenize.COMMENT or "OPT_PARAM:" not in token.string:
            continue
        matches = assignments.get(token.start[0], [])
        if len(matches) != 1 or len(matches[0].targets) != 1 or not isinstance(matches[0].targets[0], ast.Name):
            raise ValueError("Ambiguous OPT_PARAM assignment")
        name = matches[0].targets[0].id
        if name in names or name in arguments:
            raise ValueError("Duplicate or input OPT_PARAM declaration")
        names.add(name)
    return len(names)


def parameter_inventory(root, label):
    """Inspect raw generated responses and each chain's training-selected code."""
    rows, issues, definitions = [], [], []
    for chain in sorted((root / "training").glob("*/self_evolve_h*_r*")):
        match = re.fullmatch(r"self_evolve_h(50|100|200|500)_r([123])", chain.name)
        if not match:
            continue
        horizon, repeat = map(int, match.groups())
        common = dict(run=label, scenario_id=chain.parent.name,
                      source_training_horizon=horizon, repeat=repeat,
                      scope="primary" if horizon == 200 else "horizon_extension")
        definition_path = chain / "search_definition.json"
        if definition_path.exists():
            try:
                definition = _read(definition_path)
                definitions.append(dict(common, **{key: definition.get(key) for key in
                    ("max_opt_params", "population_size", "generations", "optimizer", "optimizer_maxiter",
                     "optimizer_eps", "burnin", "horizon", "model", "training_arrays_sha256")}))
            except (OSError, ValueError) as exc:
                issues.append(dict(run=label, file=str(definition_path), error=str(exc)))
        seen = set()
        for path in sorted((chain / "model_responses").glob("*.json")):
            row = dict(common, stage="generated_response", file=str(path), opt_param_count=None)
            try:
                saved = _read(path)
                row["response_state"] = saved.get("state")
                metadata = saved.get("metadata", {})
                for key in ("generation", "operator", "candidate_index", "candidate_attempt"):
                    row[key] = metadata.get(key)
                identity = tuple(row.get(key) for key in
                                 ("generation", "operator", "candidate_index", "candidate_attempt"))
                if identity in seen:
                    raise ValueError("Duplicate generated-response slot/attempt")
                seen.add(identity)
                if saved.get("state") != "complete":
                    row["count_status"] = "pending_response"
                else:
                    code = _source_from_response(saved.get("content"))
                    row["code_sha256"] = hashlib.sha256(code.encode()).hexdigest()
                    row["opt_param_count"] = count_opt_params(code)
                    row["count_status"] = "counted"
            except (OSError, ValueError, SyntaxError, TypeError, tokenize.TokenError) as exc:
                row.update(count_status="unparseable", error=str(exc))
            rows.append(row)
        completion_path = chain / "completed.json"
        if completion_path.exists():
            row = dict(common, stage="final_training_selected", file=str(completion_path), opt_param_count=None)
            try:
                completion = _read(completion_path)
                if completion.get("status") not in {"complete", "completed"}:
                    raise ValueError("Chain is not completed")
                path = Path(completion["best_code_path"])
                path = (path if path.is_absolute() else chain / path).resolve()
                if not path.is_relative_to(chain.resolve()):
                    raise ValueError("Final source path escapes its chain")
                code = path.read_text()
                digest = hashlib.sha256(code.encode()).hexdigest()
                if digest != completion["code_sha256"]:
                    raise ValueError("Final source hash mismatch")
                row.update(code_sha256=digest, opt_param_count=count_opt_params(code), count_status="counted")
            except (OSError, KeyError, ValueError, SyntaxError, TypeError, tokenize.TokenError) as exc:
                row.update(count_status="unparseable", error=str(exc))
                issues.append(dict(run=label, file=str(completion_path), error=str(exc)))
            rows.append(row)
    summaries = []
    for scope in ("primary", "horizon_extension"):
        for stage in ("generated_response", "final_training_selected"):
            group = [row for row in rows if row["scope"] == scope and row["stage"] == stage]
            counts = [row["opt_param_count"] for row in group if row["count_status"] == "counted"]
            summaries.append(dict(run=label, scope=scope, stage=stage, observed=len(group), counted=len(counts),
                pending=sum(row["count_status"] == "pending_response" for row in group),
                unparseable=sum(row["count_status"] == "unparseable" for row in group),
                histogram=dict(sorted(Counter(counts).items())),
                minimum=min(counts) if counts else None, maximum=max(counts) if counts else None,
                mean=float(np.mean(counts)) if counts else None, median=float(np.median(counts)) if counts else None,
                above_four=sum(count > 4 for count in counts)))
    return rows, summaries, definitions, issues


def dataset_pairing(old_root, new_root):
    """Verify both manifests and supplied physical-file hashes, without scoring."""
    manifests, issues = [], []
    for label, root in (("old", old_root), ("new", new_root)):
        path = root / "dataset_manifest.json"
        if not path.exists():
            manifests.append({})
            continue
        try:
            entries = _read(path).get("files", [])
            mapping = {}
            for entry in entries:
                key = (entry["scenario_id"], entry["split"])
                if key in mapping:
                    raise ValueError("Duplicate dataset manifest key")
                value = dict(entry)
                if entry.get("file_sha256"):
                    source = (root / entry["path"]).resolve()
                    if not source.is_relative_to(root) or hashlib.sha256(source.read_bytes()).hexdigest() != entry["file_sha256"]:
                        raise ValueError("Dataset archive hash mismatch: " + str(key))
                mapping[key] = value
            manifests.append(mapping)
        except (OSError, KeyError, TypeError, ValueError) as exc:
            manifests.append({})
            issues.append(dict(run=label, file=str(path), error=str(exc)))
    rows = []
    for scenario in scenario_specs():
        for split in ("train", "validation", "test"):
            key = (scenario.scenario_id, split)
            old, new = (manifest.get(key, {}) for manifest in manifests)
            digest = old.get("arrays_sha256")
            same = bool(isinstance(digest, str) and re.fullmatch(r"[0-9a-f]{64}", digest)
                        and digest == new.get("arrays_sha256")
                        and old.get("n_paths") == new.get("n_paths")
                        and old.get("n_periods") == new.get("n_periods"))
            status = "matched" if same else "mismatch" if old and new else "missing"
            rows.append(dict(scenario_id=key[0], split=split, status=status,
                             old_arrays_sha256=digest, new_arrays_sha256=new.get("arrays_sha256"),
                             old_n_paths=old.get("n_paths"), new_n_paths=new.get("n_paths")))
    return rows, issues


def _paired_arrays(candidate, reference):
    left, right = candidate["row"], reference["row"]
    digest = left.get("dataset_arrays_sha256")
    if not digest or digest != right.get("dataset_arrays_sha256"):
        raise ValueError("Paired dataset hashes differ or are missing")
    if (candidate["arrays"]["total_cost"].shape != reference["arrays"]["total_cost"].shape
            or not np.array_equal(candidate["arrays"]["demand_units"], reference["arrays"]["demand_units"])):
        raise ValueError("Paired path shapes or ordered demand totals differ")
    if not left.get("provenance_verified") or not right.get("provenance_verified"):
        raise ValueError("Policy/dataset provenance is incomplete")


def _average(items):
    """Require all three planned draws; never choose the best or pair draw IDs."""
    if sorted(item["row"]["repeat"] for item in items) != [1, 2, 3]:
        return None
    for item in items:
        _paired_arrays(item, items[0])
    first = items[0]
    values = np.stack([item["arrays"]["total_cost"] for item in items])
    return {"row": dict(first["row"], n_repeats=3), "arrays": {
        "total_cost": values.mean(axis=0), "demand_units": first["arrays"]["demand_units"]},
        "repeat_costs_per_period": (values.mean(axis=1) / first["row"]["horizon"]).tolist()}


def _group_evaluations(records):
    groups, baselines = {}, {}
    for item in records:
        row = item["row"]
        key = (row["scenario_id"], row["source_training_horizon"], row["mode"], row["horizon"])
        if row["scope"] in {"primary", "horizon_extension"} and row["policy_id"] in {
                f"self_evolve_h{key[1]}_r{repeat}" for repeat in (1, 2, 3)}:
            groups.setdefault(key, []).append(item)
        elif row["scope"] in {"baseline", "baseline_extension"} and row["family"] in REFERENCES:
            baselines[(*key, row["family"])] = item
    return groups, baselines


def _baseline_inventory(root):
    hashes = {}
    for path in sorted((root / "baselines").glob("*/h*/records.json")):
        for name, record in _read(path).items():
            hashes[(path.parent.parent.name, int(path.parent.name[1:]), name)] = _sha(record)
    return hashes


def compare_runs(old_run, new_run, output_dir, *, n_bootstrap=5000):
    old_root, new_root, output = (Path(path).resolve() for path in (old_run, new_run, output_dir))
    if old_root == new_root or output in {old_root, new_root}:
        raise ValueError("Use distinct input runs and a dedicated comparison output directory")
    if isinstance(n_bootstrap, bool) or not isinstance(n_bootstrap, int) or n_bootstrap < 1:
        raise ValueError("bootstrap must be a positive integer")
    if output.exists() and any(output.iterdir()) and not (output / "parameter_comparison.json").exists():
        raise ValueError("Refusing to overwrite a non-comparison directory")
    pairs, issues = dataset_pairing(old_root, new_root)
    matched_tests = {row["scenario_id"] for row in pairs if row["split"] == "test" and row["status"] == "matched"}
    loaded, groups, refs = {}, {}, {}
    parameters, distributions, definitions = [], [], []
    baseline_hashes = {}
    for label, root in (("old", old_root), ("new", new_root)):
        loaded[label], errors = load_evaluations(root)
        issues.extend(dict(run=label, **error) for error in errors)
        groups[label], refs[label] = _group_evaluations(loaded[label])
        rows, summaries, settings, errors = parameter_inventory(root, label)
        parameters.extend(rows); distributions.extend(summaries); definitions.extend(settings); issues.extend(errors)
        try:
            baseline_hashes[label] = _baseline_inventory(root)
        except (OSError, TypeError, ValueError, KeyError) as exc:
            baseline_hashes[label] = {}
            issues.append(dict(run=label, error="Baseline inventory: " + str(exc)))
    all_baselines = sorted(set(baseline_hashes["old"]) | set(baseline_hashes["new"]))
    baseline_pairing = [dict(scenario_id=k[0], source_training_horizon=k[1], family=k[2],
                            status="matched" if baseline_hashes["old"].get(k) == baseline_hashes["new"].get(k)
                            else "mismatch_or_missing", old_record_sha256=baseline_hashes["old"].get(k),
                            new_record_sha256=baseline_hashes["new"].get(k)) for k in all_baselines]
    settings = {(row["run"], row["scenario_id"], row["source_training_horizon"], row["repeat"]): row for row in definitions}
    setting_differences = []
    for key, old in settings.items():
        if key[0] != "old":
            continue
        new = settings.get(("new", *key[1:]))
        if new:
            for field in ("population_size", "generations", "optimizer", "optimizer_maxiter", "optimizer_eps",
                          "burnin", "horizon", "model", "training_arrays_sha256"):
                if old[field] != new[field]:
                    setting_differences.append(dict(scenario_id=key[1], source_training_horizon=key[2],
                                                    repeat=key[3], field=field, old=old[field], new=new[field]))
    designs = [(spec.scenario_id, 200) for spec in scenario_specs()]
    designs += [("exp_ar_pos08_fixed6", horizon) for horizon in (50, 100, 500)]
    windows, comparisons = [], []
    for sid, training_h in designs:
        for mode in MODES:
            for horizon in HORIZONS:
                key = (sid, training_h, mode, horizon)
                row = dict(scenario_id=sid, source_training_horizon=training_h, mode=mode, horizon=horizon,
                           scope="primary" if training_h == 200 else "horizon_extension",
                           diagonal=training_h == horizon, status="incomplete", planned_repeats_per_run=3)
                averages = {}
                try:
                    for label in ("old", "new"):
                        items = groups[label].get(key, [])
                        row[label + "_n_repeats"] = len(items)
                        averages[label] = _average(items)
                        if averages[label] is not None:
                            costs = averages[label]["repeat_costs_per_period"]
                            row[label + "_mean_cost_per_period"] = float(np.mean(costs))
                            row[label + "_generation_sd"] = float(np.std(costs, ddof=1))
                    if not all(averages.values()):
                        windows.append(row)
                        continue
                    if sid not in matched_tests:
                        raise ValueError("Test dataset pairing is not verified")
                    _paired_arrays(averages["new"], averages["old"])
                    requests = [("new_vs_old", averages["new"], averages["old"])]
                    for family in REFERENCES:
                        old_ref, new_ref = (refs[label].get((*key, family)) for label in ("old", "new"))
                        if old_ref is None or new_ref is None:
                            raise ValueError("Missing matched reference: " + family)
                        _paired_arrays(old_ref, new_ref)
                        hashes = [baseline_hashes[label].get((sid, training_h, family)) for label in ("old", "new")]
                        if (not hashes[0] or hashes[0] != hashes[1]
                                or old_ref["row"].get("record_sha256") != hashes[0]
                                or new_ref["row"].get("record_sha256") != hashes[1]
                                or not np.array_equal(old_ref["arrays"]["total_cost"], new_ref["arrays"]["total_cost"])):
                            raise ValueError("Baseline source or path costs changed: " + family)
                        row[family + "_mean_cost_per_period"] = float(old_ref["arrays"]["total_cost"].mean()/horizon)
                        requests.extend((label + "_vs_" + family, averages[label], old_ref) for label in ("old", "new"))
                    pending = []
                    for name, candidate, reference in requests:
                        _paired_arrays(candidate, reference)
                        stats = paired_statistics(candidate["arrays"]["total_cost"]/horizon,
                                                  reference["arrays"]["total_cost"]/horizon,
                                                  seed=SEED, n_bootstrap=n_bootstrap)
                        row[name + "_improvement_pct"] = stats["improvement_pct"]
                        row[name + "_improvement_pct_ci"] = stats["improvement_pct_ci"]
                        pending.append(dict(scenario_id=sid, source_training_horizon=training_h,
                            mode=mode, horizon=horizon, comparison=name, candidate_repeats=3,
                            reference_repeats=3 if name == "new_vs_old" else 1,
                            dataset_arrays_sha256=candidate["row"]["dataset_arrays_sha256"], **stats))
                    comparisons.extend(pending)
                    row["status"] = "complete"
                except (KeyError, TypeError, ValueError) as exc:
                    row.update(status="pairing_error", error=str(exc))
                    issues.append(dict(scenario_id=sid, source_training_horizon=training_h,
                                       mode=mode, horizon=horizon, error=str(exc)))
                windows.append(row)
    aggregates = []
    for training_h in HORIZONS:
        for mode in MODES:
            for horizon in HORIZONS:
                expected = [row for row in windows if row["source_training_horizon"] == training_h
                            and row["mode"] == mode and row["horizon"] == horizon]
                complete = [row for row in expected if row["status"] == "complete"]
                aggregate = dict(source_training_horizon=training_h, mode=mode, horizon=horizon,
                    complete_scenarios=len(complete), planned_scenarios=len(expected),
                    aggregation="equally weighted scenarios; descriptive; available complete scenarios only")
                for metric in ("old_mean_cost_per_period", "new_mean_cost_per_period", "new_vs_old_improvement_pct",
                               *(label+"_vs_"+family+"_improvement_pct" for family in REFERENCES for label in ("old", "new"))):
                    values = [row[metric] for row in complete]
                    aggregate[metric + "_mean"] = float(np.mean(values)) if values else None
                    aggregate[metric + "_median"] = float(np.median(values)) if values else None
                aggregates.append(aggregate)
    main = [row for row in windows if row["source_training_horizon"] == row["horizon"] == 200 and row["mode"] == "steady"]
    complete = (all(row["status"] == "complete" for row in windows)
                and all(row["status"] == "matched" for row in pairs)
                and len(baseline_pairing) == 63 and all(row["status"] == "matched" for row in baseline_pairing)
                and all(sum(row["run"] == label and row["stage"] == "final_training_selected"
                            and row["count_status"] == "counted" for row in parameters) == 27 for label in ("old", "new"))
                and not issues)
    result = dict(schema_version=1, created_utc=datetime.now(timezone.utc).isoformat(),
        status="complete" if complete else "incomplete", old_run=str(old_root), new_run=str(new_root),
        exploratory_disclosure=EXPLORATORY, units="mean cost per period", bootstrap_replicates=n_bootstrap,
        bootstrap_seed=SEED, planned_comparison_windows=len(windows),
        complete_comparison_windows=sum(row["status"] == "complete" for row in windows),
        pairing_unit="whole demand/lead-time trajectory; average three generated policies within each path first",
        interval_scope="path sampling only; excludes generation variation; no multiplicity adjustment",
        selection="all three planned independent draws in each run; no test-best selection; repeat IDs are not paired model seeds",
        parameter_count_definition="distinct OPT_PARAM-comment-annotated scalar assignments, not the four policy inputs",
        parameter_response_denominator="each saved final model response, including candidate attempts; not unique candidates; pending/unparseable excluded from numerical distribution",
        dataset_pairing=pairs, baseline_pairing=baseline_pairing, search_setting_differences=setting_differences,
        search_settings=definitions, parameter_distributions=distributions, main=main, windows=windows,
        aggregates=aggregates, comparisons=comparisons, issues=issues)
    output.mkdir(parents=True, exist_ok=True)
    _write_json(output / "parameter_comparison.json", result)
    for filename, rows in (("main_h200_steady.csv", main), ("all_windows.csv", windows),
                           ("paired_comparisons.csv", comparisons), ("scenario_aggregates.csv", aggregates),
                           ("parameter_counts.csv", parameters), ("parameter_distributions.csv", distributions),
                           ("dataset_pairing.csv", pairs), ("baseline_pairing.csv", baseline_pairing)):
        _write_csv(output / filename, rows)
    _write_markdown(output, result)
    return result


def _fmt(value, digits=3):
    return "—" if value is None else f"{value:.{digits}f}"


def _write_markdown(output, result):
    lines = ["# 参数数量上限消融：旧轮与新轮", "",
        f"状态：**{result['status']}**；完成 {result['complete_comparison_windows']}/{result['planned_comparison_windows']} 个比较窗口。", "",
        EXPLORATORY, "", f"- 旧轮：{result['old_run']}", f"- 新轮：{result['new_run']}", "",
        "成本单位均为每期平均成本，越低越好。每轮分别在每条路径上平均全部三次独立生成，再按同一需求与交货期路径配对；不选测试最佳策略，也不把两轮 r1 当作配对的模型随机种子。", "",
        "95% 区间重采样整条路径，仅反映需求路径抽样误差，不包含策略生成变异，也未作多重比较校正。生成间样本 SD 单列。改善率为 100×(对照−候选)/对照，正值有利于候选。", "",
        "## 主比较：训练 H=200，评价 H=200，B=500", "",
        "三次未齐时不显示部分重复的替代均值。PIL 改善列按“旧轮 → 新轮”显示，使用两轮哈希及逐路径成本一致的对照。", "",
        "| 场景 | 旧/新重复数 | 旧成本 ± 生成 SD | 新成本 ± 生成 SD | 新比旧改善% [95% CI] | Conditional PIL 成本 | 改善% 旧→新 | Adaptive PIL 成本 | 改善% 旧→新 |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for row in result["main"]:
        costs = [f"{_fmt(row.get(label+'_mean_cost_per_period'))} ± {_fmt(row.get(label+'_generation_sd'))}" for label in ("old", "new")]
        ci = row.get("new_vs_old_improvement_pct_ci")
        improvement = (_fmt(row.get("new_vs_old_improvement_pct")) +
                       (f" [{_fmt(ci[0])}, {_fmt(ci[1])}]" if ci else ""))
        cells = [row["scenario_id"], f"{row.get('old_n_repeats',0)}/3 · {row.get('new_n_repeats',0)}/3", *costs, improvement]
        for family in REFERENCES:
            cells += [_fmt(row.get(family+"_mean_cost_per_period")),
                      " → ".join(_fmt(row.get(label+"_vs_"+family+"_improvement_pct")) for label in ("old", "new"))]
        lines.append("| " + " | ".join(cells) + " |")
    lines += ["", "## 全时域与冷暖启动", "",
        "[全部窗口](all_windows.csv) 包括固定 H=200 策略在 H=50/100/200/500 的评价，以及 AR+ 的 H=50/100/500 单独重训扩展；source_training_horizon 明确区分两者。cold_start 为 B=0，steady 为 B=500。", "",
        "[跨场景汇总](scenario_aggregates.csv) 同时报等权均值、中位数和完成/计划场景数，属于描述指标；未完成时只汇总完整配对场景，不外推至全部场景。[全部配对区间](paired_comparisons.csv) 使用相同路径。", "",
        "## OPT_PARAM 数量", "",
        "只数 OPT_PARAM 注释绑定的独立标量赋值；四个策略输入是观测状态，不算可优化参数。原始生成阶段按每个已保存的模型最终回复计数（包括同一候选的第二次请求），最终阶段每条链仅统计按训练目标选定的 policy.py。种子策略不混入模型生成分母。无法解析与未返回的回复单列，不能当作零参数。", "",
        "| 轮次 | 范围 | 阶段 | 可计数/已观察 | 未返回 | 无法解析 | 最小/中位/最大 | >4 | 数量分布 |",
        "|---|---|---|---:|---:|---:|---:|---:|---|"]
    for row in result["parameter_distributions"]:
        lines.append(f"| {row['run']} | {row['scope']} | {row['stage']} | {row['counted']}/{row['observed']} | {row['pending']} | {row['unparseable']} | {_fmt(row['minimum'],0)}/{_fmt(row['median'],1)}/{_fmt(row['maximum'],0)} | {row['above_four']} | {json.dumps(row['histogram'], ensure_ascii=False)} |")
    lines += ["", "完整明细：[参数计数](parameter_counts.csv)、[数据配对](dataset_pairing.csv)、[基线记录配对](baseline_pairing.csv)、[机器可读报告](parameter_comparison.json)。", "",
        f"除参数上限外，已观察搜索设置差异 {len(result['search_setting_differences'])} 条；读取或配对问题 {len(result['issues'])} 条，详见 JSON。不完整或不一致的窗口不会生成比较区间。", ""]
    (output / "report.md").write_text("\n".join(lines))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--previous-run", "--old-run", dest="old_run", type=Path, required=True)
    parser.add_argument("--run-dir", "--new-run", dest="new_run", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path,
                        help="Dedicated comparison folder; default NEW/parameter_comparison")
    parser.add_argument("--bootstrap", type=int, default=5000)
    parser.add_argument("--require-complete", action="store_true",
                        help="Write the diagnostic report, then exit 2 if comparison is incomplete")
    args = parser.parse_args()
    answer = compare_runs(args.old_run, args.new_run, args.output_dir or args.new_run / "parameter_comparison",
                          n_bootstrap=args.bootstrap)
    print(json.dumps({name: answer[name] for name in
                      ("status", "complete_comparison_windows", "planned_comparison_windows")}, ensure_ascii=False))
    if args.require_complete and answer["status"] != "complete":
        sys.exit(2)
