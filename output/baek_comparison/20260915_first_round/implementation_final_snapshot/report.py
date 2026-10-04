"""Read frozen scores and write an auditable Chinese report and CSV tables.

No model requests, policy execution, tuning, or test-based policy selection occur
here. Importing this module has no filesystem side effects. SVG figures contain
observed between-draw ranges, not confidence intervals or optimality claims.
"""

from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import hashlib
from html import escape
import json
import math
from pathlib import Path
import re

import numpy as np

from .analysis import paired_statistics
from .runner import DEFAULT_RUN, recover_spend


BATCHES = ("existing_test", "fresh_test", "integer_test", "long_run")
BATCH_LABELS = {"existing_test": "现有基准测试集", "fresh_test": "独立新需求测试集",
                "integer_test": "统一整数动作检查", "long_run": "长期运行检查"}
SOURCE_LABELS = {"baek_generated": "Baek", "historical_training_selected": "历史 AHD",
                 "training_tuned_classical": "经典基线"}
POLICY_FAILURES = {"invalid", "timeout", "invalid_final_output", "tool_limit_repeated"}


def _read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def _fmt(value, digits=2):
    return f"{value:.{digits}f}" if _number(value) else "—"


def _cell(value):
    return str(value).replace("|", "\\|").replace("\n", " ")


def _link(path, label=None):
    path = Path(path).resolve()
    return f"[{label or path.name}](<{path}>)"


def _cross_scenario_summary_line(group, batch_name, method, reference):
    first = [row["first_draw_improvement_pct"] for row in group if _number(row["first_draw_improvement_pct"])]
    means = [row["mean_improvement_pct"] for row in group if _number(row["mean_improvement_pct"])]
    label = "训练选定经典基线" if reference == "classical_train_selected" else "历史 AHD（可用场景）"
    return (f"| {BATCH_LABELS[batch_name]} | {method} | {label} | {len(means)}/{len(group)} | "
            f"{_fmt(float(np.mean(first)) if first else None)}% (n={len(first)}) | "
            f"{_fmt(float(np.median(first)) if first else None)}% | "
            f"{_fmt(float(np.mean(means)) if means else None)}% | "
            f"{_fmt(float(np.median(means)) if means else None)}% | "
            f"{sum(row['n_valid'] for row in group)}/{sum(row['n_planned'] for row in group)} |")


def _csv(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = list(dict.fromkeys(key for row in rows for key in row)) or ["status"]
    with path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: json.dumps(value, ensure_ascii=False) if isinstance(value, (list, dict)) else value
                             for key, value in row.items()})


def _family(scenario_id):
    return "normal" if scenario_id.startswith("normal_") else scenario_id.split("_", 1)[0]


def _expected_specs(manifest, scenario_id, method):
    level = method.removeprefix("Baek-")
    return [spec for spec in manifest.get("sessions", [])
            if spec.get("level") == level and spec.get("family") == _family(scenario_id)
            and (level == "L2" or spec.get("scenario_id") == scenario_id)]


def _artifact_id(record, path):
    metadata = record.get("metadata", {})
    return metadata.get("artifact_id") or metadata.get("session_id") or record.get("session_id") or path.stem


def _batch_status(record, batch):
    global_status = record.get("status", "ok")
    if global_status != "ok":
        return global_status
    if batch is None:
        return "not_scored"
    return batch.get("status", "ok")


def _check_pair(candidate, reference):
    """Check shared-path provenance before interpreting a paired difference."""
    c, r = candidate.get("per_path", {}), reference.get("per_path", {})
    cv, rv = c.get("total_cost"), r.get("total_cost")
    if cv is None or rv is None or len(cv) != len(rv):
        raise ValueError("Missing or different number of per-path costs")
    cd, rd = c.get("demand_units"), r.get("demand_units")
    if cd is None or rd is None or not np.array_equal(np.asarray(cd), np.asarray(rd)):
        raise ValueError("Demand totals or path order differ")
    ch, rh = candidate.get("demand_sha256"), reference.get("demand_sha256")
    if ch and rh and ch != rh:
        raise ValueError("Demand-path SHA-256 differs")
    cs, rs = candidate.get("summary", {}), reference.get("summary", {})
    for field in ("periods_scored", "periods_simulated", "mode", "integer_orders"):
        if cs.get(field) != rs.get(field):
            raise ValueError(f"Scoring protocol differs: {field}")
    return "matching_demand_sha256" if ch and rh else "shared_scenario_batches_and_matching_path_demand_totals"


def _read_generation_events(log_path):
    """Read opaque journal items; verify any claim that reopens a session."""
    if not log_path.exists():
        return []
    raw = log_path.read_bytes()
    events, offset = [], 0
    for line in raw.splitlines(keepends=True):
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            offset += len(line)
            continue
        if event.get("event") == "request_reconciled":
            from .harness import validate_request_reconciliation
            validate_request_reconciliation(event, raw[:offset])
        events.append(event)
        offset += len(line)
    return events


def _transport_recoveries(events):
    recoveries = []
    for index, event in enumerate(events):
        if event.get("event") != "request_reconciled" or event.get("reopens_session") is not True:
            continue
        later = events[index + 1:]
        resumed = next((item for item in later if item.get("event") == "session_resumed"), None)
        fields = ("reconciliation_id", "request_index", "charge_resolution", "actual_cost_usd",
                  "retained_cost_upper_usd", "reserved_cost_retained_usd", "request_payload_sha256",
                  "context_sha256", "failure_event_sha256", "terminal_event_sha256", "log_prefix_sha256",
                  "accounting_evidence", "reason")
        recoveries.append({**{key: event.get(key) for key in fields},
                           "event_index": index,
                           "session_resumed_logged": resumed is not None,
                           "continued_response_logged": any(item.get("event") == "response" for item in later),
                           "completed_tool_calls_at_resume": resumed.get("completed_tool_calls") if resumed else None,
                           "python_seconds_at_resume": resumed.get("productive_python_seconds") if resumed else None})
    return recoveries


