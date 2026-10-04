#!/usr/bin/env python3
"""
Merge basestock performance into cost_matrix CSVs without modifying originals.

Outputs new CSVs in a separate directory (default: ./with_basestock).
"""
from __future__ import annotations

import argparse
import csv
import os
import re
from pathlib import Path
from typing import Dict, List, Tuple


DATASET_COL = "dataset"
SOURCE_FILE_COL = "source_file"


def normalize_dataset_id(s: str) -> str:
    """Strip a trailing '.json' if present (only at the end)."""
    s = str(s)
    return re.sub(r"\.json$", "", s)


def build_join_id_from_source_file(source_file: str, L: int, p_str: str) -> str:
    """Build the cost-matrix-style dataset id from a summary row's source_file."""
    s = normalize_dataset_id(source_file)
    s2, n = re.subn(r"_L\d+_c\d+_\d+_", f"_L{L}_p{p_str}_", s)
    if n == 0:
        return s
    return s2


def discover_cost_files(cost_dir: Path) -> List[Tuple[Path, int, str]]:
    out: List[Tuple[Path, int, str]] = []
    pat = re.compile(r"^cost_matrix_L(?P<L>\d+)_p(?P<p>[0-9]+(?:\.[0-9]+)?)\.csv$")
    for f in sorted(cost_dir.iterdir()):
        if not f.is_file():
            continue
        m = pat.match(f.name)
        if not m:
            continue
        L = int(m.group("L"))
        p_str = m.group("p")
        out.append((f, L, p_str))
    return out


def read_summary_map(
    summary_path: Path, L: int, p_str: str, baseline_col: str
) -> Dict[str, str]:
    """Return join_id -> basestock cost string (keeps original formatting)."""
    with summary_path.open(newline="") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None:
            raise ValueError(f"No header in summary file: {summary_path}")
        if baseline_col not in reader.fieldnames:
            raise ValueError(f"Missing baseline col '{baseline_col}' in {summary_path}")

        use_source_file = SOURCE_FILE_COL in reader.fieldnames
        join_map: Dict[str, str] = {}
        for row in reader:
            if use_source_file:
                join_id = build_join_id_from_source_file(row[SOURCE_FILE_COL], L, p_str)
            else:
                join_id = normalize_dataset_id(row.get(DATASET_COL, ""))
            if join_id:
                join_map[join_id] = row.get(baseline_col, "")
        return join_map


def merge_one(
    cost_path: Path,
    summary_path: Path,
    out_path: Path,
    L: int,
    p_str: str,
    baseline_col: str,
) -> Tuple[int, int]:
    """Return (n_rows, n_matched)."""
    join_map = read_summary_map(summary_path, L, p_str, baseline_col)

    with cost_path.open(newline="") as f_in, out_path.open("w", newline="") as f_out:
        reader = csv.DictReader(f_in)
        if reader.fieldnames is None:
            raise ValueError(f"No header in cost file: {cost_path}")

        fieldnames = list(reader.fieldnames)
        if DATASET_COL not in fieldnames:
            # Treat first column as dataset
            fieldnames[0] = DATASET_COL

        out_fieldnames = fieldnames[:]
        if baseline_col not in out_fieldnames:
            out_fieldnames.append(baseline_col)

        writer = csv.DictWriter(f_out, fieldnames=out_fieldnames)
        writer.writeheader()

        n_rows = 0
        n_matched = 0
        for row in reader:
            n_rows += 1
            ds = row.get(DATASET_COL, "")
            base = join_map.get(str(ds), "")
            if base != "":
                n_matched += 1
            row[baseline_col] = base
            writer.writerow(row)

    return n_rows, n_matched


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--cost-dir",
        type=str,
        default=None,
        help="Directory with cost_matrix_L{L}_p{p}.csv files. Default: script directory.",
    )
    parser.add_argument(
        "--generalize-dir",
        type=str,
        default=None,
        help="Directory with basestock_constant_summary_L{L}_p{p}.csv files. "
             "Default: sibling 'generalize' folder.",
    )
    parser.add_argument(
        "--out-dir",
        type=str,
        default=None,
        help="Output directory for merged CSVs. Default: <cost-dir>/with_basestock.",
    )
    parser.add_argument(
        "--baseline-col",
        type=str,
        default="avg_cost_basestock",
        help="Column name to merge from summary CSV.",
    )
    args = parser.parse_args()

    here = Path(__file__).resolve().parent
    cost_dir = Path(args.cost_dir).resolve() if args.cost_dir else here
    generalize_dir = Path(args.generalize_dir).resolve() if args.generalize_dir else (here.parent / "generalize")
    out_dir = Path(args.out_dir).resolve() if args.out_dir else (cost_dir / "with_basestock")

    if not cost_dir.exists():
        raise FileNotFoundError(f"cost-dir not found: {cost_dir}")
    if not generalize_dir.exists():
        raise FileNotFoundError(f"generalize-dir not found: {generalize_dir}")

    os.makedirs(out_dir, exist_ok=True)

    cost_files = discover_cost_files(cost_dir)
    if not cost_files:
        raise FileNotFoundError(f"No cost_matrix_L{{L}}_p{{p}}.csv files found in: {cost_dir}")

    total_rows = 0
    total_matched = 0
    for cost_path, L, p_str in cost_files:
        summary_name = f"basestock_constant_summary_L{L}_p{p_str}.csv"
        summary_path = generalize_dir / summary_name
        if not summary_path.exists():
            print(f"[SKIP] Missing summary: {summary_path}")
            continue

        out_path = out_dir / cost_path.name
        n_rows, n_matched = merge_one(cost_path, summary_path, out_path, L, p_str, args.baseline_col)
        total_rows += n_rows
        total_matched += n_matched
        print(f"[OK] {cost_path.name} -> {out_path} | matched {n_matched}/{n_rows}")

    if total_rows > 0:
        print(f"[DONE] Total matched {total_matched}/{total_rows} rows.")


if __name__ == "__main__":
    main()
