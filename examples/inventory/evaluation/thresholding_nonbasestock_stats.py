#!/usr/bin/env python3
"""Thresholding motif rate among non-base-stock matched policies."""

from __future__ import annotations

import ast
import csv
import importlib.util
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
MINING_SCRIPT = ROOT / "examples" / "inventory" / "evaluation" / "mine_specific_inventory_motifs.py"
OUT_DIR = ROOT / "examples" / "inventory" / "evaluation" / "thresholding_nonbasestock"
OUT_LABELS = OUT_DIR / "thresholding_nonbasestock_policy_labels.csv"
OUT_SUMMARY = OUT_DIR / "thresholding_nonbasestock_summary.csv"
OUT_EXAMPLES = OUT_DIR / "thresholding_nonbasestock_examples.csv"

STATE_NAMES = {
    "on_hand_inventory",
    "inventory",
    "current_inventory",
    "inventory_position",
    "effective_inventory",
    "net_inventory",
    "gap",
    "inventory_gap",
    "raw_order",
    "shortage",
    "coverage",
}
PIPE_NAMES = {"pipeline_orders", "pipeline", "pipeline_vector", "Q_t", "Q"}
ORDER_LIKE = ("order", "amount", "replenish", "quantity", "raw_order", "final_order")
COMPONENT_LIKE = ("boost", "extra", "adjustment", "multiplier", "factor", "gap", "signal")
EXPLICIT_THRESHOLD_TOKENS = (
    "threshold",
    "reorder_point",
    "critical",
    "emergency",
    "coverage",
    "shortage",
    "min_order",
    "minimum_order",
    "max_order",
    "cap",
)