def _generation_rows(run_dir, manifest):
    rows = []
    expected = {spec["session_id"]: spec for spec in manifest.get("sessions", [])}
    folders = {path.name: path for path in (run_dir / "sessions").glob("*") if path.is_dir()}
    for base_id, folder in list(folders.items()):
        for retry_folder in folder.glob("retry_*"):
            if retry_folder.is_dir():
                folders[f"{base_id}/{retry_folder.name}"] = retry_folder
    for session_id in sorted(set(expected) | set(folders)):
        folder = folders.get(session_id, run_dir / "sessions" / session_id)
        base_session_id = session_id.split("/", 1)[0]
        result_path = folder / "result.json"
        result = _read(result_path) if result_path.exists() else {}
        spec = {**expected.get(base_session_id, {}), **result}
        log_path = folder / "events.jsonl"
        events = _read_generation_events(log_path)
        recoveries = _transport_recoveries(events)
        responses = [event["response"] for event in events
                     if event.get("event") == "response" and isinstance(event.get("response"), dict)]
        known_cost = sum(response.get("usage", {}).get("cost", 0) for response in responses
                         if _number(response.get("usage", {}).get("cost")))
        sums = {field: sum(response.get("usage", {}).get(field, 0) or 0 for response in responses)
                for field in ("input_tokens", "output_tokens", "total_tokens")}
        reasoning = sum((r.get("usage", {}).get("output_tokens_details") or {}).get("reasoning_tokens", 0) or 0
                        for r in responses)
        cached = sum((r.get("usage", {}).get("input_tokens_details") or {}).get("cached_tokens", 0) or 0
                     for r in responses)
        if not responses and not events:
            known_cost = spec.get("cost_usd", 0.0)
            sums.update({key: spec.get("usage", {}).get(key, 0) for key in sums})
        known_cost += sum(item["actual_cost_usd"] for item in recoveries
                          if item["charge_resolution"] == "authoritative_cost" and _number(item["actual_cost_usd"]))
        status = spec.get("status", "running_or_interrupted" if events else "pending")
        tool_calls, python_seconds = spec.get("tool_calls"), spec.get("python_seconds")
        requests = spec.get("requests", len(responses))
        if recoveries:
            last_recovery = recoveries[-1]
            later_terminals = [item for item in events[last_recovery["event_index"] + 1:]
                               if item.get("event") == "session_end"]
            if later_terminals:
                status = later_terminals[-1].get("result", {}).get("status", status)
            else:
                status = ("running_after_transport_recovery" if last_recovery["session_resumed_logged"]
                          else "transport_recovery_ready")
            tool_events = [item for item in events if item.get("event") == "tool_result"]
            tool_calls = sum(not str(item.get("result", {}).get("error", "")).startswith("Python tool budget exhausted")
                             for item in tool_events)
            python_seconds = sum(item.get("result", {}).get("elapsed_seconds", 0.0) for item in tool_events)
            requests = sum(item.get("event") == "request" for item in events)
        code_path = folder / "policy.py"
        digest = hashlib.sha256(code_path.read_bytes()).hexdigest() if code_path.exists() else None
        timestamps = [e["timestamp"] for e in events if _number(e.get("timestamp"))]
        rows.append({
            "session_id": session_id, "base_session_id": base_session_id,
            "level": spec.get("level"), "family": spec.get("family"),
            "repeat": spec.get("repeat"), "attempt": spec.get("attempt", 2 if "/retry_" in session_id else 1),
            "status": status,
            "known_charged_usd": known_cost, **sums, "reasoning_tokens_included_in_output": reasoning,
            "cached_input_tokens": cached, "tool_calls": tool_calls,
            "python_seconds": python_seconds, "requests": requests,
            "transport_recovery_count": len(recoveries), "transport_recoveries": recoveries,
            "conservative_recovery_bound_usd": sum(item["retained_cost_upper_usd"] for item in recoveries
                if item["charge_resolution"] == "conservative_bound" and _number(item["retained_cost_upper_usd"])),
            "logged_elapsed_seconds": max(timestamps) - min(timestamps) if timestamps else None,
            "actual_models": spec.get("actual_models", []),
            "code_path": str(code_path) if code_path.exists() else None,
            "code_sha256": spec.get("code_sha256"),
            "code_hash_matches": digest == spec["code_sha256"] if digest and spec.get("code_sha256") else None,
            "result_path": str(result_path) if result_path.exists() else None,
            "error": spec.get("error"),
            "invalidity_evidence": spec.get("invalidity_evidence", []),
        })
    return rows


def _transport_recovery_lines(run_dir, generation):
    records = [(row, recovery) for row in generation for recovery in row.get("transport_recoveries", [])]
    if not records:
        return []
    retained = sum(item["retained_cost_upper_usd"] for _, item in records
                   if item["charge_resolution"] == "conservative_bound" and _number(item["retained_cost_upper_usd"]))
    lines = ["", "### 传输故障后的原会话恢复", "",
             f"日志中有 {len(records)} 条通过原日志、请求、上下文及证据哈希核验的恢复记录。"
             f"其中未知费用的保守上界合计 **${retained:.6f}**，继续占用全局预算；上界不当作已确认实际费用。"
             "恢复限定在原会话、原提示和原上下文内，保留已完成工具结果及累计调用次数、执行时长，工具预算不重置。"
             "这些传输恢复本身不增加独立生成次数，也不属于无效策略补跑或按测试成绩重抽。", "",
             "丢失的响应可能已在服务端执行；保留费用上界不代表原请求未执行或已确认零收费。"
             "从已保存上下文继续也不能称为找回丢失的原响应。下表区分恢复核准与已经开始续接，"
             "策略是否完成仍以上方会话状态为准；恢复记录不证明 TLS 故障根因已修复。", "",
             "| 会话 | 原传输请求（从 1 开始） | 恢复状态 | 原请求实际费用 | 保留上界 | 核账记录 |",
             "|---|---:|---|---:|---:|---|"]
    for row, item in records:
        state = "已记录从原上下文开始续接" if item["session_resumed_logged"] else "已核准；尚未记录实际续接"
        actual = (f"${item['actual_cost_usd']:.6f}" if item["charge_resolution"] == "authoritative_cost"
                  and _number(item["actual_cost_usd"]) else "未知")
        upper = item["retained_cost_upper_usd"] if item["charge_resolution"] == "conservative_bound" else 0.0
        evidence = [entry.get("path") for entry in (item.get("accounting_evidence") or []) if entry.get("path")]
        links = "；".join(_link(path, "证据") for path in evidence) or "见会话日志"
        request_index = item.get("request_index")
        request_number = request_index + 1 if isinstance(request_index, int) else "—"
        lines.append(f"| {row['session_id']} | {request_number} | {state} | {actual} | ${_fmt(upper, 6)} | {links} |")
    snapshots = sorted(run_dir.glob("transport_recovery*/key_usage_snapshot*.json"))
    if snapshots:
        lag_observed = False
        for path in snapshots:
            snapshot = _read(path)
            logged = snapshot.get("logged_confirmed_after_usd", snapshot.get("after", {}).get("confirmed_cost_usd"))
            accounted = snapshot.get("key_usage", {}).get("usage_monthly")
            lag_observed |= _number(logged) and _number(accounted) and logged > accounted + 1e-9
        note = "账户汇总快照只反映各查询时已经入账的费用。"
        if lag_observed:
            note += "核对中已观察到账户汇总落后于成功响应日志，因此一次金额对齐不能证明故障请求永久零收费。"
        else:
            note += "查询时未观察到额外费用，不能据此证明故障请求未执行或永久零收费。"
        lines += ["", note + " " + "；".join(_link(path, path.name) for path in snapshots)]
    return lines


