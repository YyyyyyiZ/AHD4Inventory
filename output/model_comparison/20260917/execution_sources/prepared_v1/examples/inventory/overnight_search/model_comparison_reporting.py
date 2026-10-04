"""Offline, generation-level reporting for the prospective backbone comparison.

Reads only the explicitly supplied run directory. It never imports the policy
runner, generates demand tapes, executes policies, or makes network requests.
``--self-test`` uses a disposable, wholly synthetic fixture.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
import hashlib
import json
import math
from pathlib import Path
import re
import statistics
import tempfile

from scipy.stats import t


REPEATS = (1, 2, 3)
SCENARIO_COUNT = 20
TRANSFER_COUNT = 8
MARGIN_PCT = 2.0


def _number(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError("数值必须是 JSON number")
    result = float(value)
    if not math.isfinite(result):
        raise ValueError("数值必须有限")
    return result


def _dump(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
                    encoding="utf-8")


def _read(root, relative, expected_type, issues, fingerprints):
    path = root / relative
    try:
        data = path.read_bytes()
        fingerprints[relative] = hashlib.sha256(data).hexdigest()
        value = json.loads(data)
        if not isinstance(value, expected_type):
            raise ValueError(f"顶层应为 {expected_type.__name__}")
        return value
    except (OSError, ValueError, UnicodeError) as error:
        issues.append({"input": relative, "error": str(error)})
        return None


def _three(values):
    """Never average just the successful generations."""
    available = sum(value is not None for value in values)
    full = len(values) == 3 and available == 3
    return {"repeat_values": values, "available_repeats": available,
            "complete": full,
            "mean": statistics.mean(values) if full else None,
            "sample_sd": statistics.stdev(values) if full else None}


def _gap(candidate, control):
    return 100.0 * (candidate / control - 1.0) if control > 0 else None


def _paired_statistics(values, allow_screen):
    result = _three(values)
    result.update(unit="percentage_points", confidence_level=0.95, sidedness="upper_one_sided",
                  degrees_of_freedom=2, noninferiority_margin_pct=MARGIN_PCT,
                  upper_95_pct=None, exploratory_noninferiority_screen_pass=None)
    if result["complete"]:
        result["upper_95_pct"] = result["mean"] + float(t.ppf(.95, 2)) * result["sample_sd"] / math.sqrt(3)
        if allow_screen:
            result["exploratory_noninferiority_screen_pass"] = result["upper_95_pct"] < MARGIN_PCT
    return result


def _cell(file_record, name):
    if file_record is None or file_record.get("valid") is not True:
        return None
    return file_record.get("accepted_results", {}).get(name)


def _load_results(root, relative, scenario_names, issues, fingerprints):
    source = _read(root, relative, dict, issues, fingerprints)
    if source is None:
        return None
    record = {"valid": source.get("valid") is True, "accepted_results": {}}
    if not record["valid"]:
        issues.append({"input": relative, "error": "valid 不是 true；失败结果不参与成功者筛选",
                       "error_type": source.get("error_type")})
        return record
    rows = source.get("results")
    if not isinstance(rows, dict):
        issues.append({"input": relative, "error": "缺少 results 对象"})
        return record
    extras = sorted(set(rows) - set(scenario_names))
    if extras:
        issues.append({"input": relative, "error": "存在清单外场景", "scenarios": extras})
    for name in scenario_names:
        try:
            row = rows[name]
            if not isinstance(row, dict):
                raise ValueError("场景记录不是对象")
            cost = _number(row["cost"])
            if cost < 0:
                raise ValueError("成本不能为负")
            paths = row["path_costs"]
            if not isinstance(paths, list) or not paths:
                raise ValueError("path_costs 必须是非空数组")
            paths = [_number(value) for value in paths]
            if any(value < 0 for value in paths):
                raise ValueError("路径成本不能为负")
            if not math.isclose(cost, statistics.mean(paths), rel_tol=1e-9, abs_tol=1e-8):
                raise ValueError("cost 与 path_costs 的均值不一致")
            if not isinstance(row["theta"], list):
                raise ValueError("theta 必须是数组")
            theta = [_number(value) for value in row["theta"]]
            record["accepted_results"][name] = {"cost": cost, "path_count": len(paths), "theta": theta}
        except (KeyError, TypeError, ValueError) as error:
            issues.append({"input": relative, "scenario": name, "error": str(error)})
    return record


def _validate_catalog(models_file, scenarios_file, issues):
    models, scenarios = [], []
    seen = set()
    if models_file is not None:
        entries = models_file.get("models")
        if not isinstance(entries, list):
            issues.append({"input": "models.json", "error": "缺少 models 数组"})
        else:
            for entry in entries:
                try:
                    if not isinstance(entry, dict):
                        raise ValueError("模型条目不是对象")
                    model = {key: entry[key] for key in ("slug", "label", "model", "role")}
                    if not all(isinstance(value, str) and value for value in model.values()):
                        raise ValueError("模型元数据必须是非空字符串")
                    if not re.fullmatch(r"[A-Za-z0-9_-]+", model["slug"]):
                        raise ValueError("slug 含非法路径字符")
                    if model["slug"] in seen:
                        raise ValueError("模型 slug 重复")
                    seen.add(model["slug"])
                    models.append(model)
                except (KeyError, TypeError, ValueError) as error:
                    issues.append({"input": "models.json", "error": str(error)})
    if sum(model["role"] == "control" for model in models) != 1:
        issues.append({"input": "models.json", "error": "必须恰有一个 role=control 的同流程 Sol 对照"})
    if len(models) < 2:
        issues.append({"input": "models.json", "error": "至少需要一个候选模型和一个对照模型"})
    seen = set()
    for spec in scenarios_file or []:
        try:
            if not isinstance(spec, dict):
                raise ValueError("场景定义不是对象")
            if not isinstance(spec["name"], str) or not spec["name"] or spec["name"] in seen:
                raise ValueError("场景名称为空或重复")
            for key in ("m", "L", "cv", "f"):
                _number(spec[key])
            seen.add(spec["name"])
            scenarios.append(spec)
        except (KeyError, TypeError, ValueError) as error:
            issues.append({"input": "scenarios.json", "error": str(error)})
    expected = {(m, 2, cv, f) for m in (3, 4, 5, 7, 8) for cv in (1.5, 2.) for f in (0., .5)}
    observed = {(s["m"], s["L"], s["cv"], s["f"]) for s in scenarios}
    if len(scenarios) != SCENARIO_COUNT or observed != expected:
        issues.append({"input": "scenarios.json", "error": "必须覆盖 m=3/4/5/7/8、L=2、CV=1.5/2、f=0/0.5 的20场景网格"})
    return models, scenarios


def _api_accounting(source, issues):
    if source is None:
        return None
    result = {}
    for key in ("limit_usd", "actual_cost_usd", "estimated_upper_usd", "held_upper_usd",
                "committed_upper_usd", "remaining_usd", "requests"):
        try:
            value = _number(source[key])
            if value < 0:
                raise ValueError("金额或请求数不能为负")
            result[key] = value
        except (KeyError, TypeError, ValueError) as error:
            issues.append({"input": "api_summary.json", "field": key, "error": str(error)})
    result["paused"] = bool(source.get("paused_reason"))
    if all(key in result for key in ("actual_cost_usd", "estimated_upper_usd", "held_upper_usd", "committed_upper_usd")):
        expected = sum(result[key] for key in ("actual_cost_usd", "estimated_upper_usd", "held_upper_usd"))
        if not math.isclose(expected, result["committed_upper_usd"], abs_tol=1e-8, rel_tol=1e-9):
            issues.append({"input": "api_summary.json", "error": "已确认、估计及预留费用之和与 committed 不一致"})
    return result


def _repeat_average(names, candidate_files, reference_files, *, reduction=False):
    values = []
    for repeat in REPEATS:
        differences = []
        for name in names:
            candidate = _cell(candidate_files[repeat], name)
            reference = _cell(reference_files[repeat], name)
            difference = _gap(candidate["cost"], reference["cost"]) if candidate and reference else None
            if difference is None:
                break
            differences.append(-difference if reduction else difference)
        values.append(statistics.mean(differences) if names and len(differences) == len(names) else None)
    return values


def _ledger_amount(value):
    """Ledger amounts are Decimal strings; do not interpret absent fees as zero."""
    if isinstance(value, bool) or not isinstance(value, (str, int, float)):
        raise ValueError("账本金额缺失或类型无效")
    try:
        result = Decimal(str(value))
    except InvalidOperation as error:
        raise ValueError("账本金额无效") from error
    if not result.is_finite() or result < 0:
        raise ValueError("账本金额必须非负且有限")
    return result


def _model_api_diagnostics(root, models, warnings, fingerprints):
    relative = "api_budget/budget.json"
    ledger = _read(root, relative, dict, warnings, fingerprints)
    fees = {model["slug"]: {"status": "unknown", "requests": None,
            "actual_cost_usd": None, "estimated_upper_usd": None, "held_upper_usd": None,
            "requests_by_state": None} for model in models}
    result = {"source": relative, "scope": "exact request.metadata.slug match",
              "unattributed_requests": None, "models": fees}
    if ledger is None:
        return result
    requests = ledger.get("requests")
    if ledger.get("currency") != "USD" or not isinstance(requests, dict):
        warnings.append({"input": relative, "error": "可选账本必须声明USD并包含requests对象"})
        return result
    grouped = {slug: [] for slug in fees}
    unattributed = 0
    for row in requests.values():
        metadata = row.get("metadata") if isinstance(row, dict) else None
        slug = metadata.get("slug") if isinstance(metadata, dict) else None
        if not isinstance(slug, str) or slug not in grouped:
            unattributed += 1
        else:
            grouped[slug].append(row)
    result["unattributed_requests"] = unattributed
    if unattributed:
        warnings.append({"input": relative, "error": f"{unattributed}条请求无可匹配的metadata.slug；不擅自分摊给任何模型"})
    for slug, rows in grouped.items():
        totals = {key: Decimal(0) for key in ("actual_cost_usd", "estimated_upper_usd", "held_upper_usd")}
        states = {}
        valid = True
        for row in rows:
            try:
                state = row["state"]
                if state not in ("actual", "pricing_upper_estimate", "pending", "unknown_charge"):
                    raise ValueError("未知账本结算状态")
                states[state] = states.get(state, 0) + 1
                output_key, source_key = (("actual_cost_usd", "actual_cost_usd") if state == "actual" else
                    ("estimated_upper_usd", "estimated_upper_usd") if state == "pricing_upper_estimate" else
                    ("held_upper_usd", "reserved_usd"))
                totals[output_key] += _ledger_amount(row.get(source_key))
            except (KeyError, TypeError, ValueError) as error:
                valid = False
                warnings.append({"input": relative, "model": slug, "error": str(error)})
        fees[slug] = {"status": "known_attributed" if valid else "invalid_amounts",
                     "requests": len(rows), "requests_by_state": states,
                     **{key: float(value) if valid else None for key, value in totals.items()}}
    return result


def _selection_diagnostics(root, slug, repeat, warnings, fingerprints):
    relative = f"runs/{slug}/r{repeat}/freeze.json"
    frozen = _read(root, relative, dict, warnings, fingerprints)
    result = {"repeat": repeat, "source": relative, "origin": None, "category": "unknown"}
    if frozen is None:
        return result
    origin = frozen.get("origin")
    if frozen.get("slug") != slug or frozen.get("repeat") != repeat or not isinstance(origin, str):
        warnings.append({"input": relative, "error": "freeze的slug/repeat/origin无法确认"})
        return result
    result["origin"] = origin
    if origin.startswith("common:") and len(origin) > len("common:"):
        result["category"] = "common_seed"
    elif re.fullmatch(re.escape(f"{slug}/r{repeat}/") + r"\d+", origin):
        result["category"] = "generated"
    else:
        warnings.append({"input": relative, "error": "来源既非common:初始策略，也非本模型本重复的候选编号"})
    return result


def _candidate_diagnostics(root, slug, repeat, expected, warnings, fingerprints):
    folder = root / f"runs/{slug}/r{repeat}/candidates"
    if expected is not None:
        paths = [folder / f"{index:02d}" / "record.json" for index in range(expected)]
        extras = set(folder.glob("*/record.json")) - set(paths)
        if extras:
            warnings.append({"input": str(folder.relative_to(root)), "error": "存在协议候选编号之外的记录，不计入计划候选总数"})
    else:
        paths = sorted(folder.glob("*/record.json"))
    valid_count, invalid_count, unreadable = 0, 0, 0
    for path in paths:
        relative = str(path.relative_to(root))
        row = _read(root, relative, dict, warnings, fingerprints)
        if row is None:
            unreadable += 1
            continue
        if row.get("valid") is True:
            valid_count += 1
        elif row.get("valid") is False:
            invalid_count += 1
        else:
            unreadable += 1
            warnings.append({"input": relative, "error": "候选valid不是布尔值，状态未知"})
    full = expected is not None and valid_count + invalid_count == expected
    return {"repeat": repeat, "expected_records": expected, "observed_record_paths": sum(path.is_file() for path in paths),
            "known_valid_count": valid_count, "known_invalid_count": invalid_count,
            "unknown_count": unreadable if expected is not None else None,
            "invalid_count": invalid_count if full else None,
            "complete": full, "status": "known" if full else "unknown_or_partial"}


def optional_diagnostics(root, models, protocol, fingerprints):
    """Optional diagnostics have a separate warning list and never gate results."""
    warnings = []
    api = _model_api_diagnostics(root, models, warnings, fingerprints)
    expected = protocol.get("generated_candidates_per_repetition") if protocol else None
    if type(expected) is not int or expected < 0:
        expected = None
        warnings.append({"input": "protocol.json", "error": "未提供有效的generated_candidates_per_repetition，无法确认候选总数/无效总数"})
    records = {}
    for model in models:
        slug = model["slug"]
        selections = [_selection_diagnostics(root, slug, repeat, warnings, fingerprints) for repeat in REPEATS]
        candidates = [_candidate_diagnostics(root, slug, repeat, expected, warnings, fingerprints) for repeat in REPEATS]
        known_common = sum(row["category"] == "common_seed" for row in selections)
        known_generated = sum(row["category"] == "generated" for row in selections)
        unknown = 3 - known_common - known_generated
        all_candidates = all(row["complete"] for row in candidates)
        records[slug] = {"api": api["models"][slug], "selected_origins": selections,
            "selected_origin_counts": {"common_seed": known_common if not unknown else None,
                "generated": known_generated if not unknown else None, "unknown": unknown,
                "known_common_seed": known_common, "known_generated": known_generated},
            "generated_candidates": {"repeats": candidates, "complete": all_candidates,
                "expected_count": 3 * expected if expected is not None else None,
                "invalid_count": sum(row["known_invalid_count"] for row in candidates) if all_candidates else None,
                "known_invalid_count": sum(row["known_invalid_count"] for row in candidates),
                "known_valid_count": sum(row["known_valid_count"] for row in candidates),
                "unknown_count": sum(row["unknown_count"] for row in candidates) if expected is not None else None}}
    return {"optional": True, "affects_core_completeness": False,
            "api_ledger_source": api["source"], "api_attribution_scope": api["scope"],
            "api_unattributed_requests": api["unattributed_requests"], "models": records,
            "warnings": warnings,
            "interpretation": "Matching performance may come from selecting and tuning a common seed; it does not establish that a cheaper LLM evolved an equally good new structure. A generated origin alone also does not establish structural novelty."}


def build_report(run):
    """Read one run, then overwrite only its two derived report artifacts."""
    root = Path(run).expanduser().resolve()
    if not root.is_dir():
        raise ValueError(f"运行目录不存在：{root}")
    issues, fingerprints = [], {}
    protocol = _read(root, "protocol.json", dict, issues, fingerprints)
    model_source = _read(root, "models.json", dict, issues, fingerprints)
    scenario_source = _read(root, "scenarios.json", list, issues, fingerprints)
    api_source = _read(root, "api_summary.json", dict, issues, fingerprints)
    models, scenarios = _validate_catalog(model_source, scenario_source, issues)
    accounting = _api_accounting(api_source, issues)
    names = [spec["name"] for spec in scenarios]
    transfer = [spec["name"] for spec in scenarios if spec["m"] in (4, 8)]
    control = next((model for model in models if model["role"] == "control"), None)
    files = {}
    for model in models:
        slug = model["slug"]
        files[slug] = {kind: {} for kind in ("tuned", "raw")}
        for repeat in REPEATS:
            for kind, filename in (("tuned", "test.json"), ("raw", "test_raw.json")):
                relative = f"runs/{slug}/r{repeat}/{filename}"
                files[slug][kind][repeat] = _load_results(root, relative, names, issues, fingerprints)
    # Zero denominators must not silently reduce the planned scenario family.
    for model in models:
        for repeat in REPEATS:
            kinds = ("raw", "tuned") if model["role"] == "control" else ("raw",)
            for kind in kinds:
                for name in names:
                    record = _cell(files[model["slug"]][kind][repeat], name)
                    if record and record["cost"] <= 0:
                        issues.append({"input": f"runs/{model['slug']}/r{repeat}/{kind}",
                                       "scenario": name, "error": "百分比指标分母成本不为正"})
    complete = not issues
    grid_valid = not any(issue["input"] == "scenarios.json" for issue in issues)
    rows = []
    for spec in scenarios:
        name = spec["name"]
        row = {"scenario": spec, "split": "transfer" if spec["m"] in (4, 8) else "discovery", "models": {}}
        for model in models:
            slug = model["slug"]
            costs, raw_costs, relative, reductions, counts = [], [], [], [], []
            for repeat in REPEATS:
                tuned = _cell(files[slug]["tuned"][repeat], name)
                raw = _cell(files[slug]["raw"][repeat], name)
                reference = _cell(files[control["slug"]]["tuned"][repeat], name) if control else None
                costs.append(tuned["cost"] if tuned else None)
                raw_costs.append(raw["cost"] if raw else None)
                relative.append(_gap(tuned["cost"], reference["cost"]) if tuned and reference else None)
                gap = _gap(tuned["cost"], raw["cost"]) if tuned and raw else None
                reductions.append(-gap if gap is not None else None)
                counts.append({"tuned": tuned["path_count"] if tuned else None,
                               "raw": raw["path_count"] if raw else None})
            row["models"][slug] = {"cost": _three(costs), "raw_cost": _three(raw_costs),
                "relative_to_control_pct": _three(relative),
                "optimizer_reduction_pct": _three(reductions), "path_counts": counts}
        rows.append(row)
    comparisons, ablations = {}, {}
    for model in models:
        slug = model["slug"]
        groups = {"all_20": names, "transfer_8": transfer}
        if control and model["role"] != "control":
            comparisons[slug] = {}
            for group, selected in groups.items():
                values = (_repeat_average(selected, files[slug]["tuned"], files[control["slug"]]["tuned"])
                          if grid_valid else [None] * 3)
                comparisons[slug][group] = {"scenario_count": len(selected),
                    **_paired_statistics(values, allow_screen=complete)}
        ablations[slug] = {group: {"scenario_count": len(selected), **_three(_repeat_average(
            selected, files[slug]["tuned"], files[slug]["raw"], reduction=True) if grid_valid else [None] * 3)}
            for group, selected in groups.items()}
    diagnostics = optional_diagnostics(root, models, protocol, fingerprints)
    summary = {"schema_version": 2, "generated_utc": datetime.now(timezone.utc).isoformat(),
        "run_directory": str(root), "complete": complete,
        "status": "complete_exploratory" if complete else "incomplete",
        "models": models, "control_slug": control["slug"] if control else None,
        "planned_scenarios": SCENARIO_COUNT, "observed_scenarios": len(names),
        "planned_transfer_scenarios": TRANSFER_COUNT, "observed_transfer_scenarios": len(transfer),
        "planned_repeats": 3, "repeat_pairing": "same_repeat_index_r1_r2_r3",
        "metric": "Per repeat: equal-scenario mean of 100*(candidate_cost/control_cost-1); then mean of three repeats",
        "positive_means": "candidate_cost_is_higher",
        "screening": "Exploratory only: paired-generation Student-t one-sided 95% upper bound < 2%; n=3, df=2; no multiplicity correction",
        "optimizer_ablation_scope": "Fixed already-selected structure, tuned versus its literal default theta; conditional ablation only",
        "missing_policy": "Do not omit failed or missing repeats, or replace them with successful repeats",
        "scenario_results": rows, "comparisons": comparisons, "optimizer_ablation": ablations,
        "api_accounting": accounting, "run_diagnostics": diagnostics,
        "issues": issues, "input_sha256": fingerprints,
        "protocol_present": protocol is not None, "winner_conclusion": None}
    markdown = render_markdown(summary)
    _dump(root / "report_summary.json", summary)
    (root / "report.md").write_text(markdown, encoding="utf-8")
    return summary


def _fmt(value, digits=3):
    return "缺失/无效" if value is None else f"{value:.{digits}f}"


def _escape(value):
    return str(value).replace("|", "\\|").replace("\n", " ").replace("\r", " ")


def _diagnostic_fmt(value, digits=0):
    return "未知" if value is None else f"{value:.{digits}f}"


def render_markdown(summary):
    complete = summary["complete"]
    models = summary["models"]
    status = "数据完整；仅作探索性比较" if complete else "INCOMPLETE：缺失或无效输入，暂不形成胜出或非劣结论"
    lines = ["# 易腐库存模型比较", "", f"状态：**{status}**。", "",
        f"计划20场景、每模型3次独立生成重复；读入{summary['observed_scenarios']}场景，其中m=4/8迁移场景{summary['observed_transfer_scenarios']}个。", "",
        "所有模型均运行同一 evolve + optimize 流程；对照由 models.json 的 role=control 指定为 Sol。模型优劣不能从API价格预先推出。", "",
        "主指标：同编号r1/r2/r3配对，每次先在20个场景上等权平均 `100 × (候选成本 / Sol成本 − 1)`，再对3次重复取均值。正数表示候选成本更高。迁移指标对m=4/8的8场景单独计算。", "",
        "均值±SD中的SD为3次生成重复的样本标准差。单侧95%上界为 `均值 + t(0.95, df=2) × SD / √3`；上界低于2%仅通过探索性非劣筛查，不构成正式非劣证明。该t区间依赖重复间独立及差值近似正态的假设，n=3很不稳定，未校正多模型、多分组比较；模拟路径不作为独立生成重复。", "",
        "缺失或失败重复均保留缺口，不计算仅成功重复的均值，不用其他重复替补。整体不完整时不标记任何筛查通过。", "",
        "成本接近可能来自最终选用了同一个共享初始策略，再由optimizer调参；不能仅凭打平就断言便宜LLM演化出了同样好的新结构。下方另列所选策略来源，生成候选标签本身也不证明结构新颖。", "",
        "| 模型 | API model ID | 角色 |", "|---|---|---|"]
    for model in models:
        lines.append(f"| {_escape(model['label'])} | `{_escape(model['model'])}` | {_escape(model['role'])} |")
    lines += ["", "## 相对同流程 Sol 的生成重复比较", "",
        "| 模型 | 场景组 | r1 / r2 / r3 (%) | 均值 ± SD (%) | 单侧95%上界 (%) | 2%探索性筛查 |",
        "|---|---|---|---|---|---|"]
    for model in models:
        for group, stats in summary["comparisons"].get(model["slug"], {}).items():
            screen = stats["exploratory_noninferiority_screen_pass"]
            label = "通过（探索性）" if screen is True else "未通过（不能据此断言更差）" if screen is False else "不判定"
            values = " / ".join(_fmt(value) for value in stats["repeat_values"])
            lines.append(f"| {_escape(model['label'])} | {group} | {values} | {_fmt(stats['mean'])} ± {_fmt(stats['sample_sd'])} | {_fmt(stats['upper_95_pct'])} | {label} |")
    lines += ["", "## 全场景成本", "", "每一行使用全部3重复；相对Sol列是三个配对百分比的均值，不是两组平均成本之比。", "",
        "| 场景 | 分组 | 模型 | r1 / r2 / r3成本 | 平均成本 ± SD | 相对Sol (%) |",
        "|---|---|---|---|---|---|"]
    for row in summary["scenario_results"]:
        for model in models:
            data = row["models"][model["slug"]]
            costs = " / ".join(_fmt(value) for value in data["cost"]["repeat_values"])
            lines.append(f"| {_escape(row['scenario']['name'])} | {row['split']} | {_escape(model['label'])} | {costs} | {_fmt(data['cost']['mean'])} ± {_fmt(data['cost']['sample_sd'])} | {_fmt(data['relative_to_control_pct']['mean'])} |")
    lines += ["", "## Optimizer 条件消融", "",
        "raw表示同一个已经选定的策略结构采用字面默认参数。逐重复计算各场景 `100 × (raw成本 − tuned成本) / raw成本` 后等权平均；正数表示调参降本。由于结构的生成和选择已经用到optimizer，该条件消融不能证明整个优化器流程的独立因果贡献，也不等同于重新运行完全不调参的结构搜索。", "",
        "| 模型 | 场景组 | r1 / r2 / r3降本 (%) | 均值 ± SD (%) |", "|---|---|---|---|"]
    for model in models:
        for group, stats in summary["optimizer_ablation"][model["slug"]].items():
            values = " / ".join(_fmt(value) for value in stats["repeat_values"])
            lines.append(f"| {_escape(model['label'])} | {group} | {values} | {_fmt(stats['mean'])} ± {_fmt(stats['sample_sd'])} |")
    diagnostics = summary["run_diagnostics"]
    lines += ["", "## 最终策略来源与候选失败诊断（可选）", "",
        "common:表示所有backbone均可使用的共享初始策略，不计作本轮LLM发现。generated表示本模型本次重复产生的候选来源。无效候选按record.json中valid=false计数；缺失记录或未知状态不会冒充零次失败。", "",
        "| 模型 | 重复 | freeze所选来源 | 来源分类 |", "|---|---|---|---|"]
    for model in models:
        for selected in diagnostics["models"][model["slug"]]["selected_origins"]:
            category = {"common_seed": "共享初始策略", "generated": "模型生成候选", "unknown": "未知"}[selected["category"]]
            lines.append(f"| {_escape(model['label'])} | r{selected['repeat']} | {_escape(selected['origin']) if selected['origin'] else '未知'} | {category} |")
    lines += ["", "| 模型 | 共享初始策略次数 / 生成策略次数 / 未知次数 | 计划生成候选总数 | 无效候选总数 |",
              "|---|---|---|---|"]
    for model in models:
        diagnostic = diagnostics["models"][model["slug"]]
        origins = diagnostic["selected_origin_counts"]
        counts = (f"{origins['common_seed']} / {origins['generated']} / 0" if not origins["unknown"] else
            f"总数未知（已确认共享{origins['known_common_seed']}、生成{origins['known_generated']}；未知{origins['unknown']}）")
        candidates = diagnostic["generated_candidates"]
        invalid = (str(candidates["invalid_count"]) if candidates["complete"] else
            f"未知（已确认无效{candidates['known_invalid_count']}；未确认{_diagnostic_fmt(candidates['unknown_count'])}）")
        lines.append(f"| {_escape(model['label'])} | {counts} | {_diagnostic_fmt(candidates['expected_count'])} | {invalid} |")
    if diagnostics["warnings"]:
        lines += ["", f"可选诊断有{len(diagnostics['warnings'])}条缺失/无效/归属提示，详见report_summary.json的run_diagnostics.warnings。这些缺口不改变核心性能结果的完整性状态。"]
    lines += ["", "## API费用", ""]
    fees = summary["api_accounting"]
    if fees:
        lines += [f"已确认费用 ${_fmt(fees.get('actual_cost_usd'), 7)}；按价格表估计上限 ${_fmt(fees.get('estimated_upper_usd'), 7)}；仍预留上限 ${_fmt(fees.get('held_upper_usd'), 7)}。",
            f"三者合计保守上限 ${_fmt(fees.get('committed_upper_usd'), 7)}；预算 ${_fmt(fees.get('limit_usd'), 2)}；请求数 {_fmt(fees.get('requests'), 0)}。估计和预留不冒充已确认实扣；API费用不含本地CPU计算。"]
    else:
        lines.append("费用摘要缺失/无效，不能确认支出。")
    lines += ["", "逐模型费用只按api_budget/budget.json的request.metadata.slug精确归属，不按客户端名称猜测。pending和unknown_charge保留原预留上限；缺少可选账本时显示未知。",
        f"未归属请求数：{_diagnostic_fmt(diagnostics['api_unattributed_requests'])}。未归属请求不分摊给任何模型，逐模型之和可能与总账不同。", "",
        "| 模型 | 已确认USD | 估计上限USD | 仍预留上限USD | 已归属请求数 |", "|---|---|---|---|---|"]
    for model in models:
        fees = diagnostics["models"][model["slug"]]["api"]
        lines.append(f"| {_escape(model['label'])} | {_diagnostic_fmt(fees['actual_cost_usd'], 7)} | {_diagnostic_fmt(fees['estimated_upper_usd'], 7)} | {_diagnostic_fmt(fees['held_upper_usd'], 7)} | {_diagnostic_fmt(fees['requests'])} |")
    if summary["issues"]:
        lines += ["", "## 缺失或无效输入", ""]
        for issue in summary["issues"]:
            detail = f" / {issue['scenario']}" if issue.get("scenario") else ""
            lines.append(f"- `{_escape(issue['input'])}`{_escape(detail)}：{_escape(issue['error'])}")
    lines += ["", "本报告只读取已保存结果，不重跑策略、不重新选择结构或参数。全部原始结果保持不变；report_summary.json保存逐重复统计、缺口和输入SHA-256。", ""]
    return "\n".join(lines)


def self_test():
    """Fabricated file contract, aggregation and missing-data checks only."""
    with tempfile.TemporaryDirectory(prefix="model-comparison-report-fixture-") as temporary:
        root = Path(temporary)
        specs = [{"name": f"perish_m{m}_L2_cv{cv:g}_f{f:g}", "m": m, "L": 2, "cv": cv, "f": f}
                 for m in (3, 4, 5, 7, 8) for cv in (1.5, 2.) for f in (0., .5)]
        _dump(root / "protocol.json", {"synthetic_fixture": True})
        _dump(root / "scenarios.json", specs)
        _dump(root / "models.json", {"models": [
            {"slug": "sol", "label": "Sol", "model": "synthetic-sol", "role": "control"},
            {"slug": "candidate", "label": "Candidate", "model": "synthetic-candidate", "role": "candidate"}]})
        _dump(root / "api_summary.json", {"limit_usd": 10, "actual_cost_usd": 1,
            "estimated_upper_usd": .2, "held_upper_usd": .3, "committed_upper_usd": 1.5,
            "remaining_usd": 8.5, "requests": 6, "paused_reason": None})
        for slug in ("sol", "candidate"):
            for repeat in REPEATS:
                folder = root / "runs" / slug / f"r{repeat}"
                folder.mkdir(parents=True)
                for raw, filename in ((False, "test.json"), (True, "test_raw.json")):
                    rows = {}
                    for index, spec in enumerate(specs):
                        base = 50. + index * 7. + repeat
                        gap = (0., 1., 2.)[repeat - 1] if index % 2 else (-1., 0., 1.)[repeat - 1]
                        cost = base * (1 + gap / 100.) if slug == "candidate" else base
                        cost *= 1.25 if raw else 1.
                        rows[spec["name"]] = {"cost": cost, "path_costs": [cost - 1, cost + 1], "theta": [0.]}
                    _dump(folder / filename, {"valid": True, "results": rows})
        result = build_report(root)
        assert result["complete"] and len(result["scenario_results"]) == 20
        stats = result["comparisons"]["candidate"]["all_20"]
        assert all(math.isclose(x, y, abs_tol=1e-11) for x, y in zip(stats["repeat_values"], (-.5, .5, 1.5)))
        assert math.isclose(stats["mean"], .5, abs_tol=1e-11)
        assert math.isclose(stats["sample_sd"], 1., abs_tol=1e-11)
        assert math.isclose(stats["upper_95_pct"], .5 + float(t.ppf(.95, 2)) / math.sqrt(3), abs_tol=1e-11)
        assert stats["exploratory_noninferiority_screen_pass"] is False
        assert result["comparisons"]["candidate"]["transfer_8"]["scenario_count"] == 8
        assert math.isclose(result["optimizer_ablation"]["candidate"]["all_20"]["mean"], 20.)
        assert json.loads((root / "report_summary.json").read_text())["complete"]
        assert "n=3" in (root / "report.md").read_text()
        assert result["run_diagnostics"]["models"]["candidate"]["api"]["actual_cost_usd"] is None
        assert result["run_diagnostics"]["models"]["candidate"]["selected_origin_counts"]["common_seed"] is None
        assert result["run_diagnostics"]["models"]["candidate"]["generated_candidates"]["invalid_count"] is None
        _dump(root / "protocol.json", {"synthetic_fixture": True, "generated_candidates_per_repetition": 2})
        for slug in ("sol", "candidate"):
            for repeat in REPEATS:
                folder = root / "runs" / slug / f"r{repeat}"
                origin = "common:flexible_age_weights" if repeat == 1 else f"{slug}/r{repeat}/00"
                _dump(folder / "freeze.json", {"slug": slug, "repeat": repeat, "origin": origin})
                for index in (0, 1):
                    candidate_folder = folder / "candidates" / f"{index:02d}"
                    candidate_folder.mkdir(parents=True)
                    _dump(candidate_folder / "record.json", {"index": index, "origin": f"{slug}/r{repeat}/{index:02d}", "valid": index == 0})
        (root / "api_budget").mkdir()
        ledger_path = root / "api_budget/budget.json"
        ledger = {"currency": "USD", "requests": {
            "a": {"state": "actual", "actual_cost_usd": "0.6", "metadata": {"slug": "candidate"}},
            "b": {"state": "pricing_upper_estimate", "estimated_upper_usd": "0.2", "metadata": {"slug": "candidate"}},
            "c": {"state": "unknown_charge", "reserved_usd": "0.1", "metadata": {"slug": "candidate"}},
            "d": {"state": "actual", "actual_cost_usd": "0.4", "metadata": {"slug": "sol"}},
            "e": {"state": "pending", "reserved_usd": "0.2", "metadata": {"slug": "sol"}},
            "f": {"state": "actual", "actual_cost_usd": "0", "metadata": {}}}}
        _dump(ledger_path, ledger)
        result = build_report(root)
        assert result["complete"]
        diagnostic = result["run_diagnostics"]["models"]["candidate"]
        assert diagnostic["api"]["actual_cost_usd"] == .6 and diagnostic["api"]["estimated_upper_usd"] == .2
        assert diagnostic["api"]["held_upper_usd"] == .1 and diagnostic["api"]["requests"] == 3
        assert result["run_diagnostics"]["api_unattributed_requests"] == 1
        assert diagnostic["selected_origin_counts"]["common_seed"] == 1
        assert diagnostic["selected_origin_counts"]["generated"] == 2
        assert diagnostic["generated_candidates"]["invalid_count"] == 3
        optional_record = root / "runs/candidate/r3/candidates/01/record.json"
        optional_saved = optional_record.read_text()
        optional_record.unlink()
        result = build_report(root)
        diagnostic = result["run_diagnostics"]["models"]["candidate"]
        assert result["complete"] and diagnostic["generated_candidates"]["invalid_count"] is None
        assert diagnostic["generated_candidates"]["known_invalid_count"] == 2
        assert diagnostic["generated_candidates"]["unknown_count"] == 1
        optional_record.write_text(optional_saved)
        ledger["requests"]["a"]["actual_cost_usd"] = None
        _dump(ledger_path, ledger)
        result = build_report(root)
        assert result["complete"] and result["run_diagnostics"]["models"]["candidate"]["api"]["actual_cost_usd"] is None
        ledger["requests"]["a"]["actual_cost_usd"] = "0.6"
        _dump(ledger_path, ledger)
        changed = root / "runs/candidate/r2/test.json"
        saved = changed.read_text()
        changed.unlink()
        result = build_report(root)
        stats = result["comparisons"]["candidate"]["all_20"]
        assert not result["complete"] and stats["mean"] is None and stats["repeat_values"][1] is None
        assert stats["exploratory_noninferiority_screen_pass"] is None
        changed.write_text(saved)
        row = json.loads(saved)
        row["valid"] = False
        _dump(changed, row)
        assert build_report(root)["comparisons"]["candidate"]["all_20"]["mean"] is None
        changed.write_text(saved)
        raw = root / "runs/candidate/r3/test_raw.json"
        raw_saved = raw.read_text()
        raw.unlink()
        result = build_report(root)
        assert not result["complete"] and result["comparisons"]["candidate"]["all_20"]["exploratory_noninferiority_screen_pass"] is None
        assert result["optimizer_ablation"]["candidate"]["all_20"]["mean"] is None
        raw.write_text(raw_saved)
        row = json.loads(saved)
        row["results"][specs[0]["name"]]["path_costs"][0] += 10.
        _dump(changed, row)
        assert not build_report(root)["complete"]
        changed.write_text(saved)
        _dump(root / "scenarios.json", specs[:-1])
        result = build_report(root)
        assert not result["complete"] and result["comparisons"]["candidate"]["all_20"]["mean"] is None
        _dump(root / "scenarios.json", specs)
        control = root / "runs/sol/r1/test.json"
        row = json.loads(control.read_text())
        row["results"][specs[0]["name"]].update(cost=0., path_costs=[0., 0.])
        _dump(control, row)
        result = build_report(root)
        assert not result["complete"] and result["comparisons"]["candidate"]["all_20"]["mean"] is None
        return {"ok": True, "fixture": "temporary synthetic only", "checks": [
            "20/8 scenario coverage", "three-generation paired equal-scenario percentages",
            "sample SD and one-sided t upper bound", "conditional optimizer reduction",
            "JSON/Markdown output", "missing repeat", "failed repeat", "missing raw",
            "path mean mismatch", "incomplete scenario catalog", "zero denominator",
            "optional missing diagnostics remain unknown without gating results",
            "per-model ledger actual/estimated/held amounts and slug attribution",
            "freeze common/generated counts", "candidate invalid/missing distinction",
            "invalid optional ledger amount remains unknown"]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--run", type=Path, help="Existing model comparison run directory")
    mode.add_argument("--self-test", action="store_true", help="Use only a temporary synthetic fixture")
    args = parser.parse_args()
    if args.self_test:
        print(json.dumps(self_test(), ensure_ascii=False))
    else:
        result = build_report(args.run)
        print(json.dumps({"complete": result["complete"], "issues": len(result["issues"]),
                          "report": str(args.run / "report.md")}, ensure_ascii=False))


if __name__ == "__main__":
    main()
