"""
utils/policy_exec.py  (Pro version)

Policy compilation and invocation helpers.

We load a policy code string via exec() and extract compute_order_amount callable.

We support both call signatures:
- v2: compute_order_amount(on_hand_inventory=..., pipeline_orders=[...])
- v1: compute_order_amount(current_inventory=..., pipeline_inventory=[...])

We also include a lightweight cache keyed by code string identity (hash) to avoid repeated
exec() within the same process where appropriate (e.g., repeated train/test evaluation
for the same tuned code).
"""

from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass
from typing import Callable, Any, Dict, Optional

import numpy as np


def _code_hash(code: str) -> str:
    return hashlib.sha256(code.encode("utf-8")).hexdigest()


# Simple in-process cache
_FN_CACHE: Dict[str, Callable[..., Any]] = {}


@dataclass
class CompiledPolicy:
    code_hash: str
    fn: Callable[..., Any]


def compile_policy(code: str, *, use_cache: bool = True) -> CompiledPolicy:
    h = _code_hash(code)
    if use_cache and h in _FN_CACHE:
        return CompiledPolicy(code_hash=h, fn=_FN_CACHE[h])

    g: Dict[str, Any] = {"np": np, "math": math, "__builtins__": __builtins__}
    l: Dict[str, Any] = {}
    exec(code, g, l)
    fn = l.get("compute_order_amount") or g.get("compute_order_amount")
    if not callable(fn):
        raise ValueError("compute_order_amount not found in policy code after exec().")

    if use_cache:
        _FN_CACHE[h] = fn
    return CompiledPolicy(code_hash=h, fn=fn)


def call_policy(fn: Callable[..., Any], *, on_hand: float, pipeline: list) -> float:
    """
    Invoke policy and return a nonnegative finite float order quantity.
    """
    try:
        out = fn(on_hand_inventory=on_hand, pipeline_orders=list(pipeline))
    except TypeError:
        out = fn(current_inventory=on_hand, pipeline_inventory=list(pipeline))
    except Exception:
        out = 0.0

    try:
        x = float(out)
    except Exception:
        x = 0.0

    if not np.isfinite(x) or x < 0.0:
        return 0.0
    return x
