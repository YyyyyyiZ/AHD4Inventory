#!/usr/bin/env python3
from __future__ import annotations

import csv
import math
from pathlib import Path


def fmt_num(x: float) -> str:
    if math.isinf(x):
        return "inf"
    if math.isnan(x):
        return "nan"
    return f"{x:.10g}"


def main() -> None:
    base_dir = Path(__file__).resolve().parent
    in_path = base_dir / "all_best5_merged_train_test.csv"
    out_path = base_dir / "all_best5_merged_train_test_std.csv"

    if not in_path.exists():
        raise FileNotFoundError(f"Missing input CSV: {in_path}")

    with in_path.open(newline="", encoding="utf-8") as fp:
        reader = csv.DictReader(fp)
        if not reader.fieldnames:
            raise ValueError(f"No header found in {in_path}")
        if "demand_variance" not in reader.fieldnames:
            raise KeyError(f"Missing 'demand_variance' column in {in_path}")

        out_cols = [
            "demand_std" if c == "demand_variance" else c
            for c in reader.fieldnames
        ]

        rows = []
        for row in reader:
            variance_str = (row.get("demand_variance") or "").strip()
            variance = float(variance_str)
            if variance < 0.0 and not math.isclose(variance, 0.0, abs_tol=1e-12):
                raise ValueError(f"Negative variance encountered: {variance_str}")

            row["demand_std"] = fmt_num(math.sqrt(max(variance, 0.0)))
            del row["demand_variance"]
            rows.append(row)

    with out_path.open("w", newline="", encoding="utf-8") as fp:
        writer = csv.DictWriter(fp, fieldnames=out_cols)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} rows to {out_path}")


if __name__ == "__main__":
    main()
