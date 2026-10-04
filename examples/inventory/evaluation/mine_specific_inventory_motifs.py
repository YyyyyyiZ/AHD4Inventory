#!/usr/bin/env python3
"""Mine concrete inventory-policy motifs from matched DeepSeek policies."""

from __future__ import annotations

import ast
import bisect
import csv
import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
S3_CSV = Path("/Users/fenghua/Downloads/final results - S 3.csv")
ZIP_POLICIES_JSONL = (
    ROOT / "downloads_policies" / "matched_deepseek_train_policies_m2_only_1pct" / "policies.jsonl"
)
OUT_DIR = ROOT / "examples" / "inventory" / "evaluation" / "specific_motif_mining"
OUT_LABELS = OUT_DIR / "specific_motif_policy_labels.csv"
OUT_SUMMARY = OUT_DIR / "specific_motif_summary.csv"
OUT_RESIDUAL = OUT_DIR / "specific_motif_residual_summary.csv"
OUT_EXAMPLES = OUT_DIR / "specific_motif_niche_examples.csv"

PROMPT_GLOB = "**/deepseek*processed_scipy*default_m2*/prompt_for_code/m2_*.txt"
FOLDER_RE = re.compile(
    r"deepseek[^_]*_(?P<dist>.+?)_50_plain_processed_scipy_15_default_m2(?:-m2-m2)?_(?P<pop>\d+)_r(?P<repeat>\d+)"
)
MEAN_RE = re.compile(r"mean\s*=\s*([0-9]+(?:\.[0-9]+)?)")

STATE_NAMES = {"on_hand_inventory", "inventory", "current_inventory", "I_t", "I"}
PIPE_NAMES = {"pipeline_orders", "pipeline", "pipeline_vector", "Q_t", "Q"}
TARGET_TOKENS = (
    "target",
    "desired",
    "adjusted_base",
    "dynamic_base",
    "reorder_point",
    "base_stock_level",
    "order_up_to",
)
PREV_TOKENS = ("previous", "prev", "last", "prior")
ORDER_TOKENS = ("order", "amount", "quantity", "qty")
CHANGE_TOKENS = ("delta", "change", "smooth", "smoothing", "inertia", "limit", "max_increase", "max_decrease")

SPECIFIC_MOTIFS = [
    "inventory_position_gap",
    "safety_stock_buffer",
    "fractional_gap_closure",
    "absolute_order_cap",
    "order_floor_or_baseline",
    "pipeline_total_discount",
    "pipeline_average_demand_proxy",
    "near_term_pipeline_slice",
    "near_far_pipeline_split",
    "weighted_pipeline_vector",
    "integer_rounding",
    "nonlinear_transform",
    "pipeline_extreme_or_dispersion",
    "coverage_ratio_signal",
    "low_stock_emergency_boost",
]

BROAD_MOTIFS = ["dynamic_target", "pipeline_composition", "order_inertia"]


def mangle_duplicate_headers(headers: list[str]) -> list[str]:
    seen: dict[str, int] = {}
    out: list[str] = []
    for header in headers:
        count = seen.get(header, 0)
        out.append(header if count == 0 else f"{header}.{count}")
        seen[header] = count + 1
    return out


def normalize_code(code: str) -> str:
    try:
        return ast.unparse(ast.parse(code))
    except Exception:
        return code.strip()


def code_hash(code: str) -> str:
    return hashlib.sha256(normalize_code(code).encode("utf-8")).hexdigest()


def load_s3_train_targets() -> dict[str, list[float]]:
    with S3_CSV.open(newline="", encoding="utf-8-sig") as fh:
        rows = list(csv.reader(fh))
    headers = mangle_duplicate_headers(rows[0])
    targets: dict[str, list[float]] = defaultdict(list)
    for row in rows[1:]:
        if len(row) <= 10:
            continue
        if not (
            row[0] == "deepseek-chat"
            and row[5] == "scipy"
            and row[7] == "train"
            and row[10] == "m2"
        ):
            continue
        dist = row[9]
        for col_idx in range(13, min(len(row), len(headers))):
            value = row[col_idx].strip()
            if value:
                targets[dist].append(float(value))
    return {dist: sorted(values) for dist, values in targets.items()}


