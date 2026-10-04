#!/usr/bin/env python3
"""Match S3 train policy cells against local DeepSeek prompts plus downloaded zip matches."""

from __future__ import annotations

import bisect
import csv
import re
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
S3_CSV = Path("/Users/fenghua/Downloads/final results - S 3.csv")
ZIP_MATCH_DIR = ROOT / "downloads_policies" / "matched_deepseek_train_policies_m2_only_1pct"
ZIP_MATCHES_CSV = ZIP_MATCH_DIR / "matches.csv"
OUT_DIST = ROOT / "examples" / "inventory" / "evaluation" / "s3_train_match_with_download_zip_by_distribution.csv"
OUT_GEN = ROOT / "examples" / "inventory" / "evaluation" / "s3_train_match_with_download_zip_by_distribution_generation.csv"
OUT_UNMATCHED = ROOT / "examples" / "inventory" / "evaluation" / "s3_train_match_with_download_zip_unmatched_cells.csv"

PROMPT_GLOB = "**/deepseek*processed_scipy*default_m2*/prompt_for_code/m2_*.txt"
FOLDER_RE = re.compile(
    r"deepseek[^_]*_(?P<dist>.+?)_50_plain_processed_scipy_15_default_m2(?:-m2-m2)?_(?P<pop>\d+)_r(?P<repeat>\d+)"
)
MEAN_RE = re.compile(r"mean\s*=\s*([0-9]+(?:\.[0-9]+)?)")


def mangle_duplicate_headers(headers: list[str]) -> list[str]:
    seen: dict[str, int] = {}
    out: list[str] = []
    for header in headers:
        count = seen.get(header, 0)
        out.append(header if count == 0 else f"{header}.{count}")
        seen[header] = count + 1
    return out


def load_local_prompt_costs() -> dict[str, list[float]]:
    costs: dict[str, set[float]] = defaultdict(set)
    parsed = 0
    failures = 0

    for prompt_path in sorted((ROOT / "examples" / "inventory").glob(PROMPT_GLOB)):
        folder_name = prompt_path.parents[1].name
        folder_match = FOLDER_RE.fullmatch(folder_name)
        if not folder_match:
            failures += 1
            continue

        means = MEAN_RE.findall(prompt_path.read_text(errors="ignore"))
        if not means:
            failures += 1
            continue

        costs[folder_match.group("dist")].add(round(float(means[-1]), 6))
        parsed += 1

    return {dist: sorted(values) for dist, values in costs.items()}, parsed, failures


def parse_float(value: str) -> float | None:
    value = value.strip()
    if not value:
        return None
    try:
        return float(value)
    except ValueError:
        return None


def load_s3_train_cells() -> dict[tuple[int, str], dict[str, object]]:
    cells: dict[tuple[int, str], dict[str, object]] = {}
    with S3_CSV.open(newline="", encoding="utf-8-sig") as fh:
        rows = list(csv.reader(fh))

    headers = mangle_duplicate_headers(rows[0])
    for csv_row, row in enumerate(rows[1:], start=2):
        if len(row) < 13:
            continue
        llm, problem, n_train, p, _initial, external_opt = row[:6]
        generation, split, algo_performance, dist, op = row[6], row[7], row[8], row[9], row[10]
        if not (
            llm == "deepseek-chat"
            and problem == "inventory"
            and n_train == "50"
            and p == "1"
            and external_opt == "scipy"
            and split == "train"
            and algo_performance == "processed"
            and op == "m2"
        ):
            continue

        for col_idx in range(13, min(len(row), len(headers))):
            target = parse_float(row[col_idx])
            if target is None:
                continue
            column = headers[col_idx]
            cells[(csv_row, column)] = {
                "csv_row": csv_row,
                "distribution": dist,
                "generation": int(generation),
                "column": column,
                "target_performance": target,
            }
    return cells


def has_within_one_pct(sorted_values: list[float], target: float) -> bool:
    if not sorted_values:
        return False
    lo = target * 0.99
    hi = target * 1.01
    idx = bisect.bisect_left(sorted_values, lo)
    return idx < len(sorted_values) and sorted_values[idx] <= hi


