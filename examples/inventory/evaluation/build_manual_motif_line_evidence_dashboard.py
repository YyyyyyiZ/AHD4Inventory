#!/usr/bin/env python3
"""Build a no-LLM, line-evidence dashboard for manual motif auditing.

This script does not use AST canonicalization.  It reads the sampled policy
files, extracts source-code evidence lines for each motif using deterministic
line rules, and writes a static HTML dashboard plus CSVs for audit.
"""

from __future__ import annotations

import argparse
import csv
import html
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Callable


TABLE_MOTIFS = [
    "inventory_position",
    "pipeline_weighting",
    "nonlinear_pipeline_composition",
    "order_up_to",
    "state_dependent_target",
    "partial_adjustment",
    "constant_order",
    "order_clipping",
    "order_smoothing",
]

EXTRA_MOTIFS = [
    "safety_stock_buffer",
    "pipeline_demand_proxy",
    "near_term_pipeline_focus",
    "threshold_order_activation",
    "integer_rounding",
    "emergency_or_shortage_boost",
    "nonlinear_gap_transform",
]

ALL_MOTIFS = TABLE_MOTIFS + EXTRA_MOTIFS


@dataclass(frozen=True)
class Evidence:
    motif: str
    reason: str
    line_numbers: tuple[int, ...]
    snippet: str


def rx(pattern: str) -> re.Pattern[str]:
    return re.compile(pattern, re.I)


def starts_code(line: str) -> bool:
    return line.lstrip().startswith("def compute_order_amount")


def code_body(policy_text: str) -> str:
    lines = policy_text.splitlines()
    for idx, line in enumerate(lines):
        if starts_code(line):
            return "\n".join(lines[idx:])
    return policy_text


def merge_line_numbers(*groups: list[int] | tuple[int, ...]) -> tuple[int, ...]:
    nums: set[int] = set()
    for group in groups:
        nums.update(group)
    return tuple(sorted(nums))


def is_comment_line(line: str) -> bool:
    return line.lstrip().startswith("#")


def expand_comment_code_blocks(
    lines: list[str],
    line_numbers: tuple[int, ...],
    *,
    max_code_lines: int = 10,
) -> tuple[int, ...]:
    """If evidence hits a comment, include the code block introduced by it.

    Many generated policies use descriptive comments such as
    "# Pattern recognition" immediately before the actual `if`/`for` block.
    For manual review the comment alone is weak evidence, so the dashboard
    expands such anchors to the following block deterministically.
    """

    expanded = set(line_numbers)
    n_lines = len(lines)
    for line_no in line_numbers:
        idx = line_no - 1
        if idx < 0 or idx >= n_lines or not is_comment_line(lines[idx]):
            continue

        j = idx + 1
        code_seen = False
        code_lines = 0
        while j < n_lines and code_lines < max_code_lines:
            stripped = lines[j].strip()
            current_no = j + 1
            if stripped == "":
                if code_seen:
                    break
                expanded.add(current_no)
                j += 1
                continue
            if stripped.startswith("#"):
                expanded.add(current_no)
                j += 1
                continue

            expanded.add(current_no)
            code_seen = True
            code_lines += 1
            j += 1

    return tuple(sorted(expanded))


def context_snippet(lines: list[str], line_numbers: tuple[int, ...], before: int = 1, after: int = 1) -> str:
    if not line_numbers:
        return ""
    ranges: list[tuple[int, int]] = []
    for num in line_numbers:
        start = max(1, num - before)
        end = min(len(lines), num + after)
        if ranges and start <= ranges[-1][1] + 1:
            ranges[-1] = (ranges[-1][0], max(ranges[-1][1], end))
        else:
            ranges.append((start, end))
    out: list[str] = []
    for start, end in ranges:
        for num in range(start, end + 1):
            out.append(f"L{num}: {lines[num - 1].rstrip()}")
        if (start, end) != ranges[-1]:
            out.append("...")
    return "\n".join(out)


def add_evidence(
    out: list[Evidence],
    motif: str,
    reason: str,
    lines: list[str],
    line_numbers: list[int] | tuple[int, ...],
    *,
    before: int = 1,
    after: int = 1,
) -> None:
    nums = tuple(sorted(set(line_numbers)))
    if not nums:
        return
    nums = expand_comment_code_blocks(lines, nums)
    key = (motif, reason, nums)
    if any((ev.motif, ev.reason, ev.line_numbers) == key for ev in out):
        return
    out.append(Evidence(motif=motif, reason=reason, line_numbers=nums, snippet=context_snippet(lines, nums, before, after)))


def line_matches(line: str, *patterns: str) -> bool:
    return all(re.search(pattern, line, re.I) for pattern in patterns)


def find_lines(lines: list[str], *patterns: str) -> list[int]:
    return [idx for idx, line in enumerate(lines, start=1) if line_matches(line, *patterns)]


def assignment_lhs(line: str) -> str | None:
    match = re.match(r"\s*([A-Za-z_][A-Za-z0-9_]*)\s*=", line)
    return match.group(1) if match else None