def within_one_pct(sorted_values: list[float], value: float) -> bool:
    if not sorted_values:
        return False
    idx = bisect.bisect_left(sorted_values, value * 0.99)
    return idx < len(sorted_values) and sorted_values[idx] <= value * 1.01


def extract_prompt_code(text: str) -> str | None:
    section = text.split("Section 4 Historical Policy and Cost Statistics:")[-1]
    match = re.search(
        r"I have one policy with its code as follows:\n(?P<code>.*?)(?:\n\s*Below is the cost statistics|\Z)",
        section,
        re.S,
    )
    if match and match.group("code").strip():
        return match.group("code").strip("\n")

    fallback = re.search(
        r"(def\s+compute_order_amount\s*\(.*?)(?:\n\s*Below is the cost statistics|\n\s*- Average total cost|\Z)",
        section,
        re.S,
    )
    return fallback.group(1).strip("\n") if fallback else None


def load_combined_matched_unique_policies() -> dict[str, dict[str, Any]]:
    targets = load_s3_train_targets()
    policies: dict[str, dict[str, Any]] = {}

    for prompt_path in sorted((ROOT / "examples" / "inventory").glob(PROMPT_GLOB)):
        folder_match = FOLDER_RE.fullmatch(prompt_path.parents[1].name)
        if not folder_match:
            continue
        dist = folder_match.group("dist")
        text = prompt_path.read_text(errors="ignore")
        means = MEAN_RE.findall(text)
        code = extract_prompt_code(text)
        if not means or not code:
            continue
        if not within_one_pct(targets.get(dist, []), float(means[-1])):
            continue

        normalized = normalize_code(code)
        h = code_hash(normalized)
        row = policies.setdefault(
            h,
            {
                "policy_hash": h,
                "code": normalized,
                "sources": set(),
                "distributions": set(),
                "local_prompt_count": 0,
                "zip_matched_train_cells": 0,
            },
        )
        row["sources"].add("local_prompt")
        row["distributions"].add(dist)
        row["local_prompt_count"] += 1

    with ZIP_POLICIES_JSONL.open() as fh:
        for line in fh:
            if not line.strip():
                continue
            record = json.loads(line)
            code = record.get("normalized_policy") or record.get("policy_code") or ""
            if not code:
                continue
            normalized = normalize_code(code)
            h = code_hash(normalized)
            row = policies.setdefault(
                h,
                {
                    "policy_hash": h,
                    "code": normalized,
                    "sources": set(),
                    "distributions": set(),
                    "local_prompt_count": 0,
                    "zip_matched_train_cells": 0,
                },
            )
            row["sources"].add("zip")
            row["zip_matched_train_cells"] += int(record.get("matched_train_cells") or 0)
            for dist in re.split(r"[;,|]", str(record.get("distributions", ""))):
                dist = dist.strip()
                if dist:
                    row["distributions"].add(dist)

    return policies


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


def target_like(name: str) -> bool:
    return any(token in name.lower() for token in TARGET_TOKENS)


def previous_order_like(name: str) -> bool:
    lowered = name.lower()
    return any(token in lowered for token in PREV_TOKENS) and any(token in lowered for token in ORDER_TOKENS)


def change_like(name: str) -> bool:
    return any(token in name.lower() for token in CHANGE_TOKENS)


