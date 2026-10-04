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
import gzip
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


def generation_quality(run_dir):
    """Count saved search slots and ledger reservations without running code.

    A slot can contain two model requests. Pending requests and seed optimization
    do not become extra slots, and unreadable artifacts are not model failures.
    """
    root = Path(run_dir).resolve()
    protocol = _read(root / "protocol.json", {}).get("configuration", {})
    evolution = protocol.get("evolution", {})
    population, generations = int(evolution.get("population", 10)), int(evolution.get("generations", 10))
    plans = {}
    for spec in scenario_specs():
        for repeat in (1, 2, 3):
            plans[f"training/{spec.scenario_id}/self_evolve_h200_r{repeat}"] = ("primary", 200, repeat)
    for horizon in (50, 100, 500):
        for repeat in (1, 2, 3):
            plans[f"training/exp_ar_pos08_fixed6/self_evolve_h{horizon}_r{repeat}"] = ("horizon_extension", horizon, repeat)
    directories = set(plans)
    for category in ("training", "pilots"):
        directories.update(str(p.relative_to(root)) for p in (root / category).glob("*/*") if p.is_dir())
    rows, issues, transport_records = [], [], []
    for relative in sorted(directories):
        directory = root / relative
        parts = Path(relative).parts
        definition = _read(directory / "search_definition.json", {})
        scope, horizon, repeat = plans.get(relative, ("pilot" if parts[0] == "pilots" else "other_training", None, None))
        if scope in {"primary", "horizon_extension"}:
            planned = population * generations
            if definition and (definition.get("population_size") != population or definition.get("generations") != generations
                               or definition.get("horizon") != horizon or definition.get("repeat") != repeat
                               or definition.get("scenario", {}).get("scenario_id") != parts[1]):
                issues.append({"chain": relative, "error": "Search definition differs from planned identity"})
        else:
            horizon, repeat = definition.get("horizon"), definition.get("repeat")
            planned = definition.get("population_size", 0) * definition.get("generations", 0) if definition else None
        paths = sorted((directory / "candidates").glob("*.json.gz"))
        valid = invalid = unclassified = requests = transport_failures = 0
        seen = set()
        for path in paths:
            try:
                with gzip.open(path, "rt") as handle:
                    candidate = json.load(handle)
                context = candidate["context"]
                key = (context["generation"], context["operator"], context["candidate_index"])
                if key in seen or path.name != f"g{key[0]:03d}_{key[1]}_{key[2]:03d}.json.gz":
                    raise ValueError("Duplicate slot or filename/context mismatch")
                seen.add(key)
                if (key[1] != "m2" or not 1 <= key[0] <= definition.get("generations", generations)
                        or not 0 <= key[2] < definition.get("population_size", population)):
                    raise ValueError("Candidate slot outside planned search")
                offspring = candidate["offspring"]
                code, objective = offspring.get("code"), offspring.get("objective")
                if code and (not isinstance(code, str) or candidate.get("code_sha256") != hashlib.sha256(code.encode()).hexdigest()):
                    raise ValueError("Candidate source hash mismatch")
                calls = candidate["model_requests"]
                if isinstance(calls, bool) or not isinstance(calls, int) or not 0 <= calls <= 2:
                    raise ValueError("Invalid candidate model request count")
                is_valid = bool(isinstance(code, str) and code.strip() and isinstance(objective, (int, float))
                                and not isinstance(objective, bool) and math.isfinite(objective))
                transport = candidate.get("transport_failure")
                if transport is not None:
                    if (not isinstance(transport, dict) or not isinstance(transport.get("request_id"), str)
                            or not transport["request_id"].strip()):
                        raise ValueError("Transport failure evidence lacks a request identity")
                    if is_valid:
                        raise ValueError("Transport-failure slot also contains a valid candidate")
                    transport_failures += 1
                    transport_records.append(dict(file=str(path.relative_to(root)), scope=scope,
                                                  request_id=transport["request_id"],
                                                  error_type=transport.get("error_type"),
                                                  resolution=transport.get("resolution")))
                requests += calls
                valid += int(is_valid)
                invalid += int(not is_valid)
            except (OSError, EOFError, KeyError, TypeError, ValueError) as exc:
                unclassified += 1
                issues.append({"file": str(path.relative_to(root)), "error": str(exc)})
        completion = _read(directory / "completed.json", {})
        completed = completion.get("status") in {"complete", "completed"}
        if planned is not None and len(paths) > planned:
            issues.append({"chain": relative, "error": "Recorded candidate slots exceed plan"})
        if completed and (planned is None or len(paths) != planned or unclassified):
            issues.append({"chain": relative, "error": "Completed chain has incomplete candidate records"})
        rows.append(dict(chain=relative, scenario_id=parts[1], policy_id=parts[2], scope=scope,
                         source_training_horizon=horizon, repeat=repeat, started=bool(definition or paths),
                         completed=completed, denominator_complete=bool(completed and planned == len(paths) and not unclassified),
                         planned_candidate_slots=planned, recorded_candidate_slots=len(paths),
                         not_yet_recorded_slots=max(planned-len(paths), 0) if planned is not None else None,
                         valid_candidate_slots=valid, invalid_candidate_slots=invalid,
                         transport_failure_slots=transport_failures,
                         model_or_constraint_invalid_slots=invalid-transport_failures,
                         unclassified_candidate_slots=unclassified,
                         valid_rate_classified_slots=valid/(valid+invalid) if valid+invalid else None,
                         model_requests_recorded_slots=requests))
    scopes = {}
    for scope in ("primary", "horizon_extension", "pilot", "other_training"):
        group = [row for row in rows if row["scope"] == scope]
        aggregate = {name: sum(row[name] or 0 for row in group) for name in
                     ("planned_candidate_slots", "recorded_candidate_slots", "not_yet_recorded_slots", "valid_candidate_slots",
                      "invalid_candidate_slots", "transport_failure_slots", "model_or_constraint_invalid_slots",
                      "unclassified_candidate_slots", "model_requests_recorded_slots")}
        classified = aggregate["valid_candidate_slots"] + aggregate["invalid_candidate_slots"]
        aggregate.update(planned_chains=len(group), started_chains=sum(row["started"] for row in group),
                         completed_chains=sum(row["completed"] for row in group),
                         denominator_complete=bool(group and all(row["denominator_complete"] for row in group)),
                         valid_rate_classified_slots=aggregate["valid_candidate_slots"]/classified if classified else None)
        scopes[scope] = aggregate
    # The writer replaces api_budget.json atomically; one read is a coherent,
    # read-only snapshot and does not acquire the mutating client ledger API.
    ledger = _read(root / "api_budget.json", {})
    accounting = {"available": bool(ledger), "limit_usd": ledger.get("limit_usd"), "categories": {}}
    def new_bucket():
        return dict(requests=0, completed_requests=0, pending_requests=0, uncertain_requests=0,
                    known_cost_usd=0., uncertain_held_upper_usd=0., pending_upper_usd=0.)
    total = new_bucket()
    for request in ledger.get("requests", {}).values():
        metadata = request.get("metadata", {})
        category = "preflight" if metadata.get("phase") == "preflight" else "other"
        chain = metadata.get("chain_dir")
        if chain:
            try:
                path = Path(chain)
                relative = str((path if path.is_absolute() else root/path).resolve().relative_to(root))
                category = next((r["scope"] for r in rows if r["chain"] == relative), "other")
            except ValueError:
                category = "other"
        bucket = accounting["categories"].setdefault(category, new_bucket())
        state = request.get("state")
        known, reserved = request.get("actual_cost_usd") or 0., request.get("reserved_usd") or 0.
        if any(isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0
               for value in (known, reserved)):
            issues.append({"file": "api_budget.json", "error": "Invalid accounting amount"})
            accounting["available"] = False
            continue
        for target in (bucket, total):
            target["requests"] += 1
            target["completed_requests"] += int(state == "complete")
            target["pending_requests"] += int(state == "pending")
            target["uncertain_requests"] += int(state in {"unknown_charge", "missing_cost"})
            target["known_cost_usd"] += known
            target["pending_upper_usd"] += reserved if state == "pending" else 0.
            target["uncertain_held_upper_usd"] += reserved if state in {"unknown_charge", "missing_cost"} else 0.
        if state not in {"complete", "pending", "unknown_charge", "missing_cost"}:
            issues.append({"file": "api_budget.json", "error": "Unrecognized request accounting state"})
            accounting["available"] = False
    for bucket in [total, *accounting["categories"].values()]:
        bucket["held_upper_usd"] = bucket["uncertain_held_upper_usd"] + bucket["pending_upper_usd"]
        bucket["committed_upper_usd"] = bucket["known_cost_usd"] + bucket["held_upper_usd"]
    accounting.update(total)
    return dict(created_utc=datetime.now(timezone.utc).isoformat(), scopes=scopes, chains=rows, accounting=accounting, issues=issues,
                transport_failure_records=transport_records,
                invalid_definition="invalid_candidate_slots includes transport_failure_slots; model_or_constraint_invalid_slots excludes them",
                transport_failure_definition="explicit candidate.transport_failure evidence with request identity; costs come only from the API ledger, never counted again from candidate evidence",
                valid_definition="saved nonempty code with verified source hash and finite training objective; not a test-performance criterion",
                denominator="valid rate uses classified saved candidate slots; unsaved and unreadable slots are reported separately",
                model_requests="saved-slot requests may lag ledger requests for the candidate currently in progress",
                constraints="four-argument Numba-compatible numerical whitelist; full whitelist was not enumerated in model prompts")