def find_definitions(lines: list[str], names: list[str], limit: int = 4) -> list[int]:
    wanted = {name for name in names if name}
    found: list[int] = []
    for idx, line in enumerate(lines, start=1):
        lhs = assignment_lhs(line)
        if lhs in wanted:
            found.append(idx)
            if len(found) >= limit:
                break
    return found


def nearby_definitions_for_line(lines: list[str], line_no: int, names: list[str]) -> list[int]:
    defs = find_definitions(lines[: max(0, line_no - 1)], names, limit=8)
    return defs[-4:]


def variable_names_in_expr(expr: str) -> list[str]:
    names = re.findall(r"\b[A-Za-z_][A-Za-z0-9_]*\b", expr)
    exclude = {"max", "min", "sum", "len", "int", "round", "range", "enumerate", "zip", "reversed", "abs"}
    return [name for name in names if name not in exclude]


def assignment_map(lines: list[str]) -> dict[str, str]:
    out: dict[str, str] = {}
    for line in lines:
        lhs = assignment_lhs(line)
        if lhs and "=" in line:
            out[lhs] = line.split("=", 1)[1]
    return out


def target_expr_is_state_dependent(target_name: str, defs: dict[str, str], depth: int = 0) -> bool:
    if depth > 3:
        return False
    rhs = defs.get(target_name, "")
    if not rhs:
        return False
    lower = rhs.lower()
    if re.search(
        r"pipeline|inventory|on_hand|demand|forecast|estimate|recent|lead_time|expected|effective_|weighted_|pattern|trend|urgency|coverage|risk",
        lower,
    ):
        return True
    return any(target_expr_is_state_dependent(name, defs, depth + 1) for name in variable_names_in_expr(rhs))


def positive_gap_uses_dynamic_target(line: str, defs: dict[str, str]) -> bool:
    target_names = [
        name
        for name in variable_names_in_expr(line)
        if re.search(r"(target|adjusted_base|dynamic_base|reorder)", name, re.I)
    ]
    return any(target_expr_is_state_dependent(name, defs) for name in target_names)


def evidence_inventory_position(lines: list[str]) -> list[Evidence]:
    out: list[Evidence] = []
    pipeline_signal_defs: dict[str, int] = {}
    for idx, line in enumerate(lines, start=1):
        lhs = assignment_lhs(line)
        if not lhs:
            continue
        lower = line.lower()
        if re.search(r"(effective_pipeline|weighted_pipeline|pipeline_sum|pipeline_inventory)", lhs, re.I) and re.search(
            r"pipeline_orders|sum\s*\(", lower
        ):
            pipeline_signal_defs[lhs] = idx
    for idx, line in enumerate(lines, start=1):
        lhs = assignment_lhs(line) or ""
        lower = line.lower()
        if line_matches(line, r"on_hand_inventory", r"sum\s*\(\s*pipeline_orders\s*\)") and (
            "+" in line or "-" in line
        ):
            add_evidence(out, "inventory_position", "explicit on-hand plus aggregate pipeline term", lines, [idx])
        elif line_matches(line, r"(inventory_position|net_inventory|projected_inventory)", r"pipeline_orders") and line_matches(
            line, r"on_hand_inventory|sum\s*\("
        ):
            add_evidence(out, "inventory_position", "inventory-position-like state variable", lines, [idx])
        elif re.search(r"(inventory_position|net_inventory|projected_inventory)", lhs, re.I) and "on_hand_inventory" in lower:
            used_pipeline_signals = [name for name in pipeline_signal_defs if re.search(rf"\b{re.escape(name)}\b", line)]
            if used_pipeline_signals:
                add_evidence(
                    out,
                    "inventory_position",
                    "on-hand plus previously defined effective/weighted pipeline signal",
                    lines,
                    merge_line_numbers([pipeline_signal_defs[name] for name in used_pipeline_signals], [idx]),
                )
    return out[:4]


def evidence_pipeline_weighting(lines: list[str]) -> list[Evidence]:
    out: list[Evidence] = []
    for idx, line in enumerate(lines, start=1):
        lower = line.lower()
        if re.search(r"\bweights?\s*=", lower):
            related = [idx]
            for j in range(idx + 1, min(len(lines), idx + 5) + 1):
                if re.search(r"weighted|zip\s*\(|enumerate\s*\(|pipeline_orders", lines[j - 1], re.I):
                    related.append(j)
            add_evidence(out, "pipeline_weighting", "explicit weight vector or weight schedule", lines, related)
        if re.search(r"(weighted_sum|weighted_pipeline|effective_pipeline|pipeline_weight)", lower) and re.search(
            r"pipeline|weight|discount", lower
        ):
            add_evidence(out, "pipeline_weighting", "pipeline term receives nonuniform/effective weight", lines, [idx])
        if re.search(r"for .* in .*pipeline_orders|zip\s*\(.*pipeline_orders|enumerate\s*\(.*pipeline_orders", lower) and re.search(
            r"\*|weight|discount", lower
        ):
            add_evidence(out, "pipeline_weighting", "pipeline loop/generator multiplies pipeline entries by coefficients", lines, [idx])
        if re.search(r"pipeline_orders\s*\[[^\]]+:[^\]]*\]", lower):
            add_evidence(out, "pipeline_weighting", "pipeline slice selects only part of the pipeline; review as implicit zero/one weights", lines, [idx])
        if re.search(r"(effective_pipeline|weighted_pipeline|pipeline_sum)\s*=.*sum\s*\(\s*pipeline_orders\s*\)\s*\*", lower):
            add_evidence(out, "pipeline_weighting", "aggregate pipeline multiplied by pipeline coefficient", lines, [idx])
    return out[:6]


