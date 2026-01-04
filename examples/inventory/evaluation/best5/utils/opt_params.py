"""
utils/opt_params.py  (Pro version)

Utilities for extracting and manipulating OPT_PARAM annotations embedded in policy code.

OPT_PARAM annotation format (inline comment on an assignment line):
    x = 120.0  # OPT_PARAM: {"initial": 120.0, "min": 0.0, "max": 600.0, "type": "float"}

Key capabilities
- parse_opt_params(code) -> Dict[str, OptParam]
- replace_params_in_code(code, values) -> str
- bounds adaptation for cross-distribution generalization (adapt_bounds_for_dataset)
- bound expansion when the optimizer hits boundaries (expand_bounds)

Design notes
- We treat parameters with bounds fully inside [0,1] as probability-like and keep their bounds.
- We treat parameters whose names contain inventory/order scale keywords as scale-like and expand
  their upper bounds using demand statistics and lead time.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Dict, Any, List, Tuple


# Match: <indent><name> = <rhs> [# OPT_PARAM: {...}]
_OPT_LINE_RE = re.compile(
    r"^(?P<indent>\s*)(?P<name>[A-Za-z_]\w*)\s*=\s*(?P<rhs>[^#]+?)\s*(?P<comment>#\s*OPT_PARAM:\s*(?P<cfg>\{.*\})\s*)?$"
)


@dataclass(frozen=True)
class OptParam:
    name: str
    initial: float
    min: float
    max: float
    type: str = "float"  # "float" or "int"


def _loads_json_relaxed(s: str) -> Any:
    """
    Attempt to parse JSON with minimal normalization (single quotes -> double quotes).
    """
    s2 = s.strip().replace("'", '"')
    return json.loads(s2)


def parse_opt_params(code: str) -> Dict[str, OptParam]:
    """
    Parse OPT_PARAM configs from code.
    Returns: name -> OptParam
    """
    out: Dict[str, OptParam] = {}
    for line in code.splitlines():
        if "OPT_PARAM:" not in line:
            continue
        m = _OPT_LINE_RE.match(line)
        if not m:
            continue
        name = m.group("name")
        cfg_str = m.group("cfg")
        if not cfg_str:
            continue
        try:
            cfg = _loads_json_relaxed(cfg_str)
        except Exception:
            continue
        if not isinstance(cfg, dict):
            continue
        if not all(k in cfg for k in ("initial", "min", "max")):
            continue

        typ = str(cfg.get("type", "float"))
        try:
            out[name] = OptParam(
                name=name,
                initial=float(cfg["initial"]),
                min=float(cfg["min"]),
                max=float(cfg["max"]),
                type=typ,
            )
        except Exception:
            continue
    return out


def replace_params_in_code(code: str, values: Dict[str, Any]) -> str:
    """
    Replace parameter assignments (only those that have OPT_PARAM annotations) with new values.
    Preserves the OPT_PARAM JSON and updates its "initial" field to the new value.
    """
    lines = code.splitlines()
    for i, line in enumerate(lines):
        if "OPT_PARAM:" not in line:
            continue
        m = _OPT_LINE_RE.match(line)
        if not m:
            continue
        name = m.group("name")
        if name not in values:
            continue

        indent = m.group("indent") or ""
        new_val = values[name]
        cfg_str = m.group("cfg")

        if cfg_str:
            try:
                cfg = _loads_json_relaxed(cfg_str)
                if isinstance(cfg, dict):
                    cfg["initial"] = new_val
                    new_line = f"{indent}{name} = {new_val}  # OPT_PARAM: {json.dumps(cfg)}"
                else:
                    new_line = f"{indent}{name} = {new_val}  # OPT_PARAM: {cfg_str}"
            except Exception:
                new_line = f"{indent}{name} = {new_val}  # OPT_PARAM: {cfg_str}"
        else:
            new_line = f"{indent}{name} = {new_val}"

        lines[i] = new_line

    return "\n".join(lines) + "\n"


# ---------- Bounds logic ----------
_SCALE_KEYS = (
    "stock", "base", "safety", "buffer", "target",
    "cap", "max", "order", "inventory", "reorder",
    "level", "demand",
)


def _is_prob_like(p: OptParam) -> bool:
    return p.min >= 0.0 and p.max <= 1.0


def _is_scale_like(name: str) -> bool:
    lname = name.lower()
    return any(k in lname for k in _SCALE_KEYS)


def adapt_bounds_for_dataset(
    params: Dict[str, OptParam],
    *,
    mean_d: float,
    std_d: float,
    p95_d: float,
    max_d: float,
    lead_time: int,
) -> Dict[str, OptParam]:
    """
    Produce a dataset-adapted parameter dict by expanding bounds where appropriate.

    Scale heuristic:
      scale ~= (L+1) * max( p95, mean + 2*std )
      upper bound target ~= max( 2*(L+1)*max_d, 3*scale, 50 )

    Notes
    - We keep prob-like params unchanged.
    - For scale-like params, we keep min at 0 if original min >= 0 and expand max.
    - For others, we mildly expand the upper bound to reduce over-constraining.
    """
    L = float(lead_time)
    scale = max(p95_d * (L + 1.0), (mean_d + 2.0 * std_d) * (L + 1.0), 10.0)
    scale_hi = max(2.0 * max_d * (L + 1.0), 3.0 * scale, 50.0)

    out: Dict[str, OptParam] = {}
    for name, p in params.items():
        if _is_prob_like(p):
            out[name] = p
            continue

        if _is_scale_like(name):
            new_min = 0.0 if p.min >= 0.0 else p.min
            new_max = max(p.max, scale_hi)
            new_init = min(max(p.initial, new_min), new_max)
            out[name] = OptParam(name=name, initial=new_init, min=new_min, max=new_max, type=p.type)
            continue

        # Mild expansion for non-scale-like params
        span = p.max - p.min
        if span <= 0:
            new_min = 0.0 if p.min >= 0.0 else p.min
            new_max = new_min + max(1.0, abs(p.initial) + 1.0)
        else:
            new_min = 0.0 if p.min >= 0.0 else p.min
            new_max = max(p.max, p.min + 2.0 * span)

        new_init = min(max(p.initial, new_min), new_max)
        out[name] = OptParam(name=name, initial=new_init, min=new_min, max=new_max, type=p.type)

    return out


def vectorize(params: Dict[str, OptParam]) -> Tuple[List[str], List[float], List[Tuple[float, float]]]:
    names = sorted(params.keys())
    x0 = [float(params[n].initial) for n in names]
    bounds = [(float(params[n].min), float(params[n].max)) for n in names]
    return names, x0, bounds


def _clip(v: float, lo: float, hi: float) -> float:
    return min(max(v, lo), hi)


def unvectorize(x: List[float], names: List[str], params: Dict[str, OptParam]) -> Dict[str, Any]:
    """
    Convert a numeric vector into a parameter dict, applying type casting and clipping.
    """
    out: Dict[str, Any] = {}
    for i, n in enumerate(names):
        p = params[n]
        lo, hi = float(p.min), float(p.max)
        v = float(x[i])

        if p.type == "int":
            vv = int(round(v))
            vv = int(_clip(vv, lo, hi))
            out[n] = vv
        else:
            vv = float(_clip(v, lo, hi))
            out[n] = vv
    return out


def bound_hits(x: List[float], bounds: List[Tuple[float, float]], *, frac: float = 0.01) -> List[Tuple[int, str]]:
    """
    Identify parameters that are effectively on the boundary.
    Returns list of (index, 'lower'|'upper').
    """
    hits = []
    for i, (lo, hi) in enumerate(bounds):
        if hi <= lo:
            continue
        xi = float(x[i])
        if (xi - lo) / (hi - lo) <= frac:
            hits.append((i, "lower"))
        if (hi - xi) / (hi - lo) <= frac:
            hits.append((i, "upper"))
    return hits


def expand_bounds(
    params: Dict[str, OptParam],
    names: List[str],
    hits: List[Tuple[int, str]],
    *,
    mean_d: float,
    std_d: float,
    p95_d: float,
    max_d: float,
    lead_time: int,
) -> Dict[str, OptParam]:
    """
    Expand bounds for parameters that hit bounds, based on dataset scale.

    For upper hits:
      max <- max( max*2, max + 0.5*scale_add )
    For lower hits:
      if min >= 0 -> keep at 0; else min <- min*2 (more negative)
    """
    L = float(lead_time)
    scale_add = max(p95_d * (L + 1.0), (mean_d + 2.0 * std_d) * (L + 1.0), 50.0)

    out: Dict[str, OptParam] = dict(params)
    for idx, side in hits:
        name = names[idx]
        p = out[name]
        lo, hi, init = float(p.min), float(p.max), float(p.initial)

        if side == "upper":
            new_max = max(hi * 2.0 if hi > 0 else hi + scale_add, hi + 0.5 * scale_add)
            new_init = min(init, new_max)
            out[name] = OptParam(name=name, initial=new_init, min=lo, max=new_max, type=p.type)

        elif side == "lower":
            new_min = 0.0 if lo >= 0.0 else lo * 2.0
            new_init = max(init, new_min)
            out[name] = OptParam(name=name, initial=new_init, min=new_min, max=hi, type=p.type)

    return out