class FeatureVisitor(ast.NodeVisitor):
    def __init__(self, deps: dict[str, dict[str, bool]], previous_vars: set[str]) -> None:
        self.deps = deps
        self.previous_vars = previous_vars
        self.state = False
        self.pipeline = False
        self.pipeline_composition = False
        self.previous_order = False
        self.change_control = False
        self.minmax = False

    def visit_Name(self, node: ast.Name) -> None:
        if node.id in STATE_NAMES:
            self.state = True
        if node.id in PIPE_NAMES:
            self.pipeline = True
        if node.id in self.previous_vars or previous_order_like(node.id):
            self.previous_order = True
        if change_like(node.id):
            self.change_control = True
        dep = self.deps.get(node.id)
        if dep:
            self.state |= dep["state"]
            self.pipeline |= dep["pipeline"]
            self.pipeline_composition |= dep["pipeline_composition"]
            self.previous_order |= dep["previous_order"]
            self.change_control |= dep["change_control"]
            self.minmax |= dep["minmax"]

    def visit_Subscript(self, node: ast.Subscript) -> None:
        if isinstance(node.value, ast.Name) and node.value.id in PIPE_NAMES:
            self.pipeline = True
            self.pipeline_composition = True
            if is_last_pipeline(node):
                self.previous_order = True
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        if isinstance(node.func, ast.Name):
            name = node.func.id
        elif isinstance(node.func, ast.Attribute):
            name = node.func.attr
        else:
            name = ""
        if name in {"min", "max"}:
            self.minmax = True
        if name in {"max", "min", "sorted"} and any(is_pipeline_expr(arg) for arg in node.args):
            self.pipeline = True
            self.pipeline_composition = True
        if name.lower() in {"var", "variance", "std", "mean", "median", "percentile"} and any(
            is_pipeline_expr(arg) for arg in node.args
        ):
            self.pipeline = True
            self.pipeline_composition = True
        self.generic_visit(node)

    def visit_ListComp(self, node: ast.ListComp) -> None:
        for generator in node.generators:
            if is_pipeline_expr(generator.iter):
                self.pipeline = True
                self.pipeline_composition = True
        self.generic_visit(node)

    def visit_GeneratorExp(self, node: ast.GeneratorExp) -> None:
        for generator in node.generators:
            if is_pipeline_expr(generator.iter):
                self.pipeline = True
                if not isinstance(node.elt, ast.Name):
                    self.pipeline_composition = True
        self.generic_visit(node)


def expr_features(node: ast.AST, deps: dict[str, dict[str, bool]], previous_vars: set[str]) -> dict[str, bool]:
    visitor = FeatureVisitor(deps, previous_vars)
    visitor.visit(node)
    return {
        "state": visitor.state or visitor.pipeline,
        "pipeline": visitor.pipeline,
        "pipeline_composition": visitor.pipeline_composition,
        "previous_order": visitor.previous_order,
        "change_control": visitor.change_control,
        "minmax": visitor.minmax,
    }


def detect_broad_motifs(code: str) -> dict[str, bool]:
    tree = ast.parse(code)
    deps: dict[str, dict[str, bool]] = {}
    previous_vars: set[str] = set()
    labels = {motif: False for motif in BROAD_MOTIFS}

    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            features = expr_features(node.value, deps, previous_vars)
            if is_last_pipeline(node.value):
                features["previous_order"] = True
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        previous_vars.add(target.id)
            if features["pipeline_composition"]:
                labels["pipeline_composition"] = True
            for target in node.targets:
                if not isinstance(target, ast.Name):
                    continue
                deps[target.id] = features
                if target_like(target.id) and features["state"]:
                    labels["dynamic_target"] = True
                if (
                    any(token in target.id.lower() for token in ORDER_TOKENS)
                    and features["previous_order"]
                    and (features["minmax"] or features["change_control"] or change_like(target.id))
                ):
                    labels["order_inertia"] = True
        elif isinstance(node, ast.Return) and node.value is not None:
            features = expr_features(node.value, deps, previous_vars)
            if features["pipeline_composition"]:
                labels["pipeline_composition"] = True
            if features["previous_order"] and (features["minmax"] or features["change_control"]):
                labels["order_inertia"] = True

    return labels


def has_regex(pattern: str, code: str) -> bool:
    return re.search(pattern, code, flags=re.I | re.S) is not None