def load_zip_match_keys(cells: dict[tuple[int, str], dict[str, object]]) -> tuple[set[tuple[int, str]], int, int]:
    if not ZIP_MATCHES_CSV.exists():
        return set(), 0, 0
    keys: set[tuple[int, str]] = set()
    missing_s3_cells = 0
    dist_mismatches = 0
    with ZIP_MATCHES_CSV.open(newline="", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            if row.get("matched") not in {"1", "True", "true"}:
                continue
            try:
                csv_row = int(row["csv_row"])
            except (TypeError, ValueError):
                continue
            column = row.get("column", "")
            if not column:
                continue
            key = (csv_row, column)
            cell = cells.get(key)
            if cell is None:
                missing_s3_cells += 1
                continue
            if row.get("dist") != cell["distribution"]:
                dist_mismatches += 1
                continue
            keys.add(key)
    return keys, missing_s3_cells, dist_mismatches


def pct(num: int, den: int) -> float:
    return round(100.0 * num / den, 6) if den else 0.0


def main() -> int:
    local_costs, parsed_prompts, parse_failures = load_local_prompt_costs()
    cells = load_s3_train_cells()
    zip_keys, missing_s3_zip_matches, zip_dist_mismatches = load_zip_match_keys(cells)

    rows = []
    unmatched_rows = []
    by_dist: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    by_gen: dict[tuple[str, int], dict[str, int]] = defaultdict(lambda: defaultdict(int))

    for key, cell in cells.items():
        dist = str(cell["distribution"])
        generation = int(cell["generation"])
        target = float(cell["target_performance"])
        local_match = has_within_one_pct(local_costs.get(dist, []), target)
        zip_match = key in zip_keys
        combined_match = local_match or zip_match

        for bucket in (by_dist[dist], by_gen[(dist, generation)]):
            bucket["target_train_cells"] += 1
            bucket["local_prompt_matched_cells"] += int(local_match)
            bucket["zip_matched_cells"] += int(zip_match)
            bucket["combined_matched_cells"] += int(combined_match)
            bucket["overlap_cells"] += int(local_match and zip_match)
            bucket["local_only_cells"] += int(local_match and not zip_match)
            bucket["zip_only_cells"] += int(zip_match and not local_match)

        if not combined_match:
            unmatched_rows.append(
                {
                    "csv_row": cell["csv_row"],
                    "distribution": dist,
                    "generation": generation,
                    "column": cell["column"],
                    "target_performance": target,
                }
            )

    for dist, bucket in sorted(by_dist.items()):
        den = bucket["target_train_cells"]
        rows.append(
            {
                "distribution": dist,
                "target_train_cells": den,
                "local_prompt_matched_cells": bucket["local_prompt_matched_cells"],
                "zip_matched_cells": bucket["zip_matched_cells"],
                "combined_matched_cells": bucket["combined_matched_cells"],
                "combined_match_pct": pct(bucket["combined_matched_cells"], den),
                "local_prompt_match_pct": pct(bucket["local_prompt_matched_cells"], den),
                "zip_match_pct": pct(bucket["zip_matched_cells"], den),
                "overlap_cells": bucket["overlap_cells"],
                "local_only_cells": bucket["local_only_cells"],
                "zip_only_cells": bucket["zip_only_cells"],
            }
        )

    gen_rows = []
    for (dist, generation), bucket in sorted(by_gen.items()):
        den = bucket["target_train_cells"]
        gen_rows.append(
            {
                "distribution": dist,
                "generation": generation,
                "target_train_cells": den,
                "local_prompt_matched_cells": bucket["local_prompt_matched_cells"],
                "zip_matched_cells": bucket["zip_matched_cells"],
                "combined_matched_cells": bucket["combined_matched_cells"],
                "combined_match_pct": pct(bucket["combined_matched_cells"], den),
                "local_prompt_match_pct": pct(bucket["local_prompt_matched_cells"], den),
                "zip_match_pct": pct(bucket["zip_matched_cells"], den),
                "overlap_cells": bucket["overlap_cells"],
                "local_only_cells": bucket["local_only_cells"],
                "zip_only_cells": bucket["zip_only_cells"],
            }
        )

    OUT_DIST.parent.mkdir(parents=True, exist_ok=True)
    with OUT_DIST.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    with OUT_GEN.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(gen_rows[0]))
        writer.writeheader()
        writer.writerows(gen_rows)

    with OUT_UNMATCHED.open("w", newline="", encoding="utf-8") as fh:
        fieldnames = ["csv_row", "distribution", "generation", "column", "target_performance"]
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(unmatched_rows)

    total = sum(row["target_train_cells"] for row in rows)
    combined = sum(row["combined_matched_cells"] for row in rows)
    local = sum(row["local_prompt_matched_cells"] for row in rows)
    zip_matched = sum(row["zip_matched_cells"] for row in rows)

    print(f"local_prompt_files_parsed,{parsed_prompts}")
    print(f"local_prompt_parse_failures,{parse_failures}")
    print(f"zip_missing_s3_cells,{missing_s3_zip_matches}")
    print(f"zip_dist_mismatches_excluded,{zip_dist_mismatches}")
    print(f"target_train_cells,{total}")
    print(f"local_prompt_matched_cells,{local}")
    print(f"zip_matched_cells,{zip_matched}")
    print(f"combined_matched_cells,{combined}")
    print(f"combined_match_pct,{pct(combined, total)}")
    print(f"distribution_summary,{OUT_DIST}")
    print(f"distribution_generation_summary,{OUT_GEN}")
    print(f"unmatched_cells,{OUT_UNMATCHED}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