def _generation_quality_lines(quality):
    lines = ["## 候选有效率与费用（动态快照）", "",
             "有效候选指有非空代码、源码哈希一致且训练目标有限的已落盘候选，不表示其测试表现良好；每个 slot 最多包含两次模型请求。尚未落盘的 slot 不算失败，损坏记录另列；有效率以可分类的已落盘 slot 为分母。", "",
             "| 范围 | 完成/计划链 | 已落盘/计划 slot | 有效 | 无效合计 | 输出/约束无效 | 通信失败 | 未分类 | 有效率 | 已落盘 slot 的模型请求 |",
             "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for scope, label in (("primary", "主实验"), ("horizon_extension", "按 H 重训扩展"), ("pilot", "试运行"), ("other_training", "其他训练")):
        row = quality["scopes"][scope]
        if scope == "other_training" and not row["planned_chains"]:
            continue
        rate = f"{100*row['valid_rate_classified_slots']:.1f}%" if row["valid_rate_classified_slots"] is not None else "—"
        lines.append(f"| {label} | {row['completed_chains']}/{row['planned_chains']} | {row['recorded_candidate_slots']}/{row['planned_candidate_slots']} | {row['valid_candidate_slots']} | {row['invalid_candidate_slots']} | {row['model_or_constraint_invalid_slots']} | {row['transport_failure_slots']} | {row['unclassified_candidate_slots']} | {rate} | {row['model_requests_recorded_slots']} |")
    lines += ["", "无效合计包括通信失败；通信失败仅依据候选中明确记录的 transport_failure 证据计数，不归为模型输出或数值约束失败。通信失败涉及的未知费用仅按 API 账本保留一次上限，恢复记录不代表费用已确认或已释放。",
              "未完成链的候选分母仍在增长。策略接口为四个参数、Numba-compatible 的白名单数值子集，不能使用无限制 Python；模型提示没有列出完整白名单，故白名单拒绝等失败不能全部解释为模型能力不足。正式协议保持冻结，无效候选计入原搜索额度，不因结果不利而额外重抽。", ""]
    account = quality["accounting"]
    if account["available"]:
        lines += [f"API 账本包含 preflight、试运行与正式训练：已知费用 ${account['known_cost_usd']:.6f}；未决费用保留上限 ${account['uncertain_held_upper_usd']:.6f}（{account['uncertain_requests']} 请求）；正在处理的请求预留 ${account['pending_upper_usd']:.6f}（{account['pending_requests']} 请求）。合计占用预算上界 ${account['committed_upper_usd']:.6f}，共 {account['requests']} 个请求；保留上限不是已确认费用。", ""]
    else:
        lines += ["API 费用账本尚未提供或存在待核对记录。", ""]
    lines += ["详见[候选逐链统计](tables/generation_quality.csv)与[完整统计及费用分类](generation_quality.json)。", ""]
    if quality["issues"]:
        lines += [f"候选或费用记录有 {len(quality['issues'])} 项待核对，详见上述 JSON；这些记录与评价结果完整性分别统计。", ""]
    return lines


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


def paired_comparisons(records, averaged, *, run_dir, n_bootstrap=5000,
                       reference_scopes=("baseline",), candidate_scopes=("primary",),
                       match_training_horizon=False):
    cache_dir = Path(run_dir) / "analysis_cache"
    references = {}
    for item in records:
        row = item["row"]
        if row["scope"] in reference_scopes:
            references.setdefault((row["scenario_id"], row["mode"], row["horizon"]), []).append(item)
    results, issues = [], []
    for candidate in [x for x in records if x["row"]["scope"] in candidate_scopes] + averaged:
        row, arrays = candidate["row"], candidate["arrays"]
        for reference in references.get((row["scenario_id"], row["mode"], row["horizon"]), []):
            ref, ref_arrays = reference["row"], reference["arrays"]
            if match_training_horizon and row["source_training_horizon"] != ref["source_training_horizon"]:
                continue
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
                            "reference_training_horizon": ref["source_training_horizon"],
                            "mode": row["mode"], "horizon": row["horizon"],
                            "pairing_provenance_verified": bool(row["provenance_verified"] and ref["provenance_verified"] and tape_hash), **stats})
    return results, issues


