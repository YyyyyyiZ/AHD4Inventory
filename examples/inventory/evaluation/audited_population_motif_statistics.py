#!/usr/bin/env python3
"""Audited motif labels for saved inventory populations.

This detector is deliberately more conservative than earlier exploratory
scripts.  It labels every policy record in `pops/population_generation_*.json`
with the user's table motifs and a small set of concrete extra motifs.

Counting unit: population member record, not deduplicated code.
"""

from __future__ import annotations

import ast
import csv
import json
import math
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
OUT_DIR = ROOT / "examples" / "inventory" / "evaluation" / "audited_population_motif_statistics"
OUT_LABELS = OUT_DIR / "audited_population_policy_motif_labels.csv"
OUT_OVERALL = OUT_DIR / "audited_population_motif_overall.csv"
OUT_BY_DIST = OUT_DIR / "audited_population_motif_by_distribution.csv"
OUT_TOP10 = OUT_DIR / "audited_population_motif_top10_by_distribution.csv"
OUT_TOP10_LABELS = OUT_DIR / "audited_population_top10_policy_motif_labels.csv"
OUT_TOP10_OVERALL = OUT_DIR / "audited_population_motif_top10_overall.csv"
OUT_FINAL = OUT_DIR / "audited_population_motif_final_generation.csv"
OUT_FINAL_LABELS = OUT_DIR / "audited_population_final_generation_policy_motif_labels.csv"
OUT_FINAL_BY_DIST = OUT_DIR / "audited_population_motif_final_generation_by_distribution.csv"
OUT_EXTRA = OUT_DIR / "audited_extra_motif_overall.csv"
OUT_EXTRA_BY_DIST = OUT_DIR / "audited_extra_motif_by_distribution.csv"
OUT_EXTRA_TOP10 = OUT_DIR / "audited_extra_motif_top10_overall.csv"
OUT_EXTRA_FINAL = OUT_DIR / "audited_extra_motif_final_generation.csv"
OUT_CATEGORY_SUMMARY = OUT_DIR / "audited_motif_summary_by_population_slice.csv"
OUT_AUDIT = OUT_DIR / "audited_motif_examples_for_manual_check.csv"

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

DIST_RE = re.compile(r"(?P<dist>(?:exponential|poisson|normal_std\d+)_L\d+_c\d+_\d+)")
GEN_RE = re.compile(r"population_generation_(\d+)\.json$")

STATE_NAMES = {"on_hand_inventory", "inventory", "current_inventory", "I_t", "I"}
PIPE_NAMES = {"pipeline_orders", "pipeline", "pipeline_vector", "Q_t", "Q"}
TARGET_NAME_RE = re.compile(r"(target|desired|reorder|stock_level|adjusted_base|dynamic_base)", re.I)
GAP_NAME_RE = re.compile(r"(gap|raw_order|order_needed|order_up_to|target_order|shortfall)", re.I)
ORDER_NAME_RE = re.compile(r"(order|amount|quantity|replenish|raw_order|final_order)", re.I)
WEIGHT_NAME_RE = re.compile(r"(weight|weighted|discount|coverage|effective_pipeline)", re.I)
SMOOTH_NAME_RE = re.compile(r"(alpha|beta|gain|smooth|smoothing|fraction|partial|closure|adjustment_factor)", re.I)
CAP_NAME_RE = re.compile(r"(max_order|order_cap|cap|upper|capacity|limit)", re.I)
FLOOR_NAME_RE = re.compile(r"(min_order|minimum_order|floor|lower)", re.I)
BASELINE_ORDER_RE = re.compile(r"(baseline_order|constant_order|fixed_order)", re.I)
PREVIOUS_ORDER_RE = re.compile(r"(previous_order|prev_order|last_order|prior_order)", re.I)
ORDER_LIKE_TARGET_EXCLUSION_RE = re.compile(
    r"(target_order|desired_order|raw_order|base_order|final_order|order_amount|order_quantity|order_needed|order_up_to)",
    re.I,
)