def load_mining_module():
    spec = importlib.util.spec_from_file_location("motif_mining", MINING_SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def bool_int(value: bool) -> int:
    return 1 if value else 0


def normalize(code: str) -> str:
    try:
        return ast.unparse(ast.parse(code))
    except Exception:
        return code


def is_zero_expr(node: ast.AST | None) -> bool:
    if node is None:
        return True
    if isinstance(node, ast.Constant):
        return node.value in {0, 0.0, None, False}
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        return isinstance(node.operand, ast.Constant) and node.operand.value == 0
    return False


def is_nonzero_expr(node: ast.AST | None) -> bool:
    return node is not None and not is_zero_expr(node)


class StateVisitor(ast.NodeVisitor):
    def __init__(self, deps: dict[str, bool]) -> None:
        self.deps = deps
        self.state = False

    def visit_Name(self, node: ast.Name) -> None:
        if node.id in STATE_NAMES or node.id in PIPE_NAMES:
            self.state = True
        if self.deps.get(node.id, False):
            self.state = True

    def visit_Subscript(self, node: ast.Subscript) -> None:
        if isinstance(node.value, ast.Name) and node.value.id in PIPE_NAMES:
            self.state = True
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        if isinstance(node.func, ast.Name):
            name = node.func.id
        elif isinstance(node.func, ast.Attribute):
            name = node.func.attr
        else:
            name = ""
        if name in {"sum", "len", "max", "min", "mean", "std"}:
            for arg in node.args:
                if isinstance(arg, ast.Name) and arg.id in PIPE_NAMES:
                    self.state = True
        self.generic_visit(node)


def depends_on_state(node: ast.AST, deps: dict[str, bool]) -> bool:
    visitor = StateVisitor(deps)
    visitor.visit(node)
    return visitor.state


def condition_is_threshold(node: ast.AST, deps: dict[str, bool]) -> bool:
    if isinstance(node, ast.Compare):
        if not depends_on_state(node, deps):
            return False
        if not any(isinstance(op, (ast.Lt, ast.LtE, ast.Gt, ast.GtE)) for op in node.ops):
            return False
        text = ast.unparse(node).lower()
        if re.fullmatch(r"len\(\s*pipeline_orders\s*\)\s*[<>=!]+\s*\d+", text):
            return False
        # Ordinary non-negativity gates such as "raw_order > 0" are just max(0, gap)
        # written as an if/else. Count only explicit thresholds or non-zero constants.
        if re.fullmatch(r"(raw_order|target_order|gap|inventory_gap)\s*>\s*0(?:\.0)?", text):
            return False
        if any(token in text for token in EXPLICIT_THRESHOLD_TOKENS):
            return True
        numeric_constants = []
        if isinstance(node.left, ast.Constant) and isinstance(node.left.value, (int, float)):
            numeric_constants.append(node.left.value)
        for comparator in node.comparators:
            if isinstance(comparator, ast.Constant) and isinstance(comparator.value, (int, float)):
                numeric_constants.append(comparator.value)
        return any(abs(float(value)) > 1e-9 for value in numeric_constants)
    if isinstance(node, ast.BoolOp):
        return any(condition_is_threshold(value, deps) for value in node.values)
    if isinstance(node, ast.UnaryOp):
        return condition_is_threshold(node.operand, deps)
    return False


def target_name(name: str) -> bool:
    lowered = name.lower()
    if lowered in {"recent_orders", "pipeline_orders", "orders"}:
        return False
    return (
        lowered in {"order_amount", "raw_order", "target_order", "final_order", "order_qty", "order_quantity"}
        or any(token in lowered for token in COMPONENT_LIKE)
    )


def branch_effects(stmts: list[ast.stmt], deps: dict[str, bool]) -> list[ast.AST | None]:
    effects: list[ast.AST | None] = []
    for stmt in stmts:
        if isinstance(stmt, ast.Return):
            effects.append(stmt.value)
        elif isinstance(stmt, ast.Assign):
            names = [target.id for target in stmt.targets if isinstance(target, ast.Name)]
            if any(target_name(name) for name in names):
                effects.append(stmt.value)
        elif isinstance(stmt, ast.AugAssign) and isinstance(stmt.target, ast.Name):
            if target_name(stmt.target.id):
                effects.append(stmt.value)
        elif isinstance(stmt, ast.If):
            effects.extend(branch_effects(stmt.body, deps))
            effects.extend(branch_effects(stmt.orelse, deps))
    return effects


def if_node_gates_order(node: ast.If, deps: dict[str, bool]) -> bool:
    if not condition_is_threshold(node.test, deps):
        return False
    body = branch_effects(node.body, deps)
    orelse = branch_effects(node.orelse, deps)
    if not body or not orelse:
        # if condition: component = positive; no else often means else remains zero only when the
        # variable was initialized to zero immediately before. This conservative script does not infer that.
        return False
    body_nonzero = any(is_nonzero_expr(expr) for expr in body)
    else_nonzero = any(is_nonzero_expr(expr) for expr in orelse)
    body_zero = any(is_zero_expr(expr) for expr in body)
    else_zero = any(is_zero_expr(expr) for expr in orelse)
    return (body_nonzero and else_zero) or (else_nonzero and body_zero)


def ifexp_gates_order(node: ast.IfExp, deps: dict[str, bool]) -> bool:
    return condition_is_threshold(node.test, deps) and (
        (is_zero_expr(node.body) and is_nonzero_expr(node.orelse))
        or (is_zero_expr(node.orelse) and is_nonzero_expr(node.body))
    )


def compare_multiplier_gates_order(node: ast.BinOp, deps: dict[str, bool]) -> bool:
    if not isinstance(node.op, ast.Mult):
        return False
    return condition_is_threshold(node.left, deps) or condition_is_threshold(node.right, deps)


def detect_thresholding(code: str) -> bool:
    try:
        tree = ast.parse(normalize(code))
    except SyntaxError:
        return False

    deps: dict[str, bool] = {}
    thresholding = False

    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            state_dep = depends_on_state(node.value, deps)
            for target in node.targets:
                if isinstance(target, ast.Name):
                    deps[target.id] = state_dep
        elif isinstance(node, ast.AugAssign) and isinstance(node.target, ast.Name):
            deps[node.target.id] = deps.get(node.target.id, False) or depends_on_state(node.value, deps)

    for node in ast.walk(tree):
        if isinstance(node, ast.If) and if_node_gates_order(node, deps):
            thresholding = True
        elif isinstance(node, ast.IfExp) and ifexp_gates_order(node, deps):
            thresholding = True
        elif isinstance(node, ast.BinOp) and compare_multiplier_gates_order(node, deps):
            thresholding = True
    return thresholding


def has_base_stock_gap(code: str) -> bool:
    compact = re.sub(r"\s+", " ", normalize(code))
    lower = compact.lower()
    direct = re.search(
        r"max\s*\(\s*0(?:\.0)?\s*,\s*[^)]*(?:base_stock|target_level|desired_level|safety_stock)[^)]*"
        r"(?:-\s*on_hand_inventory\s*-\s*sum\s*\(\s*pipeline_orders\s*\)|-\s*inventory_position)",
        compact,
        flags=re.I,
    )
    return bool(direct) or (
        "inventory_position = on_hand_inventory + sum(pipeline_orders)" in lower
        and re.search(r"max\s*\(\s*0(?:\.0)?\s*,\s*[^)]*-\s*inventory_position", compact, flags=re.I)
        is not None
    )


def classify_base_stock_form(code: str, mining_module: Any, thresholding: bool) -> bool:
    """Fixed order-up-to form, allowing safety stock and rounding only."""
    if not has_base_stock_gap(code):
        return False
    broad = mining_module.detect_broad_motifs(normalize(code))
    specific = mining_module.detect_specific_motifs(normalize(code))
    disqualifiers = [
        thresholding,
        broad["dynamic_target"],
        broad["pipeline_composition"],
        broad["order_inertia"],
        specific["fractional_gap_closure"],
        specific["absolute_order_cap"],
        specific["order_floor_or_baseline"],
        specific["pipeline_total_discount"],
        specific["pipeline_average_demand_proxy"],
        specific["near_term_pipeline_slice"],
        specific["near_far_pipeline_split"],
        specific["weighted_pipeline_vector"],
        specific["nonlinear_transform"],
        specific["pipeline_extreme_or_dispersion"],
        specific["coverage_ratio_signal"],
        specific["low_stock_emergency_boost"],
    ]
    return not any(disqualifiers)


def excerpt_for_threshold(code: str) -> str:
    lines = normalize(code).splitlines()
    preferred = re.compile(
        r"^\s*if\b.*("
        r"threshold|min_order|minimum_order|max_order|cap|coverage|shortage|emergency|critical|"
        r">\s*[1-9]\d*(?:\.\d+)?|<\s*[1-9]\d*(?:\.\d+)?)",
        flags=re.I,
    )
    for idx, line in enumerate(lines):
        if preferred.search(line):
            start = max(0, idx - 2)
            end = min(len(lines), idx + 6)
            return "\\n".join(lines[start:end])[:900]
    for idx, line in enumerate(lines):
        lowered = line.lower()
        if lowered.strip().startswith("if ") and any(op in line for op in [">", "<", ">=", "<="]):
            start = max(0, idx - 2)
            end = min(len(lines), idx + 6)
            return "\\n".join(lines[start:end])[:900]
    return "\\n".join(lines[:10])[:900]


def main() -> int:
    mining_module = load_mining_module()
    policies = mining_module.load_combined_matched_unique_policies()

    rows: list[dict[str, Any]] = []
    examples: list[dict[str, Any]] = []
    for policy in policies.values():
        code = policy["code"]
        thresholding = detect_thresholding(code)
        base_stock_form = classify_base_stock_form(code, mining_module, thresholding)
        row = {
            "policy_hash": policy["policy_hash"][:12],
            "sources": "+".join(sorted(policy["sources"])),
            "distributions": ";".join(sorted(policy["distributions"])),
            "local_prompt_count": policy["local_prompt_count"],
            "zip_matched_train_cells": policy["zip_matched_train_cells"],
            "base_stock_form": base_stock_form,
            "non_base_stock_form": not base_stock_form,
            "thresholding": thresholding,
            "thresholding_among_non_base_stock": thresholding and not base_stock_form,
        }
        rows.append(row)
        if thresholding and not base_stock_form and len(examples) < 25:
            examples.append(
                {
                    "policy_hash": row["policy_hash"],
                    "sources": row["sources"],
                    "distributions": row["distributions"],
                    "excerpt": excerpt_for_threshold(code),
                }
            )

    n_total = len(rows)
    n_base = sum(row["base_stock_form"] for row in rows)
    n_non_base = n_total - n_base
    n_threshold_total = sum(row["thresholding"] for row in rows)
    n_threshold_non_base = sum(row["thresholding_among_non_base_stock"] for row in rows)
    summary = [
        {"metric": "combined_matched_unique_policies", "count": n_total, "rate_pct": 100.0},
        {"metric": "base_stock_form_policies", "count": n_base, "rate_pct": round(100.0 * n_base / n_total, 4)},
        {
            "metric": "non_base_stock_form_policies",
            "count": n_non_base,
            "rate_pct": round(100.0 * n_non_base / n_total, 4),
        },
        {
            "metric": "thresholding_policies_total",
            "count": n_threshold_total,
            "rate_pct": round(100.0 * n_threshold_total / n_total, 4),
        },
        {
            "metric": "thresholding_policies_among_non_base_stock",
            "count": n_threshold_non_base,
            "rate_pct": round(100.0 * n_threshold_non_base / n_non_base, 4),
        },
    ]

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with OUT_LABELS.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    with OUT_SUMMARY.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(summary[0]))
        writer.writeheader()
        writer.writerows(summary)
    with OUT_EXAMPLES.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(examples[0]) if examples else ["policy_hash"])
        writer.writeheader()
        writer.writerows(examples)

    for row in summary:
        print(f"{row['metric']},{row['count']},{row['rate_pct']}")
    print(f"labels_csv,{OUT_LABELS}")
    print(f"summary_csv,{OUT_SUMMARY}")
    print(f"examples_csv,{OUT_EXAMPLES}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
