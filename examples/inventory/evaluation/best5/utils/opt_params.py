"""
utils/opt_params.py  (Pro v3)

Utilities for extracting and manipulating OPT_PARAM annotations embedded in policy code.

OPT_PARAM format (inline comment on an assignment line):
    x = 120.0  # OPT_PARAM: {"initial": 120.0, "min": 0.0, "max": 600.0, "type": "float"}

This module supports:
- parse_opt_params(code) -> Dict[str, OptParam]
- replace_params_in_code(code, values) -> str
- detect and drop "unused" OPT_PARAM variables (filter_unused_opt_params)
- re-calibrate (min,max,initial) for cross-distribution generalization using *training demand stats*
  (recalibrate_params_for_dataset)
- helpers for vectorization / bound expansion (kept for backward compatibility)

Why v3:
The original OPT_PARAM min/max are often derived on a different demand distribution. For generalization,
we must re-define bounds on the new training data, otherwise tuning either:
- gets trapped at the old initial (flat / non-smooth objective), or
- searches a wildly inappropriate range.

v3 therefore "rebuilds" (min,max,initial) using dataset statistics + name heuristics, and supports
adaptive expansion if the best solution keeps hitting bounds.
"""

from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass
from typing import Dict, Any, List, Tuple


# Match: <indent><name> = <rhs> [# OPT_PARAM: {...}]
_OPT_LINE_RE = re.compile(
    r"^(?P<indent>\s*)(?P<name>[A-Za-z_]\w*)\s*=\s*(?P<rhs>[^#]+?)\s*(?P<comment>#\s*OPT_PARAM:\s*(?P<cfg>\{.*\})\s*)?$"
)

# Keywords used to infer parameter semantics
_SCALE_KEYS = (
    "stock", "base", "safety", "buffer", "target",
    "cap", "max", "order", "inventory", "reorder",
    "level", "demand", "threshold",
)
_PROB_KEYS = (
    "alpha", "beta", "prob", "ratio", "smooth", "smoothing",
)


@dataclass(frozen=True)
class OptParam:
    name: str
    initial: float
    min: float
    max: float
    type: str = "float"  # "float" or "int"


def _loads_json_relaxed(s: str) -> Any:
    """Parse JSON with minimal normalization (single quotes -> double quotes)."""
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
    Replace parameter assignments (only those with OPT_PARAM annotations) with new values.
    Preserves the OPT_PARAM JSON and updates its "initial" field.
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


def _is_prob_like_by_bounds(p: OptParam) -> bool:
    return p.min >= 0.0 and p.max <= 1.0


def _is_prob_like(name: str, p: OptParam) -> bool:
    lname = name.lower()
    if _is_prob_like_by_bounds(p):
        return True
    return any(k in lname for k in _PROB_KEYS)


def _is_scale_like(name: str) -> bool:
    lname = name.lower()
    return any(k in lname for k in _SCALE_KEYS)


def filter_unused_opt_params(code: str, params: Dict[str, OptParam]) -> Dict[str, OptParam]:
    """
    Drop OPT_PARAM variables that are likely unused in the policy logic.

    Heuristic:
    - strip comments (# ...) and count occurrences of the variable token.
    - if it appears <= 1 time, it is only assigned, not referenced.
      (Typical example: base_stock defined but never used.)
    """
    # Remove comments to avoid counting tokens inside OPT_PARAM JSON.
    no_comment = "\n".join([ln.split("#", 1)[0] for ln in code.splitlines()])
    out: Dict[str, OptParam] = {}
    for name, p in params.items():
        hits = re.findall(rf"\b{re.escape(name)}\b", no_comment)
        if len(hits) <= 1:
            # Unused: skip
            continue
        out[name] = p
    return out


def _clip(v: float, lo: float, hi: float) -> float:
    return min(max(v, lo), hi)