@dataclass
class ExprInfo:
    state: bool = False
    on_hand: bool = False
    pipeline: bool = False
    pipeline_sum: bool = False
    pipeline_linear: bool = False
    pipeline_weighting: bool = False
    pipeline_nonlinear: bool = False
    previous_order: bool = False
    gap: bool = False
    fixed_target_gap: bool = False
    state_target_gap: bool = False
    const: bool = False
    value: float | None = None
    alpha_like: bool = False
    cap_like: bool = False
    floor_like: bool = False
    baseline_order_like: bool = False
    safety_stock_like: bool = False
    demand_proxy_like: bool = False
    target_like: bool = False

    def merge(self, other: "ExprInfo") -> "ExprInfo":
        return ExprInfo(
            state=self.state or other.state,
            on_hand=self.on_hand or other.on_hand,
            pipeline=self.pipeline or other.pipeline,
            pipeline_sum=self.pipeline_sum or other.pipeline_sum,
            pipeline_linear=self.pipeline_linear or other.pipeline_linear,
            pipeline_weighting=self.pipeline_weighting or other.pipeline_weighting,
            pipeline_nonlinear=self.pipeline_nonlinear or other.pipeline_nonlinear,
            previous_order=self.previous_order or other.previous_order,
            gap=self.gap or other.gap,
            fixed_target_gap=self.fixed_target_gap or other.fixed_target_gap,
            state_target_gap=self.state_target_gap or other.state_target_gap,
            const=self.const and other.const,
            value=None,
            alpha_like=self.alpha_like or other.alpha_like,
            cap_like=self.cap_like or other.cap_like,
            floor_like=self.floor_like or other.floor_like,
            baseline_order_like=self.baseline_order_like or other.baseline_order_like,
            safety_stock_like=self.safety_stock_like or other.safety_stock_like,
            demand_proxy_like=self.demand_proxy_like or other.demand_proxy_like,
            target_like=self.target_like or other.target_like,
        )


def normalize_code(code: str) -> str:
    try:
        return ast.unparse(ast.parse(code))
    except Exception:
        return code.strip()


def folder_metadata(folder_name: str) -> dict[str, str]:
    dist_match = DIST_RE.search(folder_name)
    dist = dist_match.group("dist") if dist_match else "unknown"
    prefix = folder_name.split(f"_{dist}_")[0] if dist != "unknown" and f"_{dist}_" in folder_name else ""
    model = prefix or folder_name.split("_", 1)[0]
    return {"folder": folder_name, "distribution": dist, "model": model}


