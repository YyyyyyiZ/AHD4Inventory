#!/usr/bin/env python3
"""Motif statistics over saved inventory population files.

Scope:
- uses `pops/population_generation_*.json`
- excludes `pops_best` to avoid double counting archives
- counts population members as policy records, without code deduplication
- lower objective is better
"""

from __future__ import annotations

import ast
import csv
import json
import math
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
OUT_DIR = ROOT / "examples" / "inventory" / "evaluation" / "population_motif_statistics"
OUT_LABELS = OUT_DIR / "population_policy_motif_labels.csv"
OUT_OVERALL = OUT_DIR / "population_motif_overall.csv"
OUT_TOP10 = OUT_DIR / "population_motif_top10_by_distribution.csv"
OUT_FINAL = OUT_DIR / "population_motif_final_generation.csv"
OUT_FINAL_BY_DIST = OUT_DIR / "population_motif_final_generation_by_distribution.csv"

MOTIFS = [
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

DIST_RE = re.compile(r"(?P<dist>(?:exponential|poisson|normal_std\d+)_L\d+_c\d+_\d+)")
GEN_RE = re.compile(r"population_generation_(\d+)\.json$")

STATE_NAMES = {"on_hand_inventory", "inventory", "current_inventory", "I_t", "I"}
PIPE_NAMES = {"pipeline_orders", "pipeline", "pipeline_vector", "Q_t", "Q"}
TARGET_TOKENS = (
    "target",
    "desired",
    "base_stock",
    "order_up_to",
    "reorder_point",
    "stock_level",
)
ORDER_TOKENS = ("order", "amount", "quantity", "replenish", "raw_order", "final_order")
SMOOTHING_TOKENS = (
    "alpha",
    "beta",
    "gain",
    "smooth",
    "smoothing",
    "fraction",
    "partial",
    "adjustment_factor",
    "closure",
)
WEIGHTING_TOKENS = ("weight", "discount", "coverage", "effective_pipeline", "weighted")
CLIP_TOKENS = ("max_order", "order_cap", "cap", "upper", "min_order", "minimum_order", "floor", "lower")
CONSTANT_ORDER_TOKENS = ("base_order", "baseline_order", "constant_order", "fixed_order")
PREVIOUS_TOKENS = ("previous", "prev", "last", "prior")
SMOOTH_PREV_TOKENS = ("delta", "change", "smooth", "smoothing", "inertia", "blend", "beta")


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
    if value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(number):
        return None
    return number


def is_zero_expr(node: ast.AST) -> bool:
    if isinstance(node, ast.Constant):
        return node.value in {0, 0.0, None, False}
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        return isinstance(node.operand, ast.Constant) and node.operand.value == 0
    return False


def is_pipeline_name(node: ast.AST) -> bool:
    return isinstance(node, ast.Name) and node.id in PIPE_NAMES


def is_pipeline_expr(node: ast.AST) -> bool:
    return is_pipeline_name(node) or (
        isinstance(node, ast.Subscript) and isinstance(node.value, ast.Name) and node.value.id in PIPE_NAMES
    )


def is_negative_one(node: ast.AST) -> bool:
    return (
        isinstance(node, ast.UnaryOp)
        and isinstance(node.op, ast.USub)
        and isinstance(node.operand, ast.Constant)
        and node.operand.value == 1
    ) or (isinstance(node, ast.Constant) and node.value == -1)


def is_last_pipeline(node: ast.AST) -> bool:
    if isinstance(node, ast.Subscript) and is_pipeline_name(node.value):
        return is_negative_one(node.slice)
    if isinstance(node, ast.IfExp):
        return is_last_pipeline(node.body) or is_last_pipeline(node.orelse)
    return False


def has_name_token(name: str, tokens: tuple[str, ...]) -> bool:
    lowered = name.lower()
    return any(token in lowered for token in tokens)


def target_like(name: str) -> bool:
    return has_name_token(name, TARGET_TOKENS) and "inventory_position" not in name.lower()


def order_like(name: str) -> bool:
    return has_name_token(name, ORDER_TOKENS)


def previous_order_like(name: str) -> bool:
    lowered = name.lower()
    return any(token in lowered for token in PREVIOUS_TOKENS) and order_like(lowered)


class FeatureVisitor(ast.NodeVisitor):
    def __init__(self, deps: dict[str, dict[str, bool]], previous_vars: set[str]) -> None:
        self.deps = deps
        self.previous_vars = previous_vars
        self.state = False
        self.on_hand = False
        self.pipeline = False
        self.pipeline_sum = False
        self.pipeline_weighting = False
        self.pipeline_nonlinear = False
        self.previous_order = False
        self.smoothing_param = False
        self.clip_param = False
        self.constant_order_param = False

    def visit_Name(self, node: ast.Name) -> None:
        if node.id in STATE_NAMES:
            self.state = True
            self.on_hand = True
        if node.id in PIPE_NAMES:
            self.state = True
            self.pipeline = True
        if node.id in self.previous_vars or previous_order_like(node.id):
            self.previous_order = True
        if has_name_token(node.id, SMOOTHING_TOKENS):
            self.smoothing_param = True
        if has_name_token(node.id, CLIP_TOKENS):
            self.clip_param = True
        if has_name_token(node.id, CONSTANT_ORDER_TOKENS):
            self.constant_order_param = True
        if has_name_token(node.id, WEIGHTING_TOKENS):
            self.pipeline_weighting = True
        dep = self.deps.get(node.id)
        if dep:
            self.state |= dep["state"]
            self.on_hand |= dep["on_hand"]
            self.pipeline |= dep["pipeline"]
            self.pipeline_sum |= dep["pipeline_sum"]
            self.pipeline_weighting |= dep["pipeline_weighting"]
            self.pipeline_nonlinear |= dep["pipeline_nonlinear"]
            self.previous_order |= dep["previous_order"]
            self.smoothing_param |= dep["smoothing_param"]
            self.clip_param |= dep["clip_param"]
            self.constant_order_param |= dep["constant_order_param"]

    def visit_Subscript(self, node: ast.Subscript) -> None:
        if isinstance(node.value, ast.Name) and node.value.id in PIPE_NAMES:
            self.state = True
            self.pipeline = True
            if is_last_pipeline(node):
                self.previous_order = True
            else:
                self.pipeline_weighting = True
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        if isinstance(node.func, ast.Name):
            func = node.func.id
        elif isinstance(node.func, ast.Attribute):
            func = node.func.attr
        else:
            func = ""
        args = node.args
        if func == "sum" and args and is_pipeline_expr(args[0]):
            self.state = True
            self.pipeline = True
            self.pipeline_sum = True
            if isinstance(args[0], ast.Subscript):
                self.pipeline_weighting = True
        if func in {"max", "min", "sorted"} and any(is_pipeline_expr(arg) for arg in args):
            self.state = True
            self.pipeline = True
            self.pipeline_nonlinear = True
        if func.lower() in {"var", "variance", "std", "median", "percentile"} and any(
            is_pipeline_expr(arg) for arg in args
        ):
            self.state = True
            self.pipeline = True
            self.pipeline_nonlinear = True
        self.generic_visit(node)

    def visit_ListComp(self, node: ast.ListComp) -> None:
        for generator in node.generators:
            if is_pipeline_expr(generator.iter):
                self.state = True
                self.pipeline = True
                self.pipeline_weighting = True
        self.generic_visit(node)

    def visit_GeneratorExp(self, node: ast.GeneratorExp) -> None:
        for generator in node.generators:
            if is_pipeline_expr(generator.iter):
                self.state = True
                self.pipeline = True
                if not isinstance(node.elt, ast.Name):
                    self.pipeline_weighting = True
        self.generic_visit(node)


def expr_features(node: ast.AST, deps: dict[str, dict[str, bool]], previous_vars: set[str]) -> dict[str, bool]:
    visitor = FeatureVisitor(deps, previous_vars)
    visitor.visit(node)
    return {
        "state": visitor.state,
        "on_hand": visitor.on_hand,
        "pipeline": visitor.pipeline,
        "pipeline_sum": visitor.pipeline_sum,
        "pipeline_weighting": visitor.pipeline_weighting,
        "pipeline_nonlinear": visitor.pipeline_nonlinear,
        "previous_order": visitor.previous_order,
        "smoothing_param": visitor.smoothing_param,
        "clip_param": visitor.clip_param,
        "constant_order_param": visitor.constant_order_param,
    }


def is_pipeline_total_signal(features: dict[str, bool]) -> bool:
    return features["on_hand"] and features["pipeline_sum"]


def positive_part_gap(node: ast.AST, deps: dict[str, dict[str, bool]], previous_vars: set[str]) -> tuple[bool, bool]:
    """Return (is positive-part gap, fixed_target)."""
    if not isinstance(node, ast.Call):
        return False, False
    if not isinstance(node.func, ast.Name) or node.func.id != "max" or len(node.args) < 2:
        return False, False
    if not is_zero_expr(node.args[0]):
        return False, False
    gap = node.args[1]
    if not isinstance(gap, ast.BinOp) or not isinstance(gap.op, ast.Sub):
        return False, False
    left = expr_features(gap.left, deps, previous_vars)
    right = expr_features(gap.right, deps, previous_vars)
    is_gap = left["state"] != right["state"]
    fixed_target = is_gap and not left["state"] and right["state"]
    return is_gap, fixed_target


def contains_pipeline_ratio(node: ast.AST, deps: dict[str, dict[str, bool]], previous_vars: set[str]) -> bool:
    for sub in ast.walk(node):
        if isinstance(sub, ast.BinOp) and isinstance(sub.op, ast.Div):
            left = expr_features(sub.left, deps, previous_vars)
            right = expr_features(sub.right, deps, previous_vars)
            if left["pipeline"] and right["pipeline"]:
                return True
    return False


def contains_additive_constant_order(node: ast.AST, deps: dict[str, dict[str, bool]], previous_vars: set[str]) -> bool:
    for sub in ast.walk(node):
        if isinstance(sub, ast.BinOp) and isinstance(sub.op, ast.Add):
            left = expr_features(sub.left, deps, previous_vars)
            right = expr_features(sub.right, deps, previous_vars)
            if (left["state"] and right["constant_order_param"]) or (right["state"] and left["constant_order_param"]):
                return True
    return False


def contains_clipping(node: ast.AST, deps: dict[str, dict[str, bool]], previous_vars: set[str]) -> bool:
    for sub in ast.walk(node):
        if not isinstance(sub, ast.Call):
            continue
        if not isinstance(sub.func, ast.Name) or sub.func.id not in {"min", "max"} or len(sub.args) < 2:
            continue
        if sub.func.id == "max" and is_zero_expr(sub.args[0]):
            # Positive part operator is order-up-to, not clipping.
            continue
        features = [expr_features(arg, deps, previous_vars) for arg in sub.args]
        has_state = any(feature["state"] for feature in features)
        has_clip = any(feature["clip_param"] for feature in features)
        has_numeric_bound = any(isinstance(arg, ast.Constant) and isinstance(arg.value, (int, float)) for arg in sub.args)
        if has_state and (has_clip or has_numeric_bound):
            return True
    return False


def contains_partial_adjustment(node: ast.AST, deps: dict[str, dict[str, bool]], previous_vars: set[str]) -> bool:
    for sub in ast.walk(node):
        if isinstance(sub, ast.BinOp) and isinstance(sub.op, ast.Mult):
            left = expr_features(sub.left, deps, previous_vars)
            right = expr_features(sub.right, deps, previous_vars)
            if (left["smoothing_param"] and right["state"]) or (right["smoothing_param"] and left["state"]):
                return True
    return False


def contains_order_smoothing(node: ast.AST, deps: dict[str, dict[str, bool]], previous_vars: set[str]) -> bool:
    features = expr_features(node, deps, previous_vars)
    if not features["previous_order"]:
        return False
    source = ast.unparse(node).lower()
    return any(token in source for token in SMOOTH_PREV_TOKENS) or "min(" in source or "max(" in source


def detect_motifs(code: str) -> dict[str, bool]:
    labels = {motif: False for motif in MOTIFS}
    try:
        tree = ast.parse(normalize_code(code))
    except SyntaxError:
        return labels

    deps: dict[str, dict[str, bool]] = {}
    previous_vars: set[str] = set()
    target_state_dep: dict[str, bool] = {}

    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            features = expr_features(node.value, deps, previous_vars)
            if is_last_pipeline(node.value):
                features["previous_order"] = True
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        previous_vars.add(target.id)
            if is_pipeline_total_signal(features):
                labels["inventory_position"] = True
            if features["pipeline_weighting"]:
                labels["pipeline_weighting"] = True
            if features["pipeline_nonlinear"] or contains_pipeline_ratio(node.value, deps, previous_vars):
                labels["nonlinear_pipeline_composition"] = True
            if contains_partial_adjustment(node.value, deps, previous_vars):
                labels["partial_adjustment"] = True
            if contains_clipping(node.value, deps, previous_vars):
                labels["order_clipping"] = True
            if contains_additive_constant_order(node.value, deps, previous_vars):
                labels["constant_order"] = True
            if contains_order_smoothing(node.value, deps, previous_vars):
                labels["order_smoothing"] = True
            is_gap, fixed_target = positive_part_gap(node.value, deps, previous_vars)
            if is_gap and fixed_target:
                labels["order_up_to"] = True

            for target in node.targets:
                if not isinstance(target, ast.Name):
                    continue
                deps[target.id] = features
                if target_like(target.id):
                    target_state_dep[target.id] = features["state"]
                    if features["state"]:
                        labels["state_dependent_target"] = True
                if order_like(target.id) and contains_order_smoothing(node.value, deps, previous_vars):
                    labels["order_smoothing"] = True
        elif isinstance(node, ast.AugAssign):
            features = expr_features(node.value, deps, previous_vars)
            if isinstance(node.target, ast.Name):
                deps[node.target.id] = features
            if contains_clipping(node.value, deps, previous_vars):
                labels["order_clipping"] = True
        elif isinstance(node, ast.Return) and node.value is not None:
            features = expr_features(node.value, deps, previous_vars)
            if is_pipeline_total_signal(features):
                labels["inventory_position"] = True
            if features["pipeline_weighting"]:
                labels["pipeline_weighting"] = True
            if features["pipeline_nonlinear"] or contains_pipeline_ratio(node.value, deps, previous_vars):
                labels["nonlinear_pipeline_composition"] = True
            if contains_partial_adjustment(node.value, deps, previous_vars):
                labels["partial_adjustment"] = True
            if contains_clipping(node.value, deps, previous_vars):
                labels["order_clipping"] = True
            if contains_additive_constant_order(node.value, deps, previous_vars):
                labels["constant_order"] = True
            if contains_order_smoothing(node.value, deps, previous_vars):
                labels["order_smoothing"] = True
            is_gap, fixed_target = positive_part_gap(node.value, deps, previous_vars)
            if is_gap and fixed_target:
                labels["order_up_to"] = True

    # Text fallbacks for common simple forms.
    compact = re.sub(r"\s+", " ", normalize_code(code))
    lower = compact.lower()
    if "on_hand_inventory + sum(pipeline_orders)" in lower:
        labels["inventory_position"] = True
    if re.search(r"\bweights?\s*=", compact, re.I) and re.search(r"zip\s*\(\s*weights?", compact, re.I):
        labels["pipeline_weighting"] = True
    if re.search(r"\b(max|min)\s*\(\s*pipeline_orders\s*\)", compact, re.I):
        labels["nonlinear_pipeline_composition"] = True
    if re.search(r"\b(var|variance|std)\s*\(", compact, re.I) and "pipeline_orders" in lower:
        labels["nonlinear_pipeline_composition"] = True
    if re.search(r"\bpipeline_orders\s*\[[^]]+:[^]]*\]\s*\)", compact) and "/" in compact and "sum(pipeline_orders)" in lower:
        labels["nonlinear_pipeline_composition"] = True
    if any(token in lower for token in CONSTANT_ORDER_TOKENS) and "+" in compact:
        labels["constant_order"] = True
    if re.search(r"\b(min|max)\s*\(", compact) and re.search(r"(max_order|order_cap|cap|min_order|minimum_order)", compact, re.I):
        labels["order_clipping"] = True
    if re.search(r"pipeline_orders\s*\[\s*-\s*1\s*\]", compact) and re.search(r"(previous|prev|last|smooth|delta|beta)", compact, re.I):
        labels["order_smoothing"] = True

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
            row = {
                **meta,
                "generation": generation,
                "rank_in_population_file": rank,
                "objective": objective,
                "test_objective": as_float(item.get("test_objective")),
                "code": code,
                **detect_motifs(code),
            }
            row["motif_count"] = sum(bool(row[motif]) for motif in MOTIFS)
            records.append(row)
    return records


def summarize(records: list[dict[str, Any]], group_cols: list[str] | None = None) -> list[dict[str, Any]]:
    if group_cols is None:
        group_cols = []
    grouped: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        grouped[tuple(record[col] for col in group_cols)].append(record)
    rows: list[dict[str, Any]] = []
    for key, group in sorted(grouped.items()):
        row = {col: value for col, value in zip(group_cols, key)}
        row["n_policies"] = len(group)
        for motif in MOTIFS:
            count = sum(bool(record[motif]) for record in group)
            row[f"{motif}_count"] = count
            row[f"{motif}_pct"] = round(100.0 * count / len(group), 4) if group else 0.0
        row["avg_motif_count"] = round(sum(record["motif_count"] for record in group) / len(group), 4)
        rows.append(row)
    return rows


def top10_by_distribution(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_dist: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        if record["objective"] is not None and record["distribution"] != "unknown":
            by_dist[record["distribution"]].append(record)
    selected: list[dict[str, Any]] = []
    for dist, group in by_dist.items():
        group = sorted(group, key=lambda row: row["objective"])
        k = max(1, math.ceil(0.10 * len(group)))
        for record in group[:k]:
            selected.append({**record, "top10_cutoff_k": k})
    return summarize(selected, ["distribution"])


def final_generation_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    max_gen_by_folder: dict[str, int] = {}
    for record in records:
        folder = record["folder"]
        max_gen_by_folder[folder] = max(max_gen_by_folder.get(folder, -1), int(record["generation"]))
    return [record for record in records if int(record["generation"]) == max_gen_by_folder[record["folder"]]]


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
    label_rows = [
        {
            key: value
            for key, value in record.items()
            if key not in {"code"}
        }
        for record in records
    ]
    write_csv(OUT_LABELS, label_rows)
    overall = summarize(records)
    write_csv(OUT_OVERALL, overall)
    top10 = top10_by_distribution(records)
    write_csv(OUT_TOP10, top10)
    final_records = final_generation_records(records)
    final_summary = summarize(final_records)
    final_by_dist = summarize(final_records, ["distribution"])
    write_csv(OUT_FINAL, final_summary)
    write_csv(OUT_FINAL_BY_DIST, final_by_dist)

    print(f"population_policy_records,{len(records)}")
    print(f"run_folders,{len({record['folder'] for record in records})}")
    print(f"distributions,{len({record['distribution'] for record in records})}")
    print(f"final_generation_policy_records,{len(final_records)}")
    print(f"labels_csv,{OUT_LABELS}")
    print(f"overall_csv,{OUT_OVERALL}")
    print(f"top10_csv,{OUT_TOP10}")
    print(f"final_csv,{OUT_FINAL}")
    print(f"final_by_distribution_csv,{OUT_FINAL_BY_DIST}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
