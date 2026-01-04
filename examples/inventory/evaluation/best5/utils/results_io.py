"""
utils/results_io.py  (Pro version)

Streaming CSV output + resume support.

A (policy_id, dataset_id) is considered COMPLETE if the CSV contains both
splits: "train" and "test" for that pair.

We load only the columns needed to determine completion for speed.
"""

from __future__ import annotations

from pathlib import Path
from typing import Set, Tuple, Dict, Any, Iterable

import pandas as pd


def load_completed(csv_path: Path) -> Set[Tuple[str, str]]:
    if not csv_path.exists():
        return set()

    df = pd.read_csv(csv_path, usecols=["policy_id", "dataset_id", "split"], dtype=str)
    if df.empty:
        return set()

    done: Set[Tuple[str, str]] = set()
    grouped = df.groupby(["policy_id", "dataset_id"])["split"].apply(lambda s: set(s))
    for (pid, did), splits in grouped.items():
        if "train" in splits and "test" in splits:
            done.add((pid, did))
    return done


def append_rows(csv_path: Path, rows: Iterable[Dict[str, Any]]):
    df_new = pd.DataFrame(list(rows))
    if not csv_path.exists():
        df_new.to_csv(csv_path, index=False)
    else:
        df_new.to_csv(csv_path, mode="a", header=False, index=False)
