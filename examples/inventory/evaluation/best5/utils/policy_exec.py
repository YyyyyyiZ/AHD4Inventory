"""
utils/policy_exec.py  (Pro v3)

Policy compilation and invocation helpers.

We support both call signatures:
- v2: compute_order_amount(on_hand_inventory=..., pipeline_orders=[...])
- v1: compute_order_amount(current_inventory=..., pipeline_inventory=[...])

v3 adds **parametric compilation** for tuning:
- Instead of rewriting code and re-exec() for every candidate parameter vector, we:
  1) replace OPT_PARAM assignment RHS with __PARAMS__["name"]
  2) exec() ONCE to obtain compute_order_amount that reads from __PARAMS__
  3) update __PARAMS__ dict for each candidate and run simulation
This is substantially faster and also avoids many failure modes from repeatedly exec()'ing code.
"""

from __future__ import annotations

import hashlib
import math
import re
from dataclasses import dataclass
from typing import Callable, Any, Dict, List

import numpy as np


def _code_hash(code: str) -> str:
    return hashlib.sha256(code.encode("utf-8")).hexdigest()


# Simple in-process cache for non-parametric compilation
_FN_CACHE: Dict[str, Callable[..., Any]] = {}


@dataclass
class CompiledPolicy:
    code_hash: str
    fn: Callable[..., Any]


@dataclass
class ParametricPolicy:
    code_hash: str
    fn: Callable[..., Any]
    params: Dict[str, Any]


def compile_policy(code: str, *, use_cache: bool = True) -> CompiledPolicy:
    """
    Compile policy code (non-parametric). Suitable for final evaluation.
    """
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


# Match lines like: name = ... # OPT_PARAM: {...}
_OPT_ASSIGN_RE = re.compile(
    r"^(?P<indent>\s*)(?P<name>[A-Za-z_]\w*)\s*=\s*(?P<rhs>[^#]+?)\s*(?P<comment>#\s*OPT_PARAM:.*)?$"
)


def make_parametric_code(code: str, param_names: List[str]) -> str:
    """
    Replace OPT_PARAM assignment RHS with __PARAMS__["<name>"] for the provided param_names.
    Keeps the OPT_PARAM comment (harmless) so the code is still self-describing.
    """
    names = set(param_names)
    out_lines = []
    for line in code.splitlines():
        if "OPT_PARAM:" not in line:
            out_lines.append(line)
            continue
        m = _OPT_ASSIGN_RE.match(line)
        if not m:
            out_lines.append(line)
            continue
        name = m.group("name")
        if name not in names:
            out_lines.append(line)
            continue
        indent = m.group("indent") or ""
        comment = m.group("comment") or ""
        # Use __PARAMS__ lookup
        new_line = f'{indent}{name} = __PARAMS__["{name}"]'
        if comment:
            new_line += f"  {comment.strip()}"
        out_lines.append(new_line)
    return "\n".join(out_lines) + "\n"


def compile_parametric_policy(code: str, param_names: List[str], init_params: Dict[str, Any]) -> ParametricPolicy:
    """
    Compile a parametric policy that reads OPT_PARAM values from a mutable __PARAMS__ dict.

    Returns ParametricPolicy(fn, params_dict). Update policy.params[name] to change parameters.
    """
    params_dict = dict(init_params)  # mutable
    code2 = make_parametric_code(code, param_names)
    h = _code_hash(code2)

    g: Dict[str, Any] = {"np": np, "math": math, "__PARAMS__": params_dict, "__builtins__": __builtins__}
    l: Dict[str, Any] = {}
    exec(code2, g, l)
    fn = l.get("compute_order_amount") or g.get("compute_order_amount")
    if not callable(fn):
        raise ValueError("compute_order_amount not found in parametric policy code after exec().")

    return ParametricPolicy(code_hash=h, fn=fn, params=params_dict)


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