def _draw_selection(run_dir, manifest, scenario_ids):
    """Select one attempt globally per draw using ONLY synthetic validation.

    A Level-2 attempt must pass its entire required scenario grid. Its successful
    cells cannot be combined with another attempt. Test scores never enter this
    selection. Missing or unverifiable validation leaves a draw unqualified.
    """
    manifest_hash = hashlib.sha256((run_dir / "manifest.json").read_bytes()).hexdigest()
    validations = []
    for path in sorted((run_dir / "validation").rglob("*.json")):
        validations.append((path, _read(path)))
    selections = {}
    for spec in manifest.get("sessions", []):
        parent_id = spec["session_id"]
        required = ([spec["scenario_id"]] if spec["level"] == "L1" else
                    [sid for sid in scenario_ids if _family(sid) == spec["family"]])
        attempts = []
        for attempt in (1, 2):
            folder = run_dir / "sessions" / parent_id
            if attempt == 2:
                folder /= "retry_1"
            result_path = folder / "result.json"
            artifact_id = parent_id if attempt == 1 else parent_id + "_retry_1"
            if not result_path.exists():
                attempts.append({"attempt": attempt, "artifact_id": artifact_id,
                                 "status": "running_or_interrupted" if (folder / "events.jsonl").exists() else "not_run",
                                 "validated_scenarios": 0, "required_scenarios": len(required)})
                continue
            result_bytes = result_path.read_bytes()
            result = json.loads(result_bytes)
            if result.get("status") in POLICY_FAILURES:
                attempts.append({"attempt": attempt, "artifact_id": artifact_id, "status": "invalid",
                                 "generation_status": result["status"], "validated_scenarios": 0,
                                 "required_scenarios": len(required)})
                continue
            if result.get("status") != "completed":
                attempts.append({"attempt": attempt, "artifact_id": artifact_id,
                                 "status": result.get("status", "incomplete_generation"),
                                 "validated_scenarios": 0, "required_scenarios": len(required)})
                continue
            code_hash = result.get("code_sha256")
            policy_path = folder / "policy.py"
            if (not code_hash or not policy_path.exists()
                    or hashlib.sha256(policy_path.read_bytes()).hexdigest() != code_hash):
                attempts.append({"attempt": attempt, "artifact_id": artifact_id, "status": "hash_mismatch",
                                 "validated_scenarios": 0, "required_scenarios": len(required)})
                continue
            result_hash = hashlib.sha256(result_bytes).hexdigest()
            verified, invalid, review = {}, [], []
            for path, validation in validations:
                meta = validation.get("metadata", {})
                if meta.get("session_id") != parent_id or meta.get("attempt", 1) != attempt:
                    continue
                sid = validation.get("scenario_id")
                if sid not in required:
                    continue
                if (validation.get("evaluation_kind") != "synthetic_contract_validation"
                        or validation.get("manifest_sha256") != manifest_hash
                        or validation.get("code_sha256") != code_hash
                        or meta.get("result_sha256") != result_hash):
                    review.append({"scenario_id": sid, "path": str(path), "status": "validation_hash_or_provenance_mismatch"})
                    continue
                status = validation.get("status")
                verified[sid] = status
                if status == "timeout":
                    limits = validation.get("evaluation_limits", {})
                    error = validation.get("raw_result", {}).get("error", {})
                    if (limits.get("setup_timeout_seconds") != 600 or limits.get("action_timeout_seconds") != 1
                            or error.get("stage") not in {"setup", "policy_action"}):
                        review.append({"scenario_id": sid, "path": str(path),
                                       "status": "timeout_not_proven_under_approved_policy_limits"})
                        continue
                if status in POLICY_FAILURES:
                    invalid.append({"scenario_id": sid, "path": str(path), "status": status})
                elif status != "ok":
                    review.append({"scenario_id": sid, "path": str(path), "status": status})
            state = ("invalid" if invalid else "review_required" if review else
                     "qualified" if required and len(verified) == len(required) else "validation_incomplete")
            attempts.append({"attempt": attempt, "artifact_id": artifact_id, "status": state,
                             "code_sha256": code_hash, "validated_scenarios": len(verified),
                             "required_scenarios": len(required), "invalidity": invalid, "review": review})
        qualified = [row for row in attempts if row["status"] == "qualified"]
        chosen = qualified[0] if qualified else None
        state = "selected" if chosen else "failed" if all(row["status"] == "invalid" for row in attempts) else (
            "invalid_first_attempt_retry_not_run" if attempts[0]["status"] == "invalid" and attempts[1]["status"] == "not_run"
            else "pending_qualification")
        selections[parent_id] = {"session_id": parent_id, "level": spec["level"], "family": spec["family"],
                                 "repeat": spec["repeat"], "required_scenario_ids": required,
                                 "status": state, "selected_attempt": chosen["attempt"] if chosen else None,
                                 "selected_artifact_id": chosen["artifact_id"] if chosen else None,
                                 "first_attempt_invalid": attempts[0]["status"] == "invalid",
                                 "attempts": attempts,
                                 "selection_rule": "earliest_attempt_passing_entire_required_synthetic_grid; no_test_scores"}
    return selections


def _svg_chart(path, rows, batch_name, reference="classical_train_selected"):
    """Dependency-free scientific summary: mean and min/max across valid draws."""
    selected = [r for r in rows if r["batch"] == batch_name and r["reference"] == reference
                and r["n_valid"] and _number(r.get("mean_improvement_pct"))]
    if not selected:
        return False
    scenarios = sorted({row["scenario_id"] for row in selected})
    values = [float(row[key]) for row in selected for key in ("min_improvement_pct", "max_improvement_pct")]
    lo, hi = min(-1.0, *values), max(1.0, *values)
    span = hi - lo
    lo, hi = lo - 0.08 * span, hi + 0.08 * span
    width, left, right, top, line = 1220, 295, 1020, 110, 37
    height = top + len(scenarios) * line + 95
    x = lambda v: left + (float(v) - lo) / (hi - lo) * (right - left)
    reference_title = ("historical AHD (mixed models and search budgets)" if reference == "historical_AHD"
                       else "train-selected classical baseline")
    elements = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
                '<rect width="100%" height="100%" fill="#fff"/>',
                '<style>text{font-family:Arial,sans-serif;fill:#1f2937;font-size:13px}.small{font-size:11px}.title{font-size:22px;font-weight:bold}</style>',
                f'<text x="25" y="34" class="title">{escape(batch_name)}: improvement over {reference_title}</text>',
                '<text x="25" y="59">Points: mean across valid independent draws; whiskers: observed minimum to maximum across draws.</text>',
                '<text x="25" y="80">Positive values indicate lower cost. Whiskers are generation spread, not confidence intervals. Counts show paired / planned.</text>']
    for value in np.linspace(lo, hi, 7):
        px = x(value)
        elements += [f'<line x1="{px:.2f}" x2="{px:.2f}" y1="{top-8}" y2="{height-60}" stroke="#e5e7eb"/>',
                     f'<text x="{px:.2f}" y="{height-35}" text-anchor="middle">{value:.1f}%</text>']
    elements.append(f'<line x1="{x(0):.2f}" x2="{x(0):.2f}" y1="{top-8}" y2="{height-60}" stroke="#374151" stroke-width="1.5"/>')
    for i, scenario in enumerate(scenarios):
        y = top + i * line + 12
        if i % 2 == 0:
            elements.append(f'<rect x="15" y="{y-14}" width="1170" height="35" fill="#f8fafc" opacity="0.7"/>')
        elements.append(f'<text x="25" y="{y+5}">{escape(scenario)}</text>')
        for method, color, offset in (("Baek-L1", "#b45309", -5), ("Baek-L2", "#0369a1", 6)):
            matches = [r for r in selected if r["scenario_id"] == scenario and r["method"] == method]
            if not matches:
                continue
            row = matches[0]
            yy = y + offset
            elements += [f'<line x1="{x(row["min_improvement_pct"]):.2f}" x2="{x(row["max_improvement_pct"]):.2f}" y1="{yy}" y2="{yy}" stroke="{color}" stroke-width="2"/>',
                         f'<circle cx="{x(row["mean_improvement_pct"]):.2f}" cy="{yy}" r="4" fill="{color}"/>',
                         f'<text x="1035" y="{yy+4}" class="small">{method} {row["mean_improvement_pct"]:+.2f}% ({row["n_paired"]}/{row["n_planned"]})</text>']
    elements.append('</svg>')
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(elements), encoding="utf-8")
    return True