def evidence_nonlinear_pipeline(lines: list[str]) -> list[Evidence]:
    out: list[Evidence] = []
    for idx, line in enumerate(lines, start=1):
        lower = line.lower()
        if re.search(r"\b(max|min)\s*\(\s*pipeline_orders\s*\)", lower):
            add_evidence(out, "nonlinear_pipeline_composition", "max/min over pipeline vector", lines, [idx])
        if re.search(r"(std|variance|var|median|percentile|variability)", lower) and "pipeline" in lower:
            add_evidence(out, "nonlinear_pipeline_composition", "pipeline variability/order-statistic term", lines, [idx])
        if "pipeline" in lower and re.search(r"\*\*|sqrt\s*\(|abs\s*\(", lower):
            add_evidence(out, "nonlinear_pipeline_composition", "nonlinear transform of pipeline-derived signal", lines, [idx])
        if "pipeline" in lower and "/" in lower and re.search(r"sum\s*\(|len\s*\(|ratio|coverage", lower):
            add_evidence(out, "nonlinear_pipeline_composition", "pipeline ratio or normalized pipeline statistic", lines, [idx])
        if re.search(r"pipeline_orders\s*\[[^\]]+\]\s*[<>]=?\s*pipeline_orders\s*\[[^\]]+\]", lower):
            add_evidence(out, "nonlinear_pipeline_composition", "pipeline trend/pattern comparison across positions", lines, [idx])
        if re.search(r"(trend|pattern|volatility|urgency|coverage).*pipeline", lower):
            add_evidence(out, "nonlinear_pipeline_composition", "pipeline pattern/urgency/coverage feature", lines, [idx])
    return out[:6]


def evidence_order_up_to(lines: list[str]) -> list[Evidence]:
    out: list[Evidence] = []
    gap_vars: list[tuple[int, str]] = []
    defs = assignment_map(lines)
    for idx, line in enumerate(lines, start=1):
        lhs = assignment_lhs(line) or ""
        lower = line.lower()
        if re.search(r"(max_order|order_cap|cap|upper|limit|min_order|minimum_order|floor|lower)", lhs, re.I):
            continue
        if re.search(r"(gap|target_order|raw_order|order_needed|order_amount|order_up_to)", lhs, re.I) and "-" in line and re.search(
            r"inventory|on_hand_inventory|net_inventory|projected_inventory", lower
        ):
            gap_vars.append((idx, lhs))
        if re.search(r"max\s*\(\s*0\s*,.*-.*(inventory|on_hand_inventory|net_inventory|projected_inventory)", lower) or re.search(
            r"max\s*\(.*-.*(inventory|on_hand_inventory|net_inventory|projected_inventory).*,\s*0\s*\)", lower
        ):
            if positive_gap_uses_dynamic_target(line, defs):
                continue
            deps = nearby_definitions_for_line(lines, idx, variable_names_in_expr(line))
            add_evidence(out, "order_up_to", "positive part of fixed target minus inventory signal", lines, merge_line_numbers(deps, [idx]))
    for idx, var in gap_vars:
        uses = [j for j, line in enumerate(lines, start=1) if j > idx and re.search(rf"max\s*\(\s*0\s*,\s*{re.escape(var)}\b|max\s*\(\s*{re.escape(var)}\b\s*,\s*0", line, re.I)]
        if uses:
            add_evidence(out, "order_up_to", "gap variable later converted to positive part", lines, [idx, uses[0]])
    return out[:6]


def evidence_state_dependent_target(lines: list[str]) -> list[Evidence]:
    out: list[Evidence] = []
    target_lhs = r"(target_position|target_inventory|target_level|adjusted_base_stock|adjusted_base|dynamic_base|reorder_point)"
    state_terms = r"(pipeline|inventory|demand|forecast|estimate|recent|lead_time|expected|safety)"
    for idx, line in enumerate(lines, start=1):
        lhs = assignment_lhs(line) or ""
        if re.search(target_lhs, lhs, re.I) and re.search(state_terms, line, re.I):
            deps = nearby_definitions_for_line(lines, idx, variable_names_in_expr(line))
            add_evidence(out, "state_dependent_target", "target level depends on state/proxy variables", lines, merge_line_numbers(deps, [idx]))
    return out[:5]


