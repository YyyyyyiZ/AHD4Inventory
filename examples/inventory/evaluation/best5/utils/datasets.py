"""
utils/datasets.py  (Pro version)

Dataset discovery and loading utilities.

- Discover paired *_train.json / *_test.json files under generalize/
- Load instances from JSON
- Compute pooled demand statistics (selling horizon only)

Notes
- Planning horizon padding and no-cost rule are handled in utils.inventory_sim
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Any, List, Tuple

import numpy as np


def discover_pairs(generalize_dir: Path) -> List[Tuple[str, Path, Path]]:
    train_paths = sorted(generalize_dir.glob("*_train.json"))
    out: List[Tuple[str, Path, Path]] = []
    for tp in train_paths:
        base = tp.name[:-len("_train.json")]
        testp = generalize_dir / f"{base}_test.json"
        if testp.exists():
            out.append((base, tp, testp))
    return out


def load_instances(path: Path) -> List[Dict[str, Any]]:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    return data if isinstance(data, list) else [data]


def demand_stats(instances: List[Dict[str, Any]]) -> Dict[str, float]:
    """
    Pooled stats over instance['demand'] only (selling horizon).
    """
    if not instances:
        return {"mean": 0.0, "std": 0.0, "p95": 0.0, "max": 0.0, "L": 0.0}

    L = int(instances[0].get("lead_time", 0))
    # Flatten all demands
    ds = []
    for inst in instances:
        d = inst.get("demand", [])
        if d:
            ds.extend(d)

    if not ds:
        return {"mean": 0.0, "std": 0.0, "p95": 0.0, "max": 0.0, "L": float(L)}

    arr = np.asarray(ds, dtype=float)
    return {
        "mean": float(arr.mean()),
        "std": float(arr.std(ddof=0)),
        "p95": float(np.quantile(arr, 0.95)),
        "max": float(arr.max()),
        "L": float(L),
    }