def horizon_refit_summary(records):
    """Preregistered AR+ diagonal: separate training at each evaluation horizon."""
    sid = "exp_ar_pos08_fixed6"
    chosen = []
    for item in records:
        row = item["row"]
        horizon = row["horizon"]
        if row["scenario_id"] != sid or row["source_training_horizon"] != horizon:
            continue
        if row["family"] == "self_evolve":
            if not (row.get("full_protocol") is True and row.get("repeat") in (1, 2, 3)
                    and row["policy_id"] == f"self_evolve_h{horizon}_r{row['repeat']}"):
                continue
        elif row["family"] in BASELINES:
            if row["policy_id"] != f"baseline_h{horizon}_" + row["family"]:
                continue
        else:
            continue
        chosen.append(item)
    rows, averaged = [], []
    for mode in ("steady", "cold_start"):
        for horizon in HORIZONS:
            for family in (*BASELINES, "self_evolve"):
                items = [x for x in chosen if (x["row"]["mode"], x["row"]["horizon"], x["row"]["family"]) == (mode, horizon, family)]
                expected = 3 if family == "self_evolve" else 1
                row = {"scenario_id": sid, "family": family, "mode": mode,
                       "source_training_horizon": horizon, "evaluation_horizon": horizon,
                       "comparison_type": "separately_retrained_at_each_horizon",
                       "n_valid_repeats": len(items), "n_planned_repeats": expected,
                       "policy_ids": [x["row"]["policy_id"] for x in items],
                       "provenance_complete": len(items) == expected and all(x["row"]["provenance_verified"] for x in items)}
                for metric in METRICS:
                    values = [x["row"][metric] for x in items]
                    row[metric + "_mean"] = float(np.mean(values)) if values else None
                    row[metric + "_sd"] = float(np.std(values, ddof=1)) if len(values) > 1 else None
                rows.append(row)
                if family == "self_evolve" and items:
                    first = items[0]
                    if all(x["row"].get("dataset_arrays_sha256") == first["row"].get("dataset_arrays_sha256")
                           and np.array_equal(x["arrays"]["demand_units"], first["arrays"]["demand_units"]) for x in items):
                        identity = dict(first["row"], policy_id=f"self_evolve_h{horizon}_mean_of_available_repeats",
                                        repeat=None, n_repeats=len(items), aggregate="mean_of_available_repeats")
                        identity["provenance_verified"] = all(x["row"]["provenance_verified"] for x in items)
                        means = {name: np.mean(np.stack([x["arrays"][name] for x in items]), axis=0) for name in NPZ_METRICS}
                        means["demand_units"] = first["arrays"]["demand_units"].copy()
                        averaged.append({"row": identity, "arrays": means})
    present = {(x["row"]["policy_id"], x["row"]["mode"]) for x in chosen}
    finished_self = sum(all((f"self_evolve_h{h}_r{rep}", mode) in present for mode in ("steady", "cold_start"))
                        for h in HORIZONS for rep in (1, 2, 3))
    finished_baselines = sum(all((f"baseline_h{h}_{family}", mode) in present for mode in ("steady", "cold_start"))
                            for h in HORIZONS for family in BASELINES)
    state = {"scenario_id": sid, "expected_self_evolve_groups": 12, "expected_extra_self_evolve_groups": 9,
             "self_evolve_groups_with_both_diagonals": finished_self,
             "expected_baseline_groups": 28, "baseline_groups_with_both_diagonals": finished_baselines,
             "expected_raw_diagonal_rows": 80, "raw_diagonal_rows": len(chosen),
             "complete": finished_self == 12 and finished_baselines == 28 and all(r["provenance_complete"] for r in rows)}
    return rows, chosen, averaged, state