def evidence_partial_adjustment(lines: list[str]) -> list[Evidence]:
    out: list[Evidence] = []
    factors = r"(alpha|beta|gain|smoothing_factor|smooth_factor|adjustment_factor|fraction|partial|closure)"
    order_terms = r"(target_order|raw_order|order_needed|order_amount|gap)"
    for idx, line in enumerate(lines, start=1):
        lower = line.lower()
        if re.search(factors, lower) and re.search(order_terms, lower) and "*" in line:
            deps = nearby_definitions_for_line(lines, idx, variable_names_in_expr(line))
            add_evidence(out, "partial_adjustment", "multiplicative gain applied to order gap", lines, merge_line_numbers(deps, [idx]))
        elif re.search(factors, lower) and re.search(r"\*\s*max\s*\(|max\s*\(.*\)\s*\*", lower):
            add_evidence(out, "partial_adjustment", "gain multiplies positive-part order-up-to expression", lines, [idx])
    return out[:5]


def evidence_constant_order(lines: list[str]) -> list[Evidence]:
    out: list[Evidence] = []
    for idx, line in enumerate(lines, start=1):
        if re.search(r"(baseline_order|constant_order|fixed_order)", line, re.I):
            add_evidence(out, "constant_order", "explicit baseline/constant/fixed order term", lines, [idx])
    return out[:4]


def is_positive_part_line(line: str) -> bool:
    lower = line.lower()
    return bool(
        re.search(r"max\s*\(\s*0\s*,.*-.*(inventory|gap|order)", lower)
        or re.search(r"max\s*\(.*-.*(inventory|gap|order).*,\s*0\s*\)", lower)
    )


def evidence_order_clipping(lines: list[str]) -> list[Evidence]:
    out: list[Evidence] = []
    bound_names: list[str] = []
    for idx, line in enumerate(lines, start=1):
        lhs = assignment_lhs(line)
        if lhs and re.search(r"(max_order|order_cap|cap|upper|limit|min_order|minimum_order|floor|lower)", lhs, re.I):
            bound_names.append(lhs)
    bound_defs = find_definitions(lines, bound_names)
    for idx, line in enumerate(lines, start=1):
        lower = line.lower()
        if "len(pipeline_orders)" in lower and re.search(r"min\s*\(\s*\d+\s*,\s*len\s*\(", lower):
            continue
        if is_positive_part_line(line):
            continue
        if re.search(r"\b(min|max)\s*\(", lower) and re.search(r"(max_order|order_cap|cap|limit|min_order|minimum_order|floor|order_amount|target_order)", lower):
            add_evidence(out, "order_clipping", "min/max bound applied to an order quantity", lines, merge_line_numbers(bound_defs, [idx]))
        if re.search(r"\bif\b.*order.*[<>].*(max_order|order_cap|cap|limit|min_order|minimum_order|floor|\d+)", lower):
            branch = [idx]
            for j in range(idx + 1, min(len(lines), idx + 3) + 1):
                if re.search(r"order", lines[j - 1], re.I):
                    branch.append(j)
            add_evidence(out, "order_clipping", "conditional order cap/floor", lines, merge_line_numbers(bound_defs, branch))
    return out[:6]


def evidence_order_smoothing(lines: list[str]) -> list[Evidence]:
    out: list[Evidence] = []
    for idx, line in enumerate(lines, start=1):
        lower = line.lower()
        if re.search(r"(previous_order|prev_order|last_order|prior_order|pipeline_orders\s*\[\s*-1\s*\])", lower):
            related = [idx]
            for j in range(idx + 1, min(len(lines), idx + 5) + 1):
                if re.search(r"smooth|smoothing|beta|blend|delta|previous_order|last_order|\(1\s*-", lines[j - 1], re.I):
                    related.append(j)
            if len(related) > 1 or re.search(r"smooth|beta|blend|delta", lower):
                add_evidence(out, "order_smoothing", "current order blended or limited using previous/last order", lines, related)
    return out[:5]


def evidence_safety_stock(lines: list[str]) -> list[Evidence]:
    out: list[Evidence] = []
    for idx, line in enumerate(lines, start=1):
        if re.search(r"(safety_stock|safety_buffer|buffer)", line, re.I):
            add_evidence(out, "safety_stock_buffer", "explicit safety stock or buffer variable", lines, [idx])
    return out[:4]


def evidence_pipeline_demand_proxy(lines: list[str]) -> list[Evidence]:
    out: list[Evidence] = []
    demand_lhs = r"(demand_estimate|demand_forecast|expected_demand|forecast_demand|avg_recent_demand|recent_demand|lead_time_demand|anticipated_demand|demand_adjustment|pattern_adjusted_demand|avg_weighted_demand)"
    pipeline_proxy_terms = r"(pipeline_orders|effective_pipeline|weighted_pipeline|recent_arrivals|avg_weighted_demand|pattern_adjusted_demand|lead_time|L\b|sum\s*\(|len\s*\()"
    for idx, line in enumerate(lines, start=1):
        lhs = assignment_lhs(line) or ""
        lower = line.lower()
        if re.search(demand_lhs, lhs, re.I) and re.search(pipeline_proxy_terms, lower):
            deps = nearby_definitions_for_line(lines, idx, variable_names_in_expr(line))
            add_evidence(out, "pipeline_demand_proxy", "demand proxy estimated from pipeline/history variables", lines, merge_line_numbers(deps, [idx]))
        elif re.search(r"lead_time\s*=\s*len\s*\(\s*pipeline_orders\s*\)", lower):
            add_evidence(out, "pipeline_demand_proxy", "lead-time proxy from pipeline length", lines, [idx])
    return out[:5]