def generate_report(run_dir: Path | str, *, n_bootstrap=5000) -> dict:
    """Build report.md and tables from already-frozen fit and score records."""
    run_dir = Path(run_dir).resolve()
    manifest = _read(run_dir / "manifest.json")
    generation = _generation_rows(run_dir, manifest)
    warnings = []
    classical_choice, refs = {}, []
    for path in sorted((run_dir / "baselines").glob("*.json")):
        record = _read(path)
        fits = record["fits"]
        valid = {name: fit for name, fit in fits.items() if _number(fit.get("train_mean_cost"))}
        if not valid:
            warnings.append(f"{path.stem}: 没有可核验的经典基线训练分数。")
            continue
        selected = min(valid, key=lambda name: (valid[name]["train_mean_cost"], name))
        classical_choice[path.stem] = selected
        refs.append({"scenario_id": path.stem, "reference": "classical_train_selected", "method": selected,
                     "recorded_train_mean_cost": valid[selected]["train_mean_cost"], "params": valid[selected]["params"],
                     "selection_rule": "lowest_train_mean_cost_only", "source_path": str(path),
                     "upper_edge_unresolved": valid[selected].get("search", {}).get("unresolved_upper_edge")})
    records = []
    for path in sorted((run_dir / "scores").glob("*/*.json")):
        record = _read(path)
        records.append((path, record))
    registered_scenarios = {name.removesuffix("_train.json") for name in manifest.get("data_sha256", {})
                            if name.endswith("_train.json")}
    registered_scenarios.update(spec["scenario_id"] for spec in manifest.get("sessions", []) if spec.get("scenario_id"))
    scenario_ids = sorted(registered_scenarios | set(classical_choice) | {record["scenario_id"] for _, record in records})
    selections = _draw_selection(run_dir, manifest, scenario_ids)
    indexed = {(record["scenario_id"], record.get("method")): (path, record) for path, record in records
               if record.get("source") != "baek_generated"}
    historical = [(path, record) for path, record in records if record.get("source") == "historical_training_selected"]
    for path, record in historical:
        meta = record.get("metadata", {})
        audit = record.get("training_audit", record.get("raw_result", {}).get("training_audit", {}))
        refs.append({"scenario_id": record["scenario_id"], "reference": "historical_AHD", "method": record.get("method"),
                     "model": meta.get("model"), "run_name": meta.get("run_name"),
                     "recorded_train_mean_cost": meta.get("recorded_train_objective"),
                     "selection_rule": meta.get("selection_rule"),
                     "code_sha256": record.get("code_sha256", meta.get("candidate_code_sha256")),
                     "source_path": meta.get("population_path"), "score_path": str(path),
                     "training_audit": audit, "status": record.get("status")})
        if audit and audit.get("matches_within_tolerance") is False:
            warnings.append(f"{record['scenario_id']}: 历史 AHD 的统一训练重评分与记录值不一致；请查看 references.csv。")
    per_draw, pairs = [], []
    for path, record in records:
        source, method = record.get("source", "unknown"), record.get("method", path.stem)
        meta, scenario = record.get("metadata", {}), record["scenario_id"]
        artifact_id = _artifact_id(record, path)
        selection = selections.get(meta.get("parent_session_id") or meta.get("session_id"), {})
        analysis_role = ("main" if selection.get("selected_artifact_id") == artifact_id else
                         "diagnostic_unselected" if selection.get("status") == "selected" else "pending_qualification")
        raw = record.get("raw_result", {})
        setup = record.get("setup_seconds", raw.get("setup_seconds"))
        for batch_name in BATCHES:
            batch = record.get("batches", {}).get(batch_name)
            # Long-run checks are intentionally restricted to the three core cases.
            if batch is None and batch_name == "long_run":
                continue
            status = _batch_status(record, batch)
            summary = (batch or {}).get("summary", {}) if status == "ok" else {}
            row = {"scenario_id": scenario, "batch": batch_name, "method": method, "source": source,
                   "artifact_id": artifact_id, "repeat": meta.get("repeat"), "attempt": meta.get("attempt", 1),
                   "analysis_role": analysis_role if source == "baek_generated" else "reference",
                   "status": status, "mean_total_cost": summary.get("mean_total_cost"),
                   "mean_cost_per_period": summary.get("mean_cost_per_period"),
                   "mean_holding_cost": summary.get("mean_holding_cost"),
                   "mean_lost_sales_cost": summary.get("mean_lost_sales_cost"),
                   "fill_rate": summary.get("demand_weighted_service_level"),
                   "n_paths": summary.get("n_paths"), "periods_scored": summary.get("periods_scored"),
                   "setup_seconds": setup, "setup_exceeded_30_seconds": setup > 30 if _number(setup) else None,
                   "mean_action_seconds": (batch or {}).get("mean_action_seconds"),
                   "action_timing_status": "measured" if _number((batch or {}).get("mean_action_seconds"))
                   else "not_measured_by_vectorized_classical_scorer" if source == "training_tuned_classical" else "unavailable",
                   "code_sha256": record.get("code_sha256"), "demand_sha256": (batch or {}).get("demand_sha256"),
                   "score_path": str(path), "error": record.get("error", raw.get("error"))}
            per_draw.append(row)
            if source != "baek_generated" or status != "ok":
                continue
            comparisons = [("classical_train_selected", classical_choice.get(scenario)),
                           ("historical_AHD", "AHD-historical")]
            for reference_label, reference_method in comparisons:
                other = indexed.get((scenario, reference_method))
                if not other:
                    continue
                ref_path, reference = other
                ref_batch = reference.get("batches", {}).get(batch_name)
                if _batch_status(reference, ref_batch) != "ok":
                    continue
                try:
                    provenance = _check_pair(batch, ref_batch)
                    stats = paired_statistics(batch["per_path"]["total_cost"], ref_batch["per_path"]["total_cost"],
                                              seed=manifest.get("seed_paired_bootstrap", 2026091504),
                                              n_bootstrap=n_bootstrap)
                    pair = {"scenario_id": scenario, "batch": batch_name, "method": method,
                            "artifact_id": artifact_id, "repeat": meta.get("repeat"), "attempt": meta.get("attempt", 1),
                            "analysis_role": analysis_role,
                            "reference": reference_label, "reference_method": reference_method,
                            **stats, "pairing_provenance": provenance,
                            "candidate_score_path": str(path), "reference_score_path": str(ref_path)}
                    improvement = stats["improvement_pct"]
                    pair["within_0_1pct_or_better"] = improvement >= -0.1 if _number(improvement) else None
                    pair["within_1pct_or_better"] = improvement >= -1.0 if _number(improvement) else None
                    pairs.append(pair)
                except ValueError as exc:
                    warnings.append(f"禁止配对：{scenario}/{artifact_id}/{batch_name}/{reference_label}：{exc}")
    summaries = []
    generation_index = {row["session_id"]: row for row in generation}
    core_scenarios = {spec.get("scenario_id") for spec in manifest.get("sessions", []) if spec.get("level") == "L1"}
    # Retain planned draws with no executable artifact or no score record. An
    # infrastructure interruption is pending, not an invalid generated policy.
    for scenario in scenario_ids:
        for method in ("Baek-L1", "Baek-L2"):
            for spec in _expected_specs(manifest, scenario, method):
                if any(row["scenario_id"] == scenario and row["method"] == method and row["repeat"] == spec["repeat"] for row in per_draw):
                    continue
                gen = generation_index.get(spec["session_id"], {})
                status = gen.get("status", "pending")
                failure = status in {"invalid_final_output", "tool_limit_repeated"}
                for batch_name in BATCHES:
                    if batch_name == "long_run" and scenario not in core_scenarios:
                        continue
                    per_draw.append({"scenario_id": scenario, "batch": batch_name, "method": method,
                                     "source": "baek_generated", "artifact_id": spec["session_id"], "repeat": spec["repeat"],
                                     "attempt": 1, "status": status if failure else "not_scored",
                                     "generation_status": status, "mean_total_cost": None,
                                     "error": gen.get("error"), "score_path": None})
    for scenario in scenario_ids:
        for method in ("Baek-L1", "Baek-L2"):
            expected = _expected_specs(manifest, scenario, method)
            if not expected:
                continue
            for batch_name in BATCHES:
                rows = [row for row in per_draw if row["scenario_id"] == scenario and row["method"] == method and row["batch"] == batch_name]
                if batch_name == "long_run" and not rows:
                    continue
                # A retry stays inside its original draw; choose its first valid
                # attempt in attempt order, never the lowest observed test cost.
                selected_rows, failed, pending, first_attempt_invalid = [], 0, 0, 0
                for spec in expected:
                    attempts = sorted([row for row in rows if row["repeat"] == spec["repeat"]],
                                      key=lambda row: (row["attempt"], row["artifact_id"]))
                    qualification = selections[spec["session_id"]]
                    if qualification["first_attempt_invalid"]:
                        first_attempt_invalid += 1
                    chosen_id = qualification["selected_artifact_id"]
                    chosen_rows = [row for row in attempts if row["artifact_id"] == chosen_id]
                    valid = [row for row in chosen_rows if row["status"] == "ok" and _number(row["mean_total_cost"])]
                    if valid:
                        selected_rows.append(valid[0])
                    elif qualification["status"] == "failed" or (chosen_rows and all(row["status"] in POLICY_FAILURES for row in chosen_rows)):
                        failed += 1
                    else:
                        pending += 1
                for reference in ("classical_train_selected", "historical_AHD"):
                    matched = []
                    for row in selected_rows:
                        matches = [pair for pair in pairs if pair["scenario_id"] == scenario and pair["artifact_id"] == row["artifact_id"]
                                   and pair["batch"] == batch_name and pair["reference"] == reference]
                        if matches:
                            matched.append(matches[0])
                    costs = [row["mean_total_cost"] for row in selected_rows]
                    improvements = [pair["improvement_pct"] for pair in matched if _number(pair["improvement_pct"])]
                    first = next((row for row in selected_rows if row["repeat"] == 1), None)
                    first_pair = next((pair for pair in matched if pair["repeat"] == 1), None)
                    summaries.append({"scenario_id": scenario, "method": method, "batch": batch_name, "reference": reference,
                                      "n_planned": len(expected), "n_valid": len(costs), "n_failed": failed, "n_pending": pending,
                                      "n_first_attempt_invalid": first_attempt_invalid,
                                      "n_paired": len(matched), "first_draw_cost": first["mean_total_cost"] if first else None,
                                      "draw_costs": {str(spec["repeat"]): next((row["mean_total_cost"] for row in selected_rows
                                                        if row["repeat"] == spec["repeat"]), None) for spec in expected},
                                      "first_draw_improvement_pct": first_pair["improvement_pct"] if first_pair else None,
                                      "mean_cost": float(np.mean(costs)) if costs else None,
                                      "sd_cost_across_draws": float(np.std(costs, ddof=1)) if len(costs) > 1 else None,
                                      "min_cost": min(costs) if costs else None, "max_cost": max(costs) if costs else None,
                                      "mean_improvement_pct": float(np.mean(improvements)) if improvements else None,
                                      "min_improvement_pct": min(improvements) if improvements else None,
                                      "max_improvement_pct": max(improvements) if improvements else None,
                                      "significant_wins": sum(pair["significant_outcome"] == "win" for pair in matched),
                                      "significant_losses": sum(pair["significant_outcome"] == "loss" for pair in matched),
                                      "n_within_0_1pct_or_better": sum(pair.get("within_0_1pct_or_better") is True for pair in matched),
                                      "n_within_1pct_or_better": sum(pair.get("within_1pct_or_better") is True for pair in matched),
                                      "summary_selection": "earliest_globally_synthetic_qualified_attempt_per_draw; no_test_selection"})
    tables = run_dir / "tables"
    exports = {"per_draw.csv": per_draw, "paired_comparisons.csv": pairs,
               "repeat_summary.csv": summaries, "generation.csv": generation, "references.csv": refs,
               "draw_selection.csv": list(selections.values())}
    for filename, rows in exports.items():
        _csv(tables / filename, rows)
    charts = []
    for batch_name in ("fresh_test", "existing_test"):
        path = run_dir / "figures" / f"{batch_name}_improvement.svg"
        if _svg_chart(path, summaries, batch_name):
            charts.append(path)
        ahd_path = run_dir / "figures" / f"{batch_name}_vs_ahd_improvement.svg"
        if _svg_chart(ahd_path, summaries, batch_name, reference="historical_AHD"):
            charts.append(ahd_path)
    spent, uncertain = recover_spend(run_dir)
    unresolved_upper = sum(item.get("reserved_usd", 0.0) for item in uncertain)
    accepted_upper = sum(item.get("reserved_usd", 0.0) for item in uncertain
                         if item.get("charge_resolution") == "conservative_bound" and item.get("reconciled_for_resume") is True)
    recovery_budget_note = (f"其中 ${accepted_upper:.6f} 已明确保留全额上界并允许原会话恢复，实际费用仍未知。"
                            if accepted_upper > 0 else "")
    preflight = sum((_read(path).get("usage", {}).get("cost", 0) or 0)
                    for path in run_dir.glob("api_smoke*response.json"))
    known = sum(row["known_charged_usd"] or 0 for row in generation) + preflight
    completed = sum(row["status"] == "completed" for row in generation)
    historical_inventory_path = run_dir / "historical_inventory.json"
    historical_inventory = _read(historical_inventory_path) if historical_inventory_path.exists() else {}
    first_qualified = sum(row["attempts"][0]["status"] == "qualified" for row in selections.values())
    first_invalid = sum(row["first_attempt_invalid"] for row in selections.values())
    globally_selected = sum(row["status"] == "selected" for row in selections.values())
    checked = [row for row in per_draw if row["source"] == "baek_generated" and row.get("score_path")]
    unique_evals = {(row["scenario_id"], row["artifact_id"]): row for row in checked}
    exceeds = [row for row in unique_evals.values() if row["setup_exceeded_30_seconds"]]
    lines = ["# Baek 方法在 AHD4Inventory 的第一轮比较", "",
             f"报告生成时间：{datetime.now(timezone.utc).isoformat()}。", "",
             "## 结果状态与比较口径", "",
             f"计划 {len(manifest.get('sessions', []))} 个独立首试会话；当前日志中 {completed} 个会话已提交代码。"
             f"已保存 {len(unique_evals)} 个 Baek 场景策略的评测记录。生成完成不等于策略通过有效性检查。", "",
             f"整组首试合成验证：通过 {first_qualified}、确认无效 {first_invalid}、"
             f"待完成或核查 {len(selections)-first_qualified-first_invalid}，计划分母为 {len(selections)} 个独立生成组。"
             f"计入允许的补跑后，目前 {globally_selected}/{len(selections)} 组已有统一选定的合格尝试。", "",
             "主要指标为 L 个零需求备货期之后的 50 期销售总成本；越低越好。"
             "L1 对三个核心场景分别生成策略，L2 的固定设计器用于同类别的全部场景。"
             "首次独立生成（draw 1）与全部三个独立生成的均值和离散程度分别报告；不按测试成绩挑选代表策略。", "",
             "如果某组独立生成触发无效补跑，该组统一采用按尝试顺序首次通过全部所需场景合成验证的输出。"
             "L2 的一次尝试只要在所需网格任一场景无效，原尝试就不能与补跑结果逐场景拼接；"
             "完整合成验证缺失时暂不进入主结果。原始失败与每次尝试保留，"
             "repeat_summary.csv 的 n_first_attempt_invalid 单列首试无效数；补跑不增加独立生成的计划分母。", "",
             "经典对照先在前 50 条训练路径上分别拟合 base-stock、constant-order、capped base-stock，"
             "再仅按训练成本选定每场景的对照。历史 AHD 也是按保存的训练分数选择，保留不同模型及搜索预算身份。"
             "改进率 = 100 ×（对照成本 − 候选成本）/ 对照成本；正值表示 Baek 成本更低。", "",
             "## 跨场景概况", "",
             "下表先求每场景的改进率，再对已有结果的场景等权计算均值与中位数；两者都是描述指标，不构成额外的显著性检验。"
             "“三次均值”只对有效生成求均值，缺失或失败不填入虚构成本；覆盖不足时不能视为完整实验结论。", "",
             "首次生成的均值与中位数使用相同的 r1 配对场景。三次有效生成的中位数先在每场景内平均有效生成的改进率，"
             "再对这些场景均值取中位数，保持每场景等权，不把全部场景和重复次数混合后计算。", "",
             "场景分母保留该方法的完整计划范围：L1 为 3、L2 为 30。历史 AHD 对照只在有可核验策略且完成评分的场景可用，"
             "因此历史对照行的覆盖分子通常低于分母；不能把覆盖缺失解释为 Baek 失败。首次生成列的 n 单独标明实际配对场景数。", "",
             "最后一列“有效策略/计划策略”表示 Baek 策略本身的有效性覆盖，不是与该行对照的配对数。"
             "AHD 与经典基线的汇总均值可能来自不同场景子集，不能将两个汇总改进百分比直接相减并归因于方法差异。", "",
             "| 数据 | 方法 | 对照 | 有配对结果场景/计划场景 | 首次生成平均改进 | 首次生成改进中位数 | 三次有效生成平均改进 | 三次有效生成改进中位数 | 有效策略/计划策略 |",
             "|---|---|---|---:|---:|---:|---:|---:|---:|"]
    core_lines = ["## 三个核心场景：与我们的历史 AHD 直接比较", "",
                  "以下均为同一数据批次上的 50 期销售总成本，越低越好。经典成本来自训练选定的基线；"
                  "历史 AHD 也按训练记录选择，可能来自不同模型和搜索预算。r1 是第一组独立生成，"
                  "三次均值只包含整组资格通过且该场景有效的策略，括号列出有效数/计划数。"
                  "相对 AHD 的改进率只使用通过相同需求路径核验的配对，括号列出配对数/计划数；缺失记为 —。", ""]

    def core_reference_cost(scenario_id, method, batch_name):
        entry = indexed.get((scenario_id, method))
        if entry is None:
            return None
        record = entry[1]
        batch = record.get("batches", {}).get(batch_name)
        if _batch_status(record, batch) != "ok":
            return None
        return batch.get("summary", {}).get("mean_total_cost")

    def core_mean_cell(row):
        return f"{_fmt(row.get('mean_cost'))} ({row['n_valid']}/{row['n_planned']})" if row else "—"

    def core_improvement_cell(row):
        return (f"{_fmt(row['mean_improvement_pct'])}% ({row['n_paired']}/{row['n_planned']})"
                if row and _number(row.get("mean_improvement_pct")) else "—")

    for batch_name in ("fresh_test", "existing_test"):
        core_lines += [f"### {BATCH_LABELS[batch_name]}", "",
                       "| 场景 | 经典成本 | 我们的历史 AHD 成本 | L1 r1 | L1 三次均值 | L2 r1 | L2 三次均值 | L1 相对 AHD 改进 | L2 相对 AHD 改进 |",
                       "|---|---:|---:|---:|---:|---:|---:|---:|---:|"]
        for scenario_id in sorted(s for s in core_scenarios if s):
            l1 = next((row for row in summaries if row["scenario_id"] == scenario_id and row["batch"] == batch_name
                       and row["method"] == "Baek-L1" and row["reference"] == "historical_AHD"), {})
            l2 = next((row for row in summaries if row["scenario_id"] == scenario_id and row["batch"] == batch_name
                       and row["method"] == "Baek-L2" and row["reference"] == "historical_AHD"), {})
            classic = core_reference_cost(scenario_id, classical_choice.get(scenario_id), batch_name)
            ahd = core_reference_cost(scenario_id, "AHD-historical", batch_name)
            core_lines.append(f"| {scenario_id} | {_fmt(classic)} | {_fmt(ahd)} | {_fmt(l1.get('first_draw_cost'))} | "
                              f"{core_mean_cell(l1)} | {_fmt(l2.get('first_draw_cost'))} | {core_mean_cell(l2)} | "
                              f"{core_improvement_cell(l1)} | {core_improvement_cell(l2)} |")
        core_lines.append("")
        core_figure = (run_dir / "figures/core_fresh_test_comparison.png").resolve()
        if batch_name == "fresh_test" and core_figure.is_file():
            core_lines += [f"![核心场景独立新需求比较]({core_figure})", "",
                           "圆点表示各次独立生成；线段表示对需求路径计算的配对 95% 区间；"
                           "菱形表示三次生成的平均值。区间不包含生成之间的变异。", ""]
    insertion = lines.index("## 跨场景概况")
    lines[insertion:insertion] = core_lines
    for batch_name in BATCHES:
        for method in ("Baek-L1", "Baek-L2"):
            for reference in ("classical_train_selected", "historical_AHD"):
                group = [r for r in summaries if r["batch"] == batch_name and r["method"] == method and r["reference"] == reference]
                if not group:
                    continue
                lines.append(_cross_scenario_summary_line(group, batch_name, method, reference))
    if not any(pair["analysis_role"] == "main" for pair in pairs):
        lines += ["", "**当前没有通过核验的配对成本结果，尚不能判断方法表现。**"]
    lines += ["", "### 显著性与小差距比例", "",
              "显著胜/负按每个独立生成、每个场景的配对 95% 区间判断；相同生成跨场景不当作统计独立样本。"
              "0.1% / 1% 比例为场景层面的描述指标，含成本更低的场景：改进率分别 ≥ −0.1% / −1%。"
              "分母为相应列已配对且对照均值大于零的场景数。三次均值一列先在场景内平均有效生成的改进率。", "",
              "| 数据 | 方法 | 对照 | 逐次配对显著胜 / 负 / 全部 | r1：0.1% / 1% 以内或更好 | 三次均值：0.1% / 1% 以内或更好 |",
              "|---|---|---|---:|---:|---:|"]
    def threshold_share(values, threshold):
        if not values:
            return "—"
        n = sum(value >= -threshold for value in values)
        return f"{n}/{len(values)} ({100*n/len(values):.1f}%)"
    for batch_name in BATCHES:
        for method in ("Baek-L1", "Baek-L2"):
            for reference in ("classical_train_selected", "historical_AHD"):
                group = [r for r in summaries if r["batch"] == batch_name and r["method"] == method and r["reference"] == reference]
                if not group:
                    continue
                first = [r["first_draw_improvement_pct"] for r in group if _number(r["first_draw_improvement_pct"])]
                means = [r["mean_improvement_pct"] for r in group if _number(r["mean_improvement_pct"])]
                label = "训练选定经典基线" if reference == "classical_train_selected" else "历史 AHD"
                lines.append(f"| {BATCH_LABELS[batch_name]} | {method} | {label} | "
                             f"{sum(r['significant_wins'] for r in group)} / {sum(r['significant_losses'] for r in group)} / {sum(r['n_paired'] for r in group)} | "
                             f"{threshold_share(first,.1)} / {threshold_share(first,1)} | {threshold_share(means,.1)} / {threshold_share(means,1)} |")
    lines += ["", "## 独立新需求：逐场景结果", "",
              "三次成本按 r1 / r2 / r3 顺序列出；无效或尚未评分记为 —。标准差描述生成变异，不是置信区间。"
              "逐次配对 95% bootstrap 区间见 paired_comparisons.csv，抽样单位为完整需求路径。", "",
              "| 场景 | 方法 | 首次成本 | 全部有效生成均值 ± 标准差 | 三次成本 r1 / r2 / r3 | 相对经典基线平均改进 | 有效/计划 | 失败/待完成或核查 |",
              "|---|---|---:|---:|---:|---:|---:|---:|"]
    for row in summaries:
        if row["batch"] == "fresh_test" and row["reference"] == "classical_train_selected":
            draw_costs = " / ".join(_fmt(value) for value in row["draw_costs"].values())
            lines.append(f"| {row['scenario_id']} | {row['method']} | {_fmt(row['first_draw_cost'])} | "
                         f"{_fmt(row['mean_cost'])} ± {_fmt(row['sd_cost_across_draws'])} | {draw_costs} | "
                         f"{_fmt(row['mean_improvement_pct'])}% | {row['n_valid']}/{row['n_planned']} | {row['n_failed']}/{row['n_pending']} |")
    for path in charts:
        lines += ["", f"![{path.stem}]({path})", "", _link(path, "下载独立 SVG 图")]
    lines += ["", "## 稳健性与有效性", "",
              f"独立新需求每场景 {manifest.get('fresh_test_paths', '—')} 条路径；整数检查对所有方法统一使用 ties-to-even 取整。"
              "长期检查仅覆盖三个核心场景："
              f"{manifest.get('long_run_paths', '—')} 条 × {manifest.get('long_run_periods', '—')} 期，丢弃前 {manifest.get('long_run_burn_in', '—')} 期。"
              "各检查均使用已经冻结的策略，不据此调参。长期结果的总成本对应保留期数，横向阅读应使用每期成本列。"
              "这项有限长轨迹敏感性检查没有证明系统已经达到稳态；当前未预先登记分段稳定性判据，不事后宣称收敛。", "",
              "配对统计要求相同的需求路径与计分协议；有需求哈希时核对哈希，同时核对逐路径需求总量、路径数及计分期数。"
              "逐对 95% 区间描述需求抽样误差，不包含生成之间的差异，且没有进行多重比较校正。", "",
              "明确无效输出、非法策略或策略执行超时计为失败；尚未评分、需要人工核查、来源哈希不一致或执行基础设施故障"
              "列入待完成或核查，不擅自认定为模型策略失败。", "",
              f"初始化超过原文 30 秒目标的 Baek 场景策略：{len(exceeds)}/{len(unique_evals)}。"
              "600 秒为防止初始化卡死的执行上限；超过 30 秒的记录保留并标明，不宣称满足原文的初始化时间目标。", ""]
    lines += ["经典基线的向量化评分器没有测量逐动作耗时；其计时占位值不解释为零运行时间。", ""]
    if exceeds:
        lines += ["| 场景 | 策略 | 初始化秒数 |", "|---|---|---:|"]
        lines += [f"| {r['scenario_id']} | {r['artifact_id']} | {_fmt(r['setup_seconds'])} |" for r in exceeds]
        lines.append("")
    invalid = [row for row in unique_evals.values() if row["status"] != "ok"]
    if invalid:
        lines += ["### 未通过或未完成评测的策略", "", "| 场景 | 策略 | 状态 | 原因 |", "|---|---|---|---|"]
        lines += [f"| {r['scenario_id']} | {r['artifact_id']} | {r['status']} | {_cell(r['error'] or '见评测记录')} |" for r in invalid]
        lines.append("")
    lines += ["## 模型费用与运行资源", "",
              f"模型：`{manifest.get('model', '—')}`，推理强度 `{manifest.get('reasoning_effort', '—')}`。"
              f"已知实际计费 **${known:.6f}**，其中接口预检 ${preflight:.6f}；"
              f"含未决请求保守预留的账本金额 **${spent:.6f}**，全局上限 ${manifest.get('spend_limit_usd_including_preflight_and_retries', 30):.2f}。"
              f"仍有 {len(uncertain)} 条费用未决记录，上界合计 ${unresolved_upper:.6f}。" + recovery_budget_note +
              "Python 模拟用时不折算成 API token 费用。", "",
              "Python 用时按单调时钟统计子进程墙钟时间，包含启动开销，不是 CPU 秒数。"
              "每个 worker 的 BLAS 设置为单线程；耗时仍受硬件和其他并发任务影响。"
              "时间预算是在本次机器与调度配置下的执行限制，不能作为跨硬件严格相等的计算量。", "",
              "| 会话 | 状态 | 实际已知费用 | 输入 token | 输出 token（含推理） | Python 墙钟秒数 | 工具调用 | 冻结代码 |",
              "|---|---|---:|---:|---:|---:|---:|---|"]
    for row in generation:
        code_link = _link(row["code_path"], "源码") if row["code_path"] else "—"
        lines.append(f"| {row['session_id']} | {row['status']} | ${_fmt(row['known_charged_usd'], 6)} | {row['input_tokens']} | "
                     f"{row['output_tokens']} | {_fmt(row['python_seconds'])} | {row['tool_calls'] if row['tool_calls'] is not None else '—'} | {code_link} |")
    reconciliation = run_dir / "billing_reconciliation.json"
    if reconciliation.exists():
        infra = _read(reconciliation)
        lines += ["", f"基础设施记录：{infra.get('rejected_planned_requests', '—')} 个计划请求在模型推理开始前被路由层拒绝，"
                  f"另有 {infra.get('diagnostic_rejected_requests', 0)} 个诊断拒绝请求。已核对这部分计费为 "
                  f"${infra.get('preinference_rejections_charged_usd', 0):.6f}。"
                  "它们没有生成策略，不计入独立生成次数或策略失败率。"
                  + _link(reconciliation, "费用核对记录")]
    pause_records = sorted((run_dir / "pause_history").glob("*.json"))
    recorded_three_workers = any(
        "runner generate --workers 3" in process.get("command", "")
        for path in pause_records for process in _read(path).get("processes", []))
    if recorded_three_workers and (run_dir / "evaluation_queue_progress.json").exists():
        lines += ["", "本轮已记录的实际调度为生成端至多 3 个 worker，与自动评分端至多 2 个 worker 同时运行。"
                  "manifest 记录了操作系统和逻辑 CPU 数；这里补充实际并发配置，以便解释墙钟预算。"]
    recovered_tools = sorted((run_dir / "sessions").glob("*/recovered_tool_pending.json"))
    preserved_tools = [path for path in recovered_tools
                       if "Preserved process memory" in _read(path).get("note", "")]
    http_drain_path = run_dir / "resume_http_drain.json"
    response_preserved = (http_drain_path.exists()
                          and _read(http_drain_path).get("status") == "response_preserved")
    if pause_records and (preserved_tools or response_preserved):
        note = "暂停与恢复：本次运行记录了用户要求的暂停。日志起止时间包含暂停时段；恢复后的 Python 执行秒数排除了暂停。"
        if preserved_tools:
            note += (f"{len(preserved_tools)} 个已有 Python 进程保留内存后继续执行，没有重跑；"
                     "暂停前的有效执行时长含记录注明的亚秒级估计误差。")
        if response_preserved:
            note += "暂停时尚未返回的 HTTP 响应被接收并保存，没有重新发送该请求。"
        note += "这些恢复操作不增加独立生成或无效补跑次数。"
        evidence = [_link(pause_records[-1], "暂停记录")]
        if response_preserved:
            evidence.append(_link(http_drain_path, "原请求响应恢复记录"))
        evidence += [_link(path, path.parent.name + " 进程恢复记录") for path in preserved_tools]
        lines += ["", note + " " + "；".join(evidence)]
    lines += _transport_recovery_lines(run_dir, generation)
    hash_mismatches = [row["session_id"] for row in generation if row["code_hash_matches"] is False]
    if hash_mismatches:
        warnings.append("生成源码与冻结哈希不一致：" + ", ".join(hash_mismatches))
    proposal_path = next((parent / "docs/baek_2026_comparison_proposal.md"
                          for parent in Path(__file__).resolve().parents
                          if (parent / "docs/baek_2026_comparison_proposal.md").is_file()), None)
    proposal_link = (_link(proposal_path, "已批准方案 §3")
                     if proposal_path is not None else "已批准方案 §3")
    lines += ["", "## 适配范围与结论限制", "",
              "本实验比较 Baek 的单任务工具调用策略设计流程在我们的环境中的表现。"
              "目标为 50 期销售成本、动作允许非负有限实数且没有订货容量上限；固定提前期、"
              "确定性 stationary 策略，以及 Poisson、取整 Exponential、截零取整 Normal 是本轮具体设定。", "",
              "历史 AHD 和 Baek 可能使用不同模型、计算预算及信息条件：Baek 知道真实需求分布，"
              "历史 AHD 主要依据训练样本。因此结果不能单独归因于搜索框架。现有基准测试集曾用于历史评测，"
              "独立新需求结果单独列出。没有可靠最优解的场景仅报告相对对照的成本差，不称最优性差距。", "",
              "提示描述也有差异：仓库现有 v2 提示的到货/决策时序描述与实际模拟器不一致，"
              "本轮问题描述已按实际动态修正；历史 AHD 保留既有策略，没有使用本轮相同提示重新生成。"
              "这不表示全部历史运行均使用该 v2 提示，也不据此推断这一差异对成绩的影响。"
              f"见{proposal_link}。", "",
              "历史 AHD 可用性及模型身份见下表；所有训练候选来源、索引、哈希和审计结果见 references.csv。", "",
              f"冻结的历史清单包含 {historical_inventory.get('run_count', '—')} 个运行、"
              f"{historical_inventory.get('scenario_count', '—')} 个有来源策略的场景；当前已保存历史评测记录 {len(historical)} 个场景。", "",
              "| 场景 | 历史模型 | 历史运行 | 训练记录成本 | 评测状态 |", "|---|---|---|---:|---|"]
    for row in refs:
        if row["reference"] == "historical_AHD":
            lines.append(f"| {row['scenario_id']} | {_cell(row.get('model') or '—')} | {_cell(row.get('run_name') or '—')} | "
                         f"{_fmt(row.get('recorded_train_mean_cost'))} | {row.get('status', '—')} |")
    lines += ["", "## 完整表格与记录", ""]
    for filename, label in [("policy_design_all_draws.md", "三次独立生成的订货规则解释"),
                            ("policy_design_comparison.md", "第一组规则详解")]:
        if (run_dir / filename).exists():
            lines.append(f"- {_link(run_dir / filename, label)}")
    lines += [f"- {_link(tables / filename)}" for filename in exports]
    lines += [f"- {_link(run_dir / 'manifest.json', '冻结的实验定义与数据哈希')}", ""]
    if warnings:
        lines += ["## 核查事项", ""] + [f"- {_cell(item)}" for item in warnings] + [""]
    report_path = run_dir / "report.md"
    report_path.write_text("\n".join(lines), encoding="utf-8")
    return {"report_path": str(report_path), "tables": {name: len(rows) for name, rows in exports.items()},
            "figures": [str(path) for path in charts], "warnings": warnings,
            "known_charged_usd": known, "charged_or_reserved_usd": spent,
            "unresolved_cost_upper_usd": unresolved_upper,
            "accepted_conservative_recovery_upper_usd": accepted_upper,
            "paired_comparisons": len(pairs),
            "main_paired_comparisons": sum(pair["analysis_role"] == "main" for pair in pairs)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path, default=DEFAULT_RUN)
    parser.add_argument("--n-bootstrap", type=int, default=5000)
    args = parser.parse_args()
    print(json.dumps(generate_report(args.run_dir, n_bootstrap=args.n_bootstrap), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