def recalibrate_params_for_dataset(
    params: Dict[str, OptParam],
    *,
    mean_d: float,
    std_d: float,
    p95_d: float,
    max_d: float,
    lead_time: int,
) -> Dict[str, OptParam]:
    """
    Rebuild (min, max, initial) using training demand statistics.

    Goals:
    - remove dependence on original distribution-specific OPT_PARAM bounds
    - provide sensible *scale-aware* ranges so the optimizer can move
    - keep probability-like params in [0,1]

    Strategy:
    - prob-like params: [0,1], initial clipped
    - scale-like params:
        * demand_estimate-like -> reference ~ mean_d
        * max_order / cap -> reference ~ max(mean_d, p95_d)
        * safety_stock -> reference ~ max(std_d*sqrt(L+1), 0.1*mean_d, 1)
        * base_stock / target -> reference ~ (L+1)*mean_d + safety_ref
        * thresholds -> reference ~ 0.05*mean_d
      bounds are broad multiples around the reference and also cover (L+1)*max_d
    - other params: keep positivity if original min >= 0, and widen around initial
    """
    L = float(lead_time)
    mean_d = float(mean_d)
    std_d = float(std_d)
    p95_d = float(p95_d)
    max_d = float(max_d)

    # Global scales
    inv_scale = max(mean_d * (L + 1.0), 1.0)
    inv_hi = max(2.0 * max_d * (L + 1.0), 10.0)  # conservative upper scale

    safety_ref = max(std_d * math.sqrt(L + 1.0), 0.10 * mean_d, 1.0)

    out: Dict[str, OptParam] = {}
    for name, p in params.items():
        if _is_prob_like(name, p):
            lo, hi = 0.0, 1.0
            init = _clip(float(p.initial), lo, hi)
            out[name] = OptParam(name=name, initial=init, min=lo, max=hi, type=p.type)
            continue

        lname = name.lower()

        # Decide a reference value (ref) for scale-like parameters
        if _is_scale_like(name):
            if ("demand" in lname) and ("estimate" in lname or "mean" in lname or "forecast" in lname):
                ref = max(mean_d, 1.0)
                lo, hi = 0.0, max(10.0 * ref, inv_hi)
            elif ("order" in lname and ("max" in lname or "cap" in lname)) or ("max_order" in lname):
                ref = max(p95_d, mean_d, 1.0)
                lo, hi = 0.0, max(10.0 * ref, inv_hi)
            elif "safety" in lname:
                ref = safety_ref
                lo, hi = 0.0, max(10.0 * ref, inv_hi)
            elif "threshold" in lname or "min_order" in lname:
                ref = max(0.05 * mean_d, 0.0)
                lo, hi = 0.0, max(5.0 * max(mean_d, 1.0), 100.0)
            else:
                # base_stock / target / generic inventory scale
                ref = inv_scale + safety_ref
                lo, hi = 0.0, max(10.0 * ref, inv_hi)

            # Choose a better dataset-aware initial:
            init0 = float(p.initial)
            if init0 <= 0.0 or init0 < 0.20 * ref or init0 > 5.0 * ref:
                init = ref
            else:
                init = init0

            init = _clip(init, lo, hi)
            out[name] = OptParam(name=name, initial=init, min=lo, max=hi, type=p.type)
            continue

        # Non-scale-like parameters: widen around initial (but keep sign constraints)
        init0 = float(p.initial)
        lo0, hi0 = float(p.min), float(p.max)

        # Ensure finite-ish bounds; if original span is degenerate, create one.
        span = hi0 - lo0
        if span <= 0:
            span = max(1.0, abs(init0) + 1.0)

        # Expand about the initial
        lo = min(lo0, init0 - 5.0 * span)
        hi = max(hi0, init0 + 5.0 * span)

        # If originally nonnegative, enforce nonnegative
        if lo0 >= 0.0:
            lo = 0.0

        if hi <= lo:
            hi = lo + max(1.0, abs(init0) + 1.0)

        init = _clip(init0, lo, hi)
        out[name] = OptParam(name=name, initial=init, min=lo, max=hi, type=p.type)

    return out


# --------- Backward-compatible helpers (used by earlier tuner versions) ---------

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
    Backward-compatible wrapper: in v3 we prefer recalibrate_params_for_dataset.
    """
    return recalibrate_params_for_dataset(
        params,
        mean_d=mean_d,
        std_d=std_d,
        p95_d=p95_d,
        max_d=max_d,
        lead_time=lead_time,
    )


def vectorize(params: Dict[str, OptParam]) -> Tuple[List[str], List[float], List[Tuple[float, float]]]:
    names = sorted(params.keys())
    x0 = [float(params[n].initial) for n in names]
    bounds = [(float(params[n].min), float(params[n].max)) for n in names]
    return names, x0, bounds


def unvectorize(x: List[float], names: List[str], params: Dict[str, OptParam]) -> Dict[str, Any]:
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
            out[n] = float(_clip(v, lo, hi))
    return out


def bound_hits(x: List[float], bounds: List[Tuple[float, float]], *, frac: float = 0.01) -> List[Tuple[int, str]]:
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
    Expand bounds for parameters that hit boundaries.

    v3 keeps this as a simple, conservative expansion rule. The primary mechanism
    is still recalibration (rebuild bounds) + derivative-free search.
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