def evidence_near_term_pipeline(lines: list[str]) -> list[Evidence]:
    out: list[Evidence] = []
    for idx, line in enumerate(lines, start=1):
        lower = line.lower()
        if re.search(r"pipeline_orders\s*\[\s*0\s*\]|pipeline_orders\s*\[\s*:[^\]]*\]|pipeline_orders\s*\[[^:]+:[^\]]*\]|recent_arrivals|recent_orders|immediate_arrival|near_pipeline", lower):
            add_evidence(out, "near_term_pipeline_focus", "uses near-arrival slice/index of pipeline", lines, [idx])
    return out[:5]


def evidence_threshold(lines: list[str]) -> list[Evidence]:
    out: list[Evidence] = []
    for idx, line in enumerate(lines, start=1):
        lower = line.lower()
        if re.search(r"\bif\b", lower) and re.search(
            r"threshold|reorder|critical|emergency|min_order|minimum_order|max_order|cap|coverage|shortage|low_inventory", lower
        ):
            branch = [idx]
            for j in range(idx + 1, min(len(lines), idx + 3) + 1):
                if re.search(r"order|return|boost|adjust|multiplier", lines[j - 1], re.I):
                    branch.append(j)
            add_evidence(out, "threshold_order_activation", "conditional threshold changes order action", lines, branch)
    return out[:5]


def evidence_integer_rounding(lines: list[str]) -> list[Evidence]:
    out: list[Evidence] = []
    for idx, line in enumerate(lines, start=1):
        if re.search(r"\b(int|round|ceil|floor)\s*\(", line):
            add_evidence(out, "integer_rounding", "order quantity integerization/rounding", lines, [idx])
    return out[:4]


def evidence_emergency(lines: list[str]) -> list[Evidence]:
    out: list[Evidence] = []
    for idx, line in enumerate(lines, start=1):
        if re.search(r"emergency|shortage|critical|low_inventory|stockout|aggressive", line, re.I):
            add_evidence(out, "emergency_or_shortage_boost", "emergency/shortage/critical-state order boost", lines, [idx])
    return out[:4]


def evidence_nonlinear_gap(lines: list[str]) -> list[Evidence]:
    out: list[Evidence] = []
    for idx, line in enumerate(lines, start=1):
        lower = line.lower()
        if re.search(r"(gap|raw_order|order_needed|target_order|order_amount).*(\*\*|sqrt\s*\(|log\s*\(|exp\s*\()", lower):
            add_evidence(out, "nonlinear_gap_transform", "nonlinear transform applied to order gap/order signal", lines, [idx])
    return out[:4]


EVIDENCE_FUNCS: dict[str, Callable[[list[str]], list[Evidence]]] = {
    "inventory_position": evidence_inventory_position,
    "pipeline_weighting": evidence_pipeline_weighting,
    "nonlinear_pipeline_composition": evidence_nonlinear_pipeline,
    "order_up_to": evidence_order_up_to,
    "state_dependent_target": evidence_state_dependent_target,
    "partial_adjustment": evidence_partial_adjustment,
    "constant_order": evidence_constant_order,
    "order_clipping": evidence_order_clipping,
    "order_smoothing": evidence_order_smoothing,
    "safety_stock_buffer": evidence_safety_stock,
    "pipeline_demand_proxy": evidence_pipeline_demand_proxy,
    "near_term_pipeline_focus": evidence_near_term_pipeline,
    "threshold_order_activation": evidence_threshold,
    "integer_rounding": evidence_integer_rounding,
    "emergency_or_shortage_boost": evidence_emergency,
    "nonlinear_gap_transform": evidence_nonlinear_gap,
}