def detect_specific_motifs(code: str) -> dict[str, bool]:
    compact = re.sub(r"\s+", " ", code)
    lower = compact.lower()

    labels = {motif: False for motif in SPECIFIC_MOTIFS}
    labels["inventory_position_gap"] = (
        "inventory_position" in lower
        and "sum(pipeline_orders)" in lower
        and has_regex(r"max\(\s*0(?:\.0)?\s*,[^)]*(target|base_stock|desired)[^)]*-\s*inventory_position", compact)
    )
    labels["safety_stock_buffer"] = "safety_stock" in lower or has_regex(
        r"(target|desired).*=\s*[^=\n]*(base_stock|base_level)[^=\n]*\+[^=\n]*(buffer|stock)", compact
    )
    labels["fractional_gap_closure"] = (
        has_regex(r"(smoothing|adjustment|order_factor|alpha|gain|fraction)", compact)
        and has_regex(r"(raw_order|gap|target_gap|inventory_gap)", compact)
    ) or has_regex(r"(order_amount|final_order)\s*=\s*[^=\n]*(raw_order|gap)[^=\n]*\*", compact)
    labels["absolute_order_cap"] = (
        has_regex(r"(max_order|order_cap|cap_amount|capacity|upper_bound)", compact)
        and has_regex(r"\bmin\s*\(", compact)
    ) or "clip(" in lower
    labels["order_floor_or_baseline"] = (
        has_regex(r"(min_order|minimum_order|base_order|baseline_order|constant_order)", compact)
        or has_regex(r"\bmax\s*\(\s*(?:[1-9]\d*(?:\.\d+)?|min_order|minimum_order)", compact)
    )
    labels["pipeline_total_discount"] = (
        "pipeline_adjustment" in lower
        or has_regex(r"pipeline_weight", compact)
        or has_regex(r"(target|desired)[^=\n]*=\s*[^=\n]*-\s*[^=\n]*pipeline", compact)
    )
    labels["pipeline_average_demand_proxy"] = (
        has_regex(r"sum\(pipeline_orders\)\s*/\s*len\(pipeline_orders\)", compact)
        or has_regex(r"(avg|average|mean)_?pipeline", compact)
        or (has_regex(r"(demand_estimate|demand_forecast|forecast)", compact) and "pipeline_orders" in lower)
    )
    labels["near_term_pipeline_slice"] = has_regex(r"pipeline_orders\s*\[\s*:\s*\d+", compact) or has_regex(
        r"pipeline_orders\s*\[\s*[012]\s*\]", compact
    )
    labels["near_far_pipeline_split"] = (
        has_regex(r"pipeline_orders\s*\[\s*:\s*\d+", compact)
        and has_regex(r"pipeline_orders\s*\[\s*\d+\s*:", compact)
    ) or ("near" in lower and "far" in lower and "pipeline" in lower)
    labels["weighted_pipeline_vector"] = (
        has_regex(r"weights?\s*=", compact) and has_regex(r"zip\s*\(\s*weights?", compact)
    ) or has_regex(r"weighted_(sum|pipeline|inventory)", compact)
    labels["integer_rounding"] = has_regex(r"\b(round|int|ceil|floor)\s*\(", compact)
    labels["nonlinear_transform"] = has_regex(r"\b(sqrt|log|exp|power)\s*\(", compact) or has_regex(
        r"\*\*\s*(0\.5|2|3)", compact
    )
    labels["pipeline_extreme_or_dispersion"] = has_regex(r"\b(max|min)\s*\(\s*pipeline_orders\s*\)", compact) or (
        has_regex(r"\b(var|variance|std)\s*\(", compact) and "pipeline_orders" in lower
    )
    labels["coverage_ratio_signal"] = "coverage" in lower or (
        "ratio" in lower and ("inventory" in lower or "pipeline" in lower)
    )
    labels["low_stock_emergency_boost"] = (
        has_regex(r"\bif\b[^:\n]*(inventory|position|on_hand)[^:\n]*<", compact)
        and has_regex(r"(emergency|shortage|aggressive|boost|multiplier|critical)", compact)
    )
    return labels