def as_float(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def is_zero(node: ast.AST) -> bool:
    if isinstance(node, ast.Constant):
        return node.value in {0, 0.0, None, False}
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        return isinstance(node.operand, ast.Constant) and node.operand.value == 0
    return False


def const_value(node: ast.AST) -> float | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return float(node.value)
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        inner = const_value(node.operand)
        return -inner if inner is not None else None
    return None


def name_is_pipeline(node: ast.AST) -> bool:
    return isinstance(node, ast.Name) and node.id in PIPE_NAMES


def is_pipeline_subscript(node: ast.AST) -> bool:
    return isinstance(node, ast.Subscript) and name_is_pipeline(node.value)


def is_negative_one(node: ast.AST) -> bool:
    return (
        isinstance(node, ast.UnaryOp)
        and isinstance(node.op, ast.USub)
        and isinstance(node.operand, ast.Constant)
        and node.operand.value == 1
    ) or (isinstance(node, ast.Constant) and node.value == -1)


def is_last_pipeline(node: ast.AST) -> bool:
    if is_pipeline_subscript(node):
        return is_negative_one(node.slice)
    if isinstance(node, ast.IfExp):
        return is_last_pipeline(node.body) or is_last_pipeline(node.orelse)
    return False


def name_info(name: str, env: dict[str, ExprInfo]) -> ExprInfo:
    if name in env:
        return env[name]
    lowered = name.lower()
    return ExprInfo(
        state=name in STATE_NAMES or name in PIPE_NAMES,
        on_hand=name in STATE_NAMES,
        pipeline=name in PIPE_NAMES,
        pipeline_linear=name in PIPE_NAMES,
        previous_order=bool(PREVIOUS_ORDER_RE.search(name)),
        alpha_like=bool(SMOOTH_NAME_RE.search(name)),
        cap_like=bool(CAP_NAME_RE.search(name)),
        floor_like=bool(FLOOR_NAME_RE.search(name)),
        baseline_order_like=bool(BASELINE_ORDER_RE.search(name)),
        safety_stock_like="safety_stock" in lowered or "buffer" in lowered,
        demand_proxy_like=bool(re.search(r"(demand|forecast|estimate|recent)", lowered)),
        target_like=is_target_level_name(name),
    )


def is_target_level_name(name: str) -> bool:
    return bool(TARGET_NAME_RE.search(name)) and not bool(ORDER_LIKE_TARGET_EXCLUSION_RE.search(name))


def list_tuple_constant_len(node: ast.AST) -> int | None:
    if isinstance(node, (ast.List, ast.Tuple)):
        return len(node.elts)
    return None


def expr_info(node: ast.AST, env: dict[str, ExprInfo]) -> ExprInfo:
    if isinstance(node, ast.Name):
        return name_info(node.id, env)
    if isinstance(node, ast.Constant):
        val = const_value(node)
        return ExprInfo(const=True, value=val)
    if isinstance(node, ast.UnaryOp):
        info = expr_info(node.operand, env)
        if isinstance(node.op, ast.USub) and info.value is not None:
            info.value = -info.value
        return info
    if is_pipeline_subscript(node):
        return ExprInfo(
            state=True,
            pipeline=True,
            pipeline_linear=True,
            pipeline_weighting=not is_last_pipeline(node),
            previous_order=is_last_pipeline(node),
        )
    if isinstance(node, ast.Slice):
        return ExprInfo()
    if isinstance(node, ast.Call):
        func = node.func.id if isinstance(node.func, ast.Name) else node.func.attr if isinstance(node.func, ast.Attribute) else ""
        arg_infos = [expr_info(arg, env) for arg in node.args]
        out = ExprInfo()
        for info in arg_infos:
            out = out.merge(info)
        if func == "sum" and node.args:
            arg = node.args[0]
            if name_is_pipeline(arg):
                out.state = out.pipeline = out.pipeline_sum = out.pipeline_linear = True
            elif is_pipeline_subscript(arg):
                out.state = out.pipeline = out.pipeline_linear = out.pipeline_weighting = True
        if func in {"max", "min", "sorted"} and any(info.pipeline for info in arg_infos):
            # max/min of the pipeline vector is nonlinear. min/max used for order
            # clipping is handled separately and should not rely on this flag alone.
            if any(name_is_pipeline(arg) for arg in node.args):
                out.pipeline_nonlinear = True
        if func.lower() in {"var", "variance", "std", "median", "percentile"} and any(info.pipeline for info in arg_infos):
            out.pipeline_nonlinear = True
        if func in {"int", "round", "ceil", "floor"}:
            # Keep dependency information from the rounded expression.
            pass
        return out
    if isinstance(node, ast.ListComp):
        out = ExprInfo()
        for gen in node.generators:
            if name_is_pipeline(gen.iter):
                out.state = out.pipeline = out.pipeline_linear = out.pipeline_weighting = True
        out = out.merge(expr_info(node.elt, env))
        return out
    if isinstance(node, ast.GeneratorExp):
        out = expr_info(node.elt, env)
        for gen in node.generators:
            if name_is_pipeline(gen.iter):
                out.state = out.pipeline = out.pipeline_linear = True
                if not isinstance(node.elt, ast.Name):
                    out.pipeline_weighting = True
        return out
    if isinstance(node, ast.IfExp):
        return expr_info(node.body, env).merge(expr_info(node.orelse, env)).merge(expr_info(node.test, env))
    if isinstance(node, ast.Compare):
        out = expr_info(node.left, env)
        for comp in node.comparators:
            out = out.merge(expr_info(comp, env))
        return out
    if isinstance(node, ast.BoolOp):
        out = ExprInfo()
        for value in node.values:
            out = out.merge(expr_info(value, env))
        return out
    if isinstance(node, ast.BinOp):
        left = expr_info(node.left, env)
        right = expr_info(node.right, env)
        out = left.merge(right)
        out.const = left.const and right.const
        if isinstance(node.op, ast.Add) and left.value is not None and right.value is not None:
            out.value = left.value + right.value
        elif isinstance(node.op, ast.Sub) and left.value is not None and right.value is not None:
            out.value = left.value - right.value
        elif isinstance(node.op, ast.Mult) and left.value is not None and right.value is not None:
            out.value = left.value * right.value
        elif isinstance(node.op, ast.Div) and left.value is not None and right.value not in {None, 0}:
            out.value = left.value / right.value

        if isinstance(node.op, ast.Mult):
            if (left.pipeline_linear and right.const) or (right.pipeline_linear and left.const):
                out.pipeline_weighting = True
            if (left.pipeline and right.pipeline) or left.pipeline_nonlinear or right.pipeline_nonlinear:
                out.pipeline_nonlinear = True
        if isinstance(node.op, ast.Div):
            if left.pipeline and right.pipeline_sum:
                out.pipeline_nonlinear = True
            if left.pipeline and right.pipeline and not right.pipeline_sum:
                out.pipeline_nonlinear = True
        if isinstance(node.op, (ast.Pow,)):
            if left.pipeline or left.gap or left.state:
                out.pipeline_nonlinear = left.pipeline or left.pipeline_nonlinear
        return out
    return ExprInfo()


def call_name(node: ast.Call) -> str:
    if isinstance(node.func, ast.Name):
        return node.func.id
    if isinstance(node.func, ast.Attribute):
        return node.func.attr
    return ""


def positive_gap_info(node: ast.AST, env: dict[str, ExprInfo]) -> tuple[bool, bool, bool]:
    """Return (is_gap, fixed_target_gap, state_target_gap)."""
    if not isinstance(node, ast.Call) or call_name(node) != "max" or len(node.args) < 2:
        return False, False, False
    zeros = [arg for arg in node.args if is_zero(arg)]
    if not zeros:
        return False, False, False
    candidates = [arg for arg in node.args if not is_zero(arg)]
    for candidate in candidates:
        is_gap, fixed, state_target = raw_gap_info(candidate, env)
        if is_gap:
            return is_gap, fixed, state_target
        info = expr_info(candidate, env)
        if info.gap:
            return True, info.fixed_target_gap, info.state_target_gap
    return False, False, False


def raw_gap_info(node: ast.AST, env: dict[str, ExprInfo]) -> tuple[bool, bool, bool]:
    """Recognize target-minus-state expressions, including chained subtraction."""
    info = expr_info(node, env)
    if info.gap:
        return True, info.fixed_target_gap, info.state_target_gap
    if not isinstance(node, ast.BinOp) or not isinstance(node.op, ast.Sub):
        return False, False, False

    positive_terms: list[ast.AST] = []
    negative_terms: list[ast.AST] = []

    def collect(expr: ast.AST, sign: int) -> None:
        if isinstance(expr, ast.BinOp) and isinstance(expr.op, ast.Add):
            collect(expr.left, sign)
            collect(expr.right, sign)
        elif isinstance(expr, ast.BinOp) and isinstance(expr.op, ast.Sub):
            collect(expr.left, sign)
            collect(expr.right, -sign)
        else:
            (positive_terms if sign > 0 else negative_terms).append(expr)

    collect(node, 1)
    pos_infos = [expr_info(term, env) for term in positive_terms]
    neg_infos = [expr_info(term, env) for term in negative_terms]
    neg_state = any(info.state for info in neg_infos)
    pos_state = any(info.state for info in pos_infos)
    pos_target_name = any(
        isinstance(term, ast.Name) and is_target_level_name(term.id)
        for term in positive_terms
    ) or any(
        TARGET_NAME_RE.search(ast.unparse(term))
        and not ORDER_LIKE_TARGET_EXCLUSION_RE.search(ast.unparse(term))
        for term in positive_terms
    )
    pos_target_like = any(info.target_like for info in pos_infos) or pos_target_name
    pos_nonstate = any(not info.state for info in pos_infos)
    # Fixed target gap: constants/parameters on the positive side, state signal subtracted.
    fixed = neg_state and pos_nonstate and not pos_state
    # State-dependent target gap: a target-like positive term also depends on state.
    state_target = neg_state and pos_state and pos_target_like
    return fixed or state_target, fixed, state_target


def contains_weighted_loop(stmt: ast.stmt) -> bool:
    if not isinstance(stmt, ast.For):
        return False
    text = ast.unparse(stmt).lower()
    return "pipeline_orders" in text and ("weight" in text or "discount" in text) and re.search(r"\+=", text) is not None


def contains_pipeline_ratio(node: ast.AST, env: dict[str, ExprInfo]) -> bool:
    for sub in ast.walk(node):
        if isinstance(sub, ast.BinOp) and isinstance(sub.op, ast.Div):
            left = expr_info(sub.left, env)
            right = expr_info(sub.right, env)
            if left.pipeline and right.pipeline_sum:
                return True
    return False


def contains_partial_adjustment(node: ast.AST, env: dict[str, ExprInfo]) -> bool:
    for sub in ast.walk(node):
        if not isinstance(sub, ast.BinOp) or not isinstance(sub.op, ast.Mult):
            continue
        left = expr_info(sub.left, env)
        right = expr_info(sub.right, env)
        left_gap = left.gap or positive_gap_info(sub.left, env)[0] or raw_gap_info(sub.left, env)[0]
        right_gap = right.gap or positive_gap_info(sub.right, env)[0] or raw_gap_info(sub.right, env)[0]
        left_alpha = left.alpha_like and (left.value is None or 0 < left.value < 1)
        right_alpha = right.alpha_like and (right.value is None or 0 < right.value < 1)
        if (left_alpha and right_gap) or (right_alpha and left_gap):
            return True
        if left.value is not None and 0 < left.value < 1 and (right_gap or re.search(GAP_NAME_RE, ast.unparse(sub.right))):
            return True
        if right.value is not None and 0 < right.value < 1 and (left_gap or re.search(GAP_NAME_RE, ast.unparse(sub.left))):
            return True
    return False


def contains_order_clip(node: ast.AST, env: dict[str, ExprInfo]) -> bool:
    whole_text = ast.unparse(node).lower()
    for sub in ast.walk(node):
        if not isinstance(sub, ast.Call) or call_name(sub) not in {"min", "max"} or len(sub.args) < 2:
            continue
        sub_text = ast.unparse(sub).lower()
        if "len(pipeline_orders)" in sub_text and not re.search(
            r"(order|amount|gap|cap|min_order|minimum_order|max_order|threshold)", whole_text
        ):
            continue
        # Exclude positive part and non-negativity cleanup.
        if call_name(sub) == "max" and any(is_zero(arg) for arg in sub.args):
            nonzero_args = [arg for arg in sub.args if not is_zero(arg)]
            if not any(expr_info(arg, env).floor_like for arg in sub.args) and len(nonzero_args) == 1:
                continue
        infos = [expr_info(arg, env) for arg in sub.args]
        has_state_or_order = any(info.state or info.gap for info in infos) or any(ORDER_NAME_RE.search(ast.unparse(arg)) for arg in sub.args)
        has_named_bound = any(info.cap_like or info.floor_like for info in infos)
        has_nonzero_numeric = any((value := const_value(arg)) is not None and abs(value) > 1e-9 for arg in sub.args)
        if has_state_or_order and (has_named_bound or has_nonzero_numeric):
            return True
    return False


def contains_constant_order(node: ast.AST, env: dict[str, ExprInfo]) -> bool:
    for sub in ast.walk(node):
        if isinstance(sub, ast.BinOp) and isinstance(sub.op, ast.Add):
            left = expr_info(sub.left, env)
            right = expr_info(sub.right, env)
            if (left.baseline_order_like and (right.state or right.gap)) or (right.baseline_order_like and (left.state or left.gap)):
                return True
    return False


def contains_order_smoothing(node: ast.AST, env: dict[str, ExprInfo]) -> bool:
    text = ast.unparse(node).lower()
    info = expr_info(node, env)
    if not info.previous_order:
        return False
    # Exclude using pipeline_orders[-1] only as a demand/recent-arrival proxy.
    if re.search(r"(demand|forecast|estimate|recent|arrival)", text) and not re.search(
        r"(previous_order|prev_order|last_order|delta|smooth|smoothing|beta|blend|min\(|max\()", text
    ):
        return False
    return bool(re.search(r"(previous_order|prev_order|last_order|delta|smooth|smoothing|beta|blend|min\(|max\()", text))


def condition_is_explicit_threshold(node: ast.AST, env: dict[str, ExprInfo]) -> bool:
    if not isinstance(node, ast.Compare):
        return False
    if not any(isinstance(op, (ast.Lt, ast.LtE, ast.Gt, ast.GtE)) for op in node.ops):
        return False
    text = ast.unparse(node).lower()
    if re.fullmatch(r"len\(pipeline_orders\)\s*[<>=!]+\s*\d+", text):
        return False
    if re.fullmatch(r"(raw_order|target_order|gap|inventory_gap|order_needed)\s*>\s*0(?:\.0)?", text):
        return False
    if re.search(r"(threshold|reorder|critical|emergency|coverage|shortage|min_order|minimum_order|max_order|cap)", text):
        return expr_info(node, env).state or bool(re.search(r"(gap|order|inventory|pipeline)", text))
    comparators = [const_value(comp) for comp in node.comparators]
    if any(value is not None and abs(value) > 1e-9 for value in comparators):
        return expr_info(node, env).state or bool(re.search(r"(gap|order|inventory|pipeline)", text))
    return False


def contains_integer_rounding(node: ast.AST) -> bool:
    return any(isinstance(sub, ast.Call) and call_name(sub) in {"int", "round", "ceil", "floor"} for sub in ast.walk(node))


def contains_nonlinear_gap_transform(node: ast.AST, env: dict[str, ExprInfo]) -> bool:
    for sub in ast.walk(node):
        if isinstance(sub, ast.Call) and call_name(sub).lower() in {"sqrt", "log", "exp"}:
            if any(expr_info(arg, env).gap or expr_info(arg, env).state for arg in sub.args):
                return True
        if isinstance(sub, ast.BinOp) and isinstance(sub.op, ast.Pow):
            left = expr_info(sub.left, env)
            if left.gap or left.state:
                return True
    return False


def stmt_assign_targets(stmt: ast.Assign) -> list[str]:
    return [target.id for target in stmt.targets if isinstance(target, ast.Name)]


def scan_statements(stmts: list[ast.stmt], env: dict[str, ExprInfo], labels: dict[str, bool]) -> None:
    for stmt in stmts:
        if isinstance(stmt, ast.Assign):
            value = stmt.value
            info = expr_info(value, env)
            is_gap, fixed_gap, state_gap = positive_gap_info(value, env)
            info.gap = info.gap or is_gap
            info.fixed_target_gap = info.fixed_target_gap or fixed_gap
            info.state_target_gap = info.state_target_gap or state_gap
            if is_last_pipeline(value):
                info.previous_order = True

            labels["inventory_position"] |= info.on_hand and info.pipeline_sum
            labels["pipeline_weighting"] |= info.pipeline_weighting
            labels["nonlinear_pipeline_composition"] |= info.pipeline_nonlinear or contains_pipeline_ratio(value, env)
            labels["order_up_to"] |= fixed_gap
            labels["state_dependent_target"] |= state_gap
            labels["partial_adjustment"] |= contains_partial_adjustment(value, env)
            labels["order_clipping"] |= contains_order_clip(value, env)
            labels["constant_order"] |= contains_constant_order(value, env)
            labels["order_smoothing"] |= contains_order_smoothing(value, env)
            labels["integer_rounding"] |= contains_integer_rounding(value)
            labels["nonlinear_gap_transform"] |= contains_nonlinear_gap_transform(value, env)

            names = stmt_assign_targets(stmt)
            for name in names:
                lowered = name.lower()
                if "inventory_position" in lowered and info.on_hand and info.pipeline_sum:
                    labels["inventory_position"] = True
                if is_target_level_name(name):
                    info.target_like = True
                    if info.state:
                        labels["state_dependent_target"] = True
                if PREVIOUS_ORDER_RE.search(name) and is_last_pipeline(value):
                    info.previous_order = True
                if BASELINE_ORDER_RE.search(name):
                    info.baseline_order_like = True
                if "safety_stock" in lowered or "buffer" in lowered:
                    info.safety_stock_like = True
                if re.search(r"(demand|forecast|estimate|recent)", lowered) and info.pipeline:
                    info.demand_proxy_like = True
                    labels["pipeline_demand_proxy"] = True
                if info.safety_stock_like:
                    labels["safety_stock_buffer"] = True
                env[name] = info

        elif isinstance(stmt, ast.AugAssign):
            value_info = expr_info(stmt.value, env)
            target_name = stmt.target.id if isinstance(stmt.target, ast.Name) else ""
            old = env.get(target_name, ExprInfo()) if target_name else ExprInfo()
            combined = old.merge(value_info)
            if contains_order_clip(stmt.value, env):
                labels["order_clipping"] = True
            if value_info.pipeline and re.search(r"(weight|discount)", ast.unparse(stmt).lower()):
                labels["pipeline_weighting"] = True
            if target_name:
                env[target_name] = combined

        elif isinstance(stmt, ast.For):
            text = ast.unparse(stmt).lower()
            if contains_weighted_loop(stmt):
                labels["pipeline_weighting"] = True
            if "pipeline_orders" in text and re.search(r"(demand|forecast|estimate|recent)", text):
                labels["pipeline_demand_proxy"] = True
            scan_statements(stmt.body, env.copy(), labels)
            scan_statements(stmt.orelse, env.copy(), labels)

        elif isinstance(stmt, ast.If):
            if condition_is_explicit_threshold(stmt.test, env):
                # Count only if the branches affect an order/gap-like variable or return.
                branch_text = (ast.unparse(stmt.body) + " " + ast.unparse(stmt.orelse)).lower()
                if re.search(r"(order|amount|gap|return|boost|multiplier|adjustment)", branch_text):
                    labels["threshold_order_activation"] = True
            if re.search(r"(emergency|shortage|critical|low_inv|low_inventory|aggressive)", ast.unparse(stmt).lower()):
                labels["emergency_or_shortage_boost"] = True
            scan_statements(stmt.body, env.copy(), labels)
            scan_statements(stmt.orelse, env.copy(), labels)

        elif isinstance(stmt, ast.Return) and stmt.value is not None:
            value = stmt.value
            info = expr_info(value, env)
            is_gap, fixed_gap, state_gap = positive_gap_info(value, env)
            labels["inventory_position"] |= info.on_hand and info.pipeline_sum
            labels["pipeline_weighting"] |= info.pipeline_weighting
            labels["nonlinear_pipeline_composition"] |= info.pipeline_nonlinear or contains_pipeline_ratio(value, env)
            labels["order_up_to"] |= fixed_gap
            labels["state_dependent_target"] |= state_gap
            labels["partial_adjustment"] |= contains_partial_adjustment(value, env)
            labels["order_clipping"] |= contains_order_clip(value, env)
            labels["constant_order"] |= contains_constant_order(value, env)
            labels["order_smoothing"] |= contains_order_smoothing(value, env)
            labels["integer_rounding"] |= contains_integer_rounding(value)
            labels["nonlinear_gap_transform"] |= contains_nonlinear_gap_transform(value, env)


def text_fallbacks(code: str, labels: dict[str, bool]) -> None:
    compact = re.sub(r"\s+", " ", code)
    lower = compact.lower()
    if "on_hand_inventory + sum(pipeline_orders)" in lower:
        labels["inventory_position"] = True
    if re.search(r"\bweights?\s*=", compact, re.I) and re.search(r"zip\s*\(\s*weights?", compact, re.I):
        labels["pipeline_weighting"] = True
    if re.search(r"\b(max|min)\s*\(\s*pipeline_orders\s*\)", compact, re.I):
        labels["nonlinear_pipeline_composition"] = True
    if re.search(r"\b(var|variance|std|median|percentile)\s*\(", compact, re.I) and "pipeline_orders" in lower:
        labels["nonlinear_pipeline_composition"] = True
    if re.search(r"sum\s*\(\s*pipeline_orders\s*\[[^]]+:[^]]*\]\s*\)\s*/\s*sum\s*\(\s*pipeline_orders\s*\)", compact):
        labels["nonlinear_pipeline_composition"] = True
    if re.search(r"(pipeline_orders\s*\[\s*0\s*\]|pipeline_orders\s*\[\s*:\s*\d+|recent_)", compact, re.I):
        labels["near_term_pipeline_focus"] = True
    if re.search(r"(demand|forecast|estimate|recent).{0,80}pipeline_orders|pipeline_orders.{0,80}(demand|forecast|estimate|recent)", compact, re.I):
        labels["pipeline_demand_proxy"] = True
    if re.search(r"(safety_stock|buffer)", compact, re.I):
        labels["safety_stock_buffer"] = True
    if re.search(r"(max_order|order_cap|cap|min_order|minimum_order)", compact, re.I) and re.search(r"\b(min|max|if)\b", compact):
        labels["order_clipping"] = True
    if re.search(r"(baseline_order|constant_order|fixed_order)", compact, re.I) and "+" in compact:
        labels["constant_order"] = True
    if re.search(r"(previous_order|prev_order|last_order)", compact, re.I) and re.search(r"(delta|smooth|beta|blend|min\(|max\()", compact, re.I):
        labels["order_smoothing"] = True
    if re.search(r"\b(int|round|ceil|floor)\s*\(", compact):
        labels["integer_rounding"] = True
    if re.search(r"(emergency|shortage|critical|low_inv|low_inventory|aggressive)", compact, re.I):
        labels["emergency_or_shortage_boost"] = True


def detect_motifs(code: str) -> dict[str, bool]:
    labels = {motif: False for motif in TABLE_MOTIFS + EXTRA_MOTIFS}
    normalized = normalize_code(code)
    try:
        tree = ast.parse(normalized)
    except SyntaxError:
        text_fallbacks(normalized, labels)
        return labels
    body = tree.body[0].body if tree.body and isinstance(tree.body[0], ast.FunctionDef) else tree.body
    scan_statements(body, {}, labels)
    text_fallbacks(normalized, labels)
    return labels


def iter_population_records() -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for path in sorted((ROOT / "examples" / "inventory").glob("**/pops/population_generation_*.json")):
        gen_match = GEN_RE.search(path.name)
        if not gen_match:
            continue
        generation = int(gen_match.group(1))
        folder = path.parents[1].name
        meta = folder_metadata(folder)
        try:
            data = json.loads(path.read_text())
        except Exception:
            continue
        if not isinstance(data, list):
            continue
        for rank, item in enumerate(data, start=1):
            if not isinstance(item, dict):
                continue
            code = item.get("code")
            if not isinstance(code, str) or not code.strip():
                continue
            objective = as_float(item.get("objective"))
            if objective is None:
                objective = as_float(item.get("cost"))
            labels = detect_motifs(code)
            table_motifs = [motif for motif in TABLE_MOTIFS if labels[motif]]
            extra_motifs = [motif for motif in EXTRA_MOTIFS if labels[motif]]
            records.append(
                {
                    **meta,
                    "generation": generation,
                    "rank_in_population_file": rank,
                    "objective": objective,
                    "test_objective": as_float(item.get("test_objective")),
                    **{motif: labels[motif] for motif in TABLE_MOTIFS + EXTRA_MOTIFS},
                    "table_motif_count": len(table_motifs),
                    "extra_motif_count": len(extra_motifs),
                    "table_motifs": ";".join(table_motifs),
                    "extra_motifs": ";".join(extra_motifs),
                    "code_excerpt": "\\n".join(normalize_code(code).splitlines()[:12])[:1200],
                    "_code": code,
                }
            )
    return records


def summarize(records: list[dict[str, Any]], motifs: list[str], group_cols: list[str] | None = None) -> list[dict[str, Any]]:
    group_cols = group_cols or []
    grouped: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        grouped[tuple(record[col] for col in group_cols)].append(record)
    rows: list[dict[str, Any]] = []
    for key, group in sorted(grouped.items()):
        row = {col: value for col, value in zip(group_cols, key)}
        row["n_policies"] = len(group)
        for motif in motifs:
            count = sum(bool(record[motif]) for record in group)
            row[f"{motif}_count"] = count
            row[f"{motif}_pct"] = round(100.0 * count / len(group), 4)
        count_col = "table_motif_count" if motifs == TABLE_MOTIFS else "extra_motif_count"
        row[f"avg_{count_col}"] = round(sum(int(record[count_col]) for record in group) / len(group), 4)
        rows.append(row)
    return rows


def top10_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_dist: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        if record["objective"] is not None and record["distribution"] != "unknown":
            by_dist[record["distribution"]].append(record)
    selected: list[dict[str, Any]] = []
    for dist, group in by_dist.items():
        ranked = sorted(group, key=lambda row: row["objective"])
        k = max(1, math.ceil(0.10 * len(ranked)))
        selected.extend(ranked[:k])
    return selected


def final_generation_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    max_gen_by_folder: dict[str, int] = {}
    for record in records:
        folder = record["folder"]
        max_gen_by_folder[folder] = max(max_gen_by_folder.get(folder, -1), int(record["generation"]))
    return [record for record in records if int(record["generation"]) == max_gen_by_folder[record["folder"]]]


def audit_examples(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    examples: list[dict[str, Any]] = []
    for motif in TABLE_MOTIFS + EXTRA_MOTIFS:
        positives = [record for record in records if record[motif]]
        negatives = [record for record in records if not record[motif]]
        for label, pool in [("positive", positives[:3]), ("negative", negatives[:2])]:
            for record in pool:
                examples.append(
                    {
                        "motif": motif,
                        "label": label,
                        "folder": record["folder"],
                        "distribution": record["distribution"],
                        "generation": record["generation"],
                        "objective": record["objective"],
                        "table_motifs": record["table_motifs"],
                        "extra_motifs": record["extra_motifs"],
                        "code_excerpt": record["code_excerpt"],
                    }
                )
    return examples


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        return
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    records = iter_population_records()
    label_rows = [{k: v for k, v in record.items() if k != "_code"} for record in records]
    top_records = top10_records(records)
    top_label_rows = [{k: v for k, v in record.items() if k != "_code"} for record in top_records]
    final_records = final_generation_records(records)
    final_label_rows = [{k: v for k, v in record.items() if k != "_code"} for record in final_records]

    write_csv(OUT_LABELS, label_rows)
    write_csv(OUT_TOP10_LABELS, top_label_rows)
    write_csv(OUT_FINAL_LABELS, final_label_rows)

    write_csv(OUT_OVERALL, summarize(records, TABLE_MOTIFS))
    write_csv(OUT_BY_DIST, summarize(records, TABLE_MOTIFS, ["distribution"]))
    write_csv(OUT_EXTRA, summarize(records, EXTRA_MOTIFS))
    write_csv(OUT_EXTRA_BY_DIST, summarize(records, EXTRA_MOTIFS, ["distribution"]))
    write_csv(OUT_TOP10_OVERALL, summarize(top_records, TABLE_MOTIFS))
    write_csv(OUT_TOP10, summarize(top_records, TABLE_MOTIFS, ["distribution"]))
    write_csv(OUT_EXTRA_TOP10, summarize(top_records, EXTRA_MOTIFS))
    write_csv(OUT_FINAL, summarize(final_records, TABLE_MOTIFS))
    write_csv(OUT_FINAL_BY_DIST, summarize(final_records, TABLE_MOTIFS, ["distribution"]))
    write_csv(OUT_EXTRA_FINAL, summarize(final_records, EXTRA_MOTIFS))

    category_rows = []
    for category, group in [
        ("all_population", records),
        ("top10_by_distribution", top_records),
        ("final_generation", final_records),
    ]:
        row = summarize(group, TABLE_MOTIFS)[0]
        row = {"population_slice": category, **row}
        category_rows.append(row)
    write_csv(OUT_CATEGORY_SUMMARY, category_rows)
    write_csv(OUT_AUDIT, audit_examples(records))

    print(f"audited_population_policy_records,{len(records)}")
    print(f"run_folders,{len({record['folder'] for record in records})}")
    print(f"distributions,{len({record['distribution'] for record in records})}")
    print(f"final_generation_policy_records,{len(final_records)}")
    print(f"top10_policy_records,{len(top_records)}")
    print(f"labels_csv,{OUT_LABELS}")
    print(f"top10_labels_csv,{OUT_TOP10_LABELS}")
    print(f"final_labels_csv,{OUT_FINAL_LABELS}")
    print(f"overall_csv,{OUT_OVERALL}")
    print(f"by_distribution_csv,{OUT_BY_DIST}")
    print(f"extra_csv,{OUT_EXTRA}")
    print(f"category_summary_csv,{OUT_CATEGORY_SUMMARY}")
    print(f"top10_overall_csv,{OUT_TOP10_OVERALL}")
    print(f"top10_csv,{OUT_TOP10}")
    print(f"final_csv,{OUT_FINAL}")
    print(f"final_by_distribution_csv,{OUT_FINAL_BY_DIST}")
    print(f"audit_examples_csv,{OUT_AUDIT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