def load_samples(sample_dir: Path) -> list[dict[str, str]]:
    path = sample_dir / "sample_100_policy_motif_labels.csv"
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def write_csv(path: Path, rows: list[dict[str, str | int]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        return
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def build_evidence_rows(sample_dir: Path, samples: list[dict[str, str]]) -> tuple[list[dict[str, str]], dict[str, dict[str, list[Evidence]]]]:
    rows: list[dict[str, str]] = []
    evidence_by_sample: dict[str, dict[str, list[Evidence]]] = {}
    for sample in samples:
        policy_path = sample_dir / sample["policy_file"]
        code = code_body(policy_path.read_text(encoding="utf-8"))
        lines = code.splitlines()
        evidence_by_sample[sample["sample_id"]] = {}
        for motif in ALL_MOTIFS:
            evidence = EVIDENCE_FUNCS[motif](lines)
            evidence_by_sample[sample["sample_id"]][motif] = evidence
            label = sample.get(motif) == "True"
            has_evidence = bool(evidence)
            if label and has_evidence:
                status = "label_true_with_evidence"
            elif label and not has_evidence:
                status = "label_true_no_evidence"
            elif (not label) and has_evidence:
                status = "label_false_candidate_evidence"
            else:
                status = "label_false_no_evidence"
            rows.append(
                {
                    "sample_id": sample["sample_id"],
                    "policy_file": sample["policy_file"],
                    "distribution": sample["distribution"],
                    "motif": motif,
                    "label": str(label),
                    "has_line_evidence": str(has_evidence),
                    "status": status,
                    "evidence_reasons": " | ".join(ev.reason for ev in evidence),
                    "evidence_line_numbers": " | ".join(",".join(str(num) for num in ev.line_numbers) for ev in evidence),
                    "evidence_snippets": "\n---\n".join(ev.snippet for ev in evidence),
                }
            )
    return rows, evidence_by_sample


def build_summary_rows(evidence_rows: list[dict[str, str]]) -> list[dict[str, str | int]]:
    by_motif: dict[str, list[dict[str, str]]] = {motif: [] for motif in ALL_MOTIFS}
    for row in evidence_rows:
        by_motif[row["motif"]].append(row)
    rows: list[dict[str, str | int]] = []
    for motif, group in by_motif.items():
        positives = [row for row in group if row["label"] == "True"]
        negatives = [row for row in group if row["label"] == "False"]
        rows.append(
            {
                "motif": motif,
                "label_true": len(positives),
                "label_true_with_evidence": sum(row["status"] == "label_true_with_evidence" for row in group),
                "label_true_no_evidence": sum(row["status"] == "label_true_no_evidence" for row in group),
                "label_false": len(negatives),
                "label_false_candidate_evidence": sum(row["status"] == "label_false_candidate_evidence" for row in group),
            }
        )
    return rows


def motif_badge(motif: str, label: bool, evidence: list[Evidence]) -> str:
    if label and evidence:
        cls = "ok"
        text = f"{motif}: True"
    elif label and not evidence:
        cls = "missing"
        text = f"{motif}: True"
    elif (not label) and evidence:
        cls = "candidate"
        text = f"{motif}: False?"
    else:
        cls = "off"
        text = f"{motif}: False"
    return f'<span class="badge {cls}" data-motif="{html.escape(motif)}">{html.escape(text)}</span>'


def evidence_html(evidence: list[Evidence]) -> str:
    if not evidence:
        return "<p class='muted'>No deterministic evidence line extracted.</p>"
    blocks = []
    for ev in evidence:
        blocks.append(
            f"<div class='ev'><div class='reason'>{html.escape(ev.reason)}</div><pre>{html.escape(ev.snippet)}</pre></div>"
        )
    return "\n".join(blocks)


def render_dashboard(
    sample_dir: Path,
    samples: list[dict[str, str]],
    evidence_by_sample: dict[str, dict[str, list[Evidence]]],
) -> str:
    motif_options = "\n".join(f'<option value="{html.escape(m)}">{html.escape(m)}</option>' for m in ALL_MOTIFS)
    cards = []
    for sample in samples:
        sample_id = sample["sample_id"]
        policy_path = sample_dir / sample["policy_file"]
        code = code_body(policy_path.read_text(encoding="utf-8"))
        evidence_map = evidence_by_sample[sample_id]
        true_motifs = [motif for motif in ALL_MOTIFS if sample.get(motif) == "True"]
        missing = [motif for motif in ALL_MOTIFS if sample.get(motif) == "True" and not evidence_map[motif]]
        candidates = [motif for motif in ALL_MOTIFS if sample.get(motif) != "True" and evidence_map[motif]]
        false_no_evidence = [motif for motif in ALL_MOTIFS if sample.get(motif) != "True" and not evidence_map[motif]]
        data = {
            "sample": sample_id,
            "distribution": sample["distribution"],
            "top10": sample.get("is_top10_by_distribution", "False"),
            "final": sample.get("is_final_generation", "False"),
            "motifs": true_motifs,
            "missing": missing,
            "candidates": candidates,
            "falseNoEvidence": false_no_evidence,
        }
        motif_sections = []
        for motif in ALL_MOTIFS:
            label = sample.get(motif) == "True"
            evidence = evidence_map[motif]
            if label and evidence:
                status = "label=True, evidence found"
                status_cls = "ok-text"
            elif label:
                status = "label=True, no evidence line"
                status_cls = "missing-text"
            elif evidence:
                status = "label=False, candidate evidence"
                status_cls = "candidate-text"
            else:
                status = "label=False, no evidence line"
                status_cls = "muted"
            motif_sections.append(
                f"""
<details class="motif-detail" data-motif="{html.escape(motif)}" open>
  <summary><b>{html.escape(motif)}</b> <span class="{status_cls}">{html.escape(status)}</span></summary>
  {evidence_html(evidence)}
</details>
"""
            )
        badges = "\n".join(motif_badge(motif, sample.get(motif) == "True", evidence_map[motif]) for motif in ALL_MOTIFS)
        cards.append(
            f"""
<section class="card" data-record='{html.escape(json.dumps(data, sort_keys=True))}'>
  <div class="card-head">
    <div>
      <h2>Sample {html.escape(sample_id)}</h2>
      <p>{html.escape(sample["distribution"])} · gen {html.escape(sample["generation"])} · rank {html.escape(sample["rank_in_population_file"])} · objective {html.escape(sample["objective"])}</p>
      <p class="path">{html.escape(sample["policy_file"])}</p>
    </div>
    <div class="flags">
      <span>top10: {html.escape(sample.get("is_top10_by_distribution", ""))}</span>
      <span>final: {html.escape(sample.get("is_final_generation", ""))}</span>
      <span class="missing-text">missing evidence: {len(missing)}</span>
      <span class="candidate-text">candidate FN: {len(candidates)}</span>
    </div>
  </div>
  <div class="badges">{badges}</div>
  <div class="layout">
    <div class="evidence-pane">
      <p class="focus-empty muted">Select one or more motifs to show labels and evidence for this policy.</p>
      {''.join(motif_sections)}
    </div>
    <details class="code-pane">
      <summary>Full policy code</summary>
      <pre>{html.escape(code)}</pre>
    </details>
  </div>
</section>
"""
        )
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Line Evidence Motif Audit</title>
<style>
body {{ margin: 0; font: 14px/1.45 -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; color: #1f2933; background: #f6f8fb; }}
header {{ position: sticky; top: 0; z-index: 10; padding: 16px 20px; background: #fff; border-bottom: 1px solid #d6dde8; }}
h1 {{ margin: 0 0 10px; font-size: 22px; }}
.controls {{ display: flex; flex-wrap: wrap; gap: 10px; align-items: center; }}
select, input, button {{ font: inherit; padding: 7px 9px; border: 1px solid #c8d0dc; border-radius: 6px; background: #fff; }}
button {{ cursor: pointer; }}
.control-stack {{ display: flex; flex-direction: column; gap: 4px; }}
.control-row {{ display: flex; gap: 8px; align-items: center; }}
.motif-select {{ min-width: 290px; height: 142px; }}
.hint {{ color: #697586; font-size: 12px; }}
main {{ padding: 16px 20px 36px; }}
.legend {{ color: #52606d; margin-bottom: 12px; }}
.card {{ background: #fff; border: 1px solid #d6dde8; border-radius: 8px; margin: 12px 0; padding: 14px; }}
.card-head {{ display: flex; justify-content: space-between; gap: 12px; }}
h2 {{ margin: 0; font-size: 17px; }}
p {{ margin: 3px 0; color: #52606d; }}
.path {{ font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: 12px; }}
.flags {{ display: flex; flex-direction: column; align-items: flex-end; gap: 4px; white-space: nowrap; }}
.badges {{ display: flex; flex-wrap: wrap; gap: 6px; margin: 10px 0; }}
.badge {{ display: inline-block; padding: 3px 7px; border-radius: 999px; font-size: 12px; border: 1px solid transparent; }}
.badge.ok {{ background: #e7f5ec; color: #14532d; border-color: #b7e4c7; }}
.badge.missing {{ background: #fff0f0; color: #991b1b; border-color: #fecaca; }}
.badge.candidate {{ background: #fff7df; color: #854d0e; border-color: #fde68a; }}
.badge.off {{ background: #eef1f5; color: #52606d; }}
.ok-text {{ color: #166534; }}
.missing-text {{ color: #b91c1c; }}
.candidate-text {{ color: #a16207; }}
.layout {{ display: grid; grid-template-columns: minmax(420px, 1fr) minmax(420px, 1fr); gap: 14px; }}
.motif-detail {{ border-top: 1px solid #edf1f5; padding: 7px 0; }}
.motif-detail summary {{ cursor: pointer; }}
.ev {{ margin: 7px 0 10px; }}
.reason {{ font-weight: 600; margin-bottom: 4px; color: #334e68; }}
.muted {{ color: #7b8794; }}
pre {{ margin: 0; overflow: auto; max-height: 380px; padding: 10px; background: #111827; color: #e5e7eb; border-radius: 6px; font-size: 12px; line-height: 1.4; }}
.code-pane > summary {{ cursor: pointer; font-weight: 600; margin-bottom: 8px; }}
.hidden {{ display: none; }}
@media (max-width: 1050px) {{ .layout {{ grid-template-columns: 1fr; }} .card-head {{ flex-direction: column; }} .flags {{ align-items: flex-start; }} }}
</style>
</head>
<body>
<header>
  <h1>Line Evidence Motif Audit</h1>
  <div class="controls">
    <div class="control-stack">
      <label for="motifs">Motifs</label>
      <select id="motifs" class="motif-select" multiple size="8">{motif_options}</select>
      <span class="hint">Hold Cmd/Ctrl or Shift to select multiple.</span>
    </div>
    <div class="control-stack">
      <label for="motifMatch">Motif match</label>
      <select id="motifMatch"><option value="any">Any selected</option><option value="all">All selected</option></select>
      <label><input type="checkbox" id="filterByMotifs"> filter policies by selected motifs</label>
      <button id="clearMotifs" type="button">Clear motifs</button>
    </div>
    <label>Status <select id="status"><option value="">Any</option><option value="missing">label=True no evidence</option><option value="candidate">label=False candidate evidence</option><option value="positive">label=True</option></select></label>
    <label>Distribution <input id="dist" placeholder="e.g. poisson"></label>
    <label><input type="checkbox" id="top10"> top10 only</label>
    <label><input type="checkbox" id="final"> final only</label>
    <button id="reset">Reset</button>
  </div>
</header>
<main>
  <div class="legend"><span id="shown"></span> shown out of {len(samples)} samples. Select motifs to display only those labels inside each policy. Green = label True with evidence. Red = label True without extracted evidence. Yellow = label False with candidate evidence. Gray = label False.</div>
  {''.join(cards)}
</main>
<script>
const cards = [...document.querySelectorAll('.card')];
function applyFilters() {{
  const selectedMotifs = [...document.querySelector('#motifs').selectedOptions].map(option => option.value);
  const motifMatch = document.querySelector('#motifMatch').value;
  const filterByMotifs = document.querySelector('#filterByMotifs').checked;
  const status = document.querySelector('#status').value;
  const dist = document.querySelector('#dist').value.toLowerCase();
  const top10 = document.querySelector('#top10').checked;
  const finalOnly = document.querySelector('#final').checked;
  let shown = 0;
  for (const card of cards) {{
    const data = JSON.parse(card.dataset.record);
    const visibleMotifs = new Set([...data.motifs, ...data.candidates, ...data.missing]);
    const okMotif = !filterByMotifs || selectedMotifs.length === 0
      || (motifMatch === "all"
        ? selectedMotifs.every(motif => visibleMotifs.has(motif))
        : selectedMotifs.some(motif => visibleMotifs.has(motif)));
    const okDist = !dist || data.distribution.toLowerCase().includes(dist);
    const okTop = !top10 || data.top10 === "True";
    const okFinal = !finalOnly || data.final === "True";
    let okStatus = true;
    const hasStatusInFocus = (items) => selectedMotifs.length === 0
      ? items.length > 0
      : selectedMotifs.some(motif => items.includes(motif));
    if (status === "missing") okStatus = hasStatusInFocus(data.missing);
    if (status === "candidate") okStatus = hasStatusInFocus(data.candidates);
    if (status === "positive") okStatus = hasStatusInFocus(data.motifs);
    const visible = okMotif && okDist && okTop && okFinal && okStatus;
    card.classList.toggle('hidden', !visible);
    const focusSet = new Set(selectedMotifs);
    for (const motifNode of card.querySelectorAll('[data-motif]')) {{
      const showMotif = selectedMotifs.length > 0 && focusSet.has(motifNode.dataset.motif);
      motifNode.classList.toggle('hidden', !showMotif);
    }}
    const emptyMessage = card.querySelector('.focus-empty');
    if (emptyMessage) emptyMessage.classList.toggle('hidden', selectedMotifs.length > 0);
    if (visible) shown += 1;
  }}
  document.querySelector('#shown').textContent = shown;
}}
for (const el of document.querySelectorAll('select,input')) el.addEventListener('input', applyFilters);
document.querySelector('#clearMotifs').addEventListener('click', () => {{
  for (const option of document.querySelector('#motifs').options) option.selected = false;
  document.querySelector('#filterByMotifs').checked = false;
  applyFilters();
}});
document.querySelector('#reset').addEventListener('click', () => {{
  for (const option of document.querySelector('#motifs').options) option.selected = false;
  document.querySelector('#motifMatch').value = 'any';
  document.querySelector('#filterByMotifs').checked = false;
  document.querySelector('#status').value = '';
  document.querySelector('#dist').value = '';
  document.querySelector('#top10').checked = false;
  document.querySelector('#final').checked = false;
  applyFilters();
}});
applyFilters();
</script>
</body>
</html>
"""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("sample_dir", type=Path)
    args = parser.parse_args()
    sample_dir = args.sample_dir.resolve()
    out_dir = sample_dir / "review_dashboard"
    out_dir.mkdir(parents=True, exist_ok=True)

    samples = load_samples(sample_dir)
    evidence_rows, evidence_by_sample = build_evidence_rows(sample_dir, samples)
    summary_rows = build_summary_rows(evidence_rows)
    write_csv(out_dir / "line_evidence_by_sample_motif.csv", evidence_rows)
    write_csv(out_dir / "line_evidence_quality_summary.csv", summary_rows)
    (out_dir / "review_dashboard.html").write_text(render_dashboard(sample_dir, samples, evidence_by_sample), encoding="utf-8")
    print(f"samples,{len(samples)}")
    print(f"line_evidence_csv,{out_dir / 'line_evidence_by_sample_motif.csv'}")
    print(f"summary_csv,{out_dir / 'line_evidence_quality_summary.csv'}")
    print(f"dashboard,{out_dir / 'review_dashboard.html'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