def code_excerpt(code: str, motif: str) -> str:
    keywords = {
        "nonlinear_transform": ("sqrt", "log", "exp", "**"),
        "pipeline_extreme_or_dispersion": ("max(pipeline", "min(pipeline", "var", "std"),
        "coverage_ratio_signal": ("coverage", "ratio"),
        "low_stock_emergency_boost": ("emergency", "shortage", "aggressive", "critical"),
        "near_far_pipeline_split": ("near", "far", "pipeline_orders[:"),
        "order_floor_or_baseline": ("min_order", "minimum_order", "base_order", "baseline"),
        "absolute_order_cap": ("max_order", "cap", "min("),
    }.get(motif, (motif,))
    lines = code.splitlines()
    for idx, line in enumerate(lines):
        lowered = line.lower()
        if any(keyword.lower() in lowered for keyword in keywords):
            start = max(0, idx - 2)
            end = min(len(lines), idx + 4)
            return "\\n".join(lines[start:end])[:700]
    return "\\n".join(lines[:8])[:700]


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        return
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def summarize(labels: list[dict[str, Any]], motifs: list[str]) -> list[dict[str, Any]]:
    n = len(labels)
    rows = []
    for motif in motifs:
        count = sum(bool(row[motif]) for row in labels)
        rows.append({"motif": motif, "count": count, "rate_pct": round(100.0 * count / n, 4)})
    return rows


def main() -> int:
    policies = load_combined_matched_unique_policies()
    labels: list[dict[str, Any]] = []
    examples: list[dict[str, Any]] = []

    for policy in policies.values():
        broad = detect_broad_motifs(policy["code"])
        specific = detect_specific_motifs(policy["code"])
        row = {
            "policy_hash": policy["policy_hash"][:12],
            "sources": "+".join(sorted(policy["sources"])),
            "distributions": ";".join(sorted(policy["distributions"])),
            "local_prompt_count": policy["local_prompt_count"],
            "zip_matched_train_cells": policy["zip_matched_train_cells"],
            **broad,
            **specific,
        }
        row["has_any_broad_kept_motif"] = any(row[motif] for motif in BROAD_MOTIFS)
        row["specific_motif_count"] = sum(bool(row[motif]) for motif in SPECIFIC_MOTIFS)
        labels.append(row)

    write_csv(OUT_LABELS, labels)
    write_csv(OUT_SUMMARY, summarize(labels, BROAD_MOTIFS + SPECIFIC_MOTIFS))

    residual = [row for row in labels if not row["has_any_broad_kept_motif"]]
    write_csv(OUT_RESIDUAL, summarize(residual, SPECIFIC_MOTIFS))

    overall_counts = Counter()
    for row in labels:
        for motif in SPECIFIC_MOTIFS:
            overall_counts[motif] += bool(row[motif])

    code_by_hash = {policy["policy_hash"][:12]: policy["code"] for policy in policies.values()}
    niche_motifs = [motif for motif, count in overall_counts.items() if 0 < count <= max(25, int(0.05 * len(labels)))]
    for motif in sorted(niche_motifs, key=lambda item: (overall_counts[item], item)):
        added = 0
        for row in labels:
            if not row[motif]:
                continue
            examples.append(
                {
                    "motif": motif,
                    "overall_count": overall_counts[motif],
                    "overall_rate_pct": round(100.0 * overall_counts[motif] / len(labels), 4),
                    "policy_hash": row["policy_hash"],
                    "sources": row["sources"],
                    "distributions": row["distributions"],
                    "also_has_broad_kept_motif": row["has_any_broad_kept_motif"],
                    "excerpt": code_excerpt(code_by_hash[row["policy_hash"]], motif),
                }
            )
            added += 1
            if added >= 5:
                break
    write_csv(OUT_EXAMPLES, examples)

    print(f"combined_matched_unique_policy_code,{len(labels)}")
    print(f"residual_without_dynamic_target_pipeline_composition_order_inertia,{len(residual)}")
    print(f"summary_csv,{OUT_SUMMARY}")
    print(f"residual_csv,{OUT_RESIDUAL}")
    print(f"labels_csv,{OUT_LABELS}")
    print(f"niche_examples_csv,{OUT_EXAMPLES}")
    print()
    for row in summarize(labels, SPECIFIC_MOTIFS):
        print(f"{row['motif']},{row['count']},{row['rate_pct']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