def write_horizon_refit_report(root, rows, state):
    lines = ["# 每个 horizon 单独重训：预注册扩展", "",
             f"**状态：{'完整' if state['complete'] else '尚未完成'}。self-evolve 已完成两个初始化口径 {state['self_evolve_groups_with_both_diagonals']}/12 组；基线 {state['baseline_groups_with_both_diagonals']}/28 组。**", "",
             "固定环境：正相关 Gaussian-copula 需求（latent ρ=0.8），连续指数边际均值 100，固定交货期 6，h=1、p=2。",
             "此处每个 H=50/100/200/500 都重新优化策略，表中仅保留训练 horizon 与评价 horizon 相同的对角比较。H=200 复用主实验的三次运行与七个基线；另九次 LLM 运行属于扩展，不计入 18 个主实验分母。",
             "这与[主报告](report.md)中固定 H=200 策略跨四种评价窗口的比较不同。所有优化仍只使用训练集；三个重复全部报告，没有按测试成本选择最好一轮。cold_start 表评价同一批按 B=500 训练的策略，从空库存开始，不表示另做冷启动目标训练。",
             "成本单位为每期。SD 是三个独立生成重复的样本标准差，n−1 分母；基线只有一个训练拟合结果，SD 留空。有效数不足时结果为部分记录均值。独立 CSV 中的 95% 区间为单次比较的完整路径配对 bootstrap 区间，未作多重比较校正，也不包含生成变异；1,000 条测试路径不是 1,000 次独立 LLM 训练。需求严格平稳，B=500 仅使库存近似稳态；固定平稳策略的期望单位期成本不应因 H 增大而机械降低。", "",
             "![Matched train and evaluation horizons](figures/horizon_refit.png)", ""]
    for mode, title in (("steady", "预热 500 期后的对角比较"), ("cold_start", "冷启动对角比较")):
        lines += [f"## {title}", "", "| 训练 H = 评价 H | 方法 | 成本均值 | 生成样本 SD | 有效/计划 | 满足率 |", "|---:|---|---:|---:|---:|---:|"]
        for row in rows:
            if row["mode"] != mode:
                continue
            fill = "—" if row["fill_rate_mean"] is None else f"{100*row['fill_rate_mean']:.2f}%"
            lines.append(f"| {row['evaluation_horizon']} | {LABELS[row['family']]} | {_format(row['mean_cost_per_period_mean'])} | {_format(row['mean_cost_per_period_sd'])} | {row['n_valid_repeats']}/{row['n_planned_repeats']} | {fill} |")
        lines.append("")
    lines += ["## 完整数据", "", "- [对角比较均值与样本 SD](tables/horizon_refit.csv)",
              "- [各生成重复与重复均值，配对相同训练 H 的全部基线](tables/horizon_refit_paired.csv)",
              "- [含非对角交叉评价的全部原始结果](tables/all_results.csv)", "",
              "该扩展只覆盖预注册的 AR+ 固定交货期环境，不能据此宣称所有需求过程都应按 horizon 重训。", ""]
    (root / "horizon_refit.md").write_text("\n".join(lines))


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
    quality = generation_quality(root)
    repeats, averaged = summarize_repeats(records)
    pairs, pairing_issues = paired_comparisons(records, averaged, run_dir=root, n_bootstrap=n_bootstrap)
    issues.extend(pairing_issues)
    refit_rows, refit_selected, refit_averaged, refit_state = horizon_refit_summary(records)
    refit_pairs, refit_issues = paired_comparisons(refit_selected, refit_averaged, run_dir=root, n_bootstrap=n_bootstrap,
                                                reference_scopes=("baseline", "baseline_extension"),
                                                candidate_scopes=("primary", "horizon_extension"), match_training_horizon=True)
    issues.extend(refit_issues)
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
               "horizon_refit": {**refit_state, "paired_rows": len(refit_pairs)},
               "generation_quality": quality["scopes"], "generation_quality_issues": quality["issues"],
               "api_accounting": quality["accounting"],
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
    _write_csv(tables / "horizon_refit.csv", refit_rows)
    _write_csv(tables / "generation_quality.csv", quality["chains"])
    _write_json(root / "generation_quality.json", quality)
    _write_csv(tables / "horizon_refit_paired.csv", refit_pairs, ("scenario_id", "source_training_horizon", "reference_training_horizon", "mode", "reference_family", "aggregate"))
    write_horizon_refit_report(root, refit_rows, refit_state)
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
             "主策略在真实需求预热 500 期后，以 H=200 的训练成本优化；冻结同一策略评价 H=50/100/200/500。四个窗口共享同一路径前缀，不能当作独立重复。需求从不变分布初始化，严格平稳；库存仅经过 B=500 的有限预热，属于近似稳态。冷启动从空库存与空 pipeline 开始，没有免费零需求备货期，另列结果。",
             "所有方法观察同样的上一期完整需求、当前库存、按到货日期分桶的 pipeline 与当前交货报价；不观察当前/未来需求或未来报价。随机交货期允许跨单到货。所有边际为连续 Exponential(mean=100)，潜在 AR 系数不等于需求 Pearson 自相关。",
             "完整 self-evolve 的三个重复全部报告，不按测试成本选最好一轮；样本 SD 使用 n−1 分母。下表满足率为总销售量/总需求量。按训练成本选取的参考基线只有在七个族都完成时才用于 best-of-7 摘要，全部基线仍分别保留。",
             "95% 区间是单次比较的完整路径配对 bootstrap 区间，未作多重比较校正，不重采样单个 period。跨重复的区间先在每条路径上平均各冻结策略成本，再重采样路径，描述这些策略的平均表现，既不是实际组合策略，也不包含生成不确定性；生成差异另以三次样本 SD 展示。1,000 条测试路径不是 1,000 次独立 LLM 训练。", "",
             *_generation_quality_lines(quality),
             "## 需求诊断（仅训练集）", "", "![Training demand diagnostics](figures/dataset_diagnostics.png)", "",
             "需求分布及相关结构在查看策略测试收益前固定；不得因为某些环境没有赢而删除。", "",
             "## 主表：预热后 H=200", "", *_main_table(records, repeats, "steady"), "",
             "![Steady H200 cost comparison](figures/steady_h200.png)", "",
             "## 四个评价窗口", "", "![Horizon curves](figures/horizon_curves.png)", "",
             "曲线阴影为已完成生成重复之间的 ±1 样本 SD，不是路径抽样 CI。缺失重复不补值。若库存和需求都恰处稳态，stationary 策略的期望单位期成本不因 H 改变；有限样本和近似预热会造成曲线差异。", "",
             "另见[每个 horizon 单独重训的预注册扩展](horizon_refit.md)：仅 AR+ 固定交货期，训练 H=评价 H 的对角比较；扩展与本节固定策略的跨时域评价分开报告。", "",
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
    from matplotlib.ticker import NullLocator
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
        ax.set_xscale("log"); ax.set_xticks(HORIZONS, list(map(str, HORIZONS)))
        ax.xaxis.set_minor_locator(NullLocator()); ax.grid(alpha=.15)
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
    with (root / "tables" / "horizon_refit.csv").open(newline="") as handle:
        refit_rows = list(csv.DictReader(handle))
    fig, axs = plt.subplots(1, 2, figsize=(12, 5.8))
    for mode, ax in zip(("steady", "cold_start"), axs):
        for family in (*BASELINES, "self_evolve"):
            values = sorted((r for r in refit_rows if r["mode"] == mode and r["family"] == family and int(r["n_valid_repeats"]) > 0), key=lambda r: int(r["evaluation_horizon"]))
            if values:
                h = np.array([int(r["evaluation_horizon"]) for r in values])
                means = np.array([float(r["mean_cost_per_period_mean"]) for r in values])
                color = "black" if family == "self_evolve" else palette[family]
                ax.plot(h, means, "o-", color=color, linewidth=2 if family == "self_evolve" else 1.3, label=LABELS[family])
                if family == "self_evolve":
                    sd = np.array([float(r["mean_cost_per_period_sd"]) if r["mean_cost_per_period_sd"] else np.nan for r in values])
                    ax.fill_between(h, means-sd, means+sd, color="black", alpha=.12)
        ax.set(title="After B=500 burn-in" if mode == "steady" else "Cold start (same B=500-trained rules)",
               xlabel="Training horizon = evaluation horizon", ylabel="Mean cost per period")
        ax.set_xscale("log"); ax.set_xticks(HORIZONS, list(map(str, HORIZONS)))
        ax.xaxis.set_minor_locator(NullLocator()); ax.grid(alpha=.15)
        if not ax.lines:
            ax.text(.5, .5, "Diagonal evaluation pending", ha="center", transform=ax.transAxes, color="0.45")
    handles, labels = [], []
    for ax in axs:
        for handle, label in zip(*ax.get_legend_handles_labels()):
            if label not in labels:
                handles.append(handle); labels.append(label)
    if handles:
        fig.legend(handles, labels, loc="lower center", ncol=4, frameon=False, fontsize=9)
    fig.suptitle("Horizon refit | AR+ latent 0.8, fixed lead 6", fontsize=15, y=.98)
    fig.text(.5, .105, "A separately trained rule at each H. H=200 reuses primary runs. Shading: generated-repeat SD; no best-test selection.", ha="center", fontsize=9)
    fig.tight_layout(rect=(0, .145, 1, .93))
    fig.savefig(destination / "horizon_refit.png", dpi=180)
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
