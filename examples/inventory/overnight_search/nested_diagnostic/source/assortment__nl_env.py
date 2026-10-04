"""Nested-logit hard instances (Guo et al. benchmark).

Revenue function transcribed from their models/nl_functions.py:
    V_i(S_i) = vi0_i + sum_{j in S_i} v_ij          (nest preference)
    prob_i   = V_i^gamma_i / (v0 + sum_k V_k^gamma_k)
    rev_i    = sum_{j in S_i} price_ij * v_ij / V_i
    R(S)     = sum_i prob_i * rev_i

SCORING: the GitHub release ships `best_rev` (best ATTAINABLE revenue found) alongside
`upper_bound` (Kunnumkal's 2023 theoretical bound). We score against `best_rev`. The bound is
tight -- best_rev/upper_bound averages 0.9998 (min 0.9954) over all 971 instances -- so results
scored against either denominator differ by <0.5%. The anonymised copy shipped only the bound
(as `max_rev`) and is not supported here; use the GitHub release (data/README.md).

Decision variable is per-nest: S is an (m, n) binary matrix. cap (when present) limits the
number of offered products FROM EACH NEST (their card_nested_logit; score() enforces
S.sum(axis=1) <= cap, and the frozen prompt states the same per-nest rule).
"""
from __future__ import annotations

import glob
import json
import os
from dataclasses import dataclass

import numpy as np

from mmnl_env import data_root


@dataclass
class NLInstance:
    key: str
    n: int          # products per nest
    m: int          # number of nests
    cap: int | None
    v: np.ndarray       # (m, n) preference weights
    price: np.ndarray   # (m, n)
    v0: float           # outside option
    vi0: np.ndarray     # (m,) within-nest no-purchase weight
    gamma: np.ndarray   # (m,) dissimilarity parameters
    max_rev: float      # scoring denominator: best_rev (GitHub) or upper_bound (anon)
    upper_bound: float = None   # Kunnumkal bound, when available

    def revenue(self, S) -> float:
        S = np.asarray(S, dtype=float).reshape(self.m, self.n)
        V = (S * self.v).sum(axis=1) + self.vi0          # (m,)
        Vg = V ** self.gamma
        prob = Vg / (self.v0 + Vg.sum())
        rev = (self.price * self.v * S).sum(axis=1) / V
        return float((prob * rev).sum())

    def score(self, S) -> float:
        S = np.asarray(S).reshape(self.m, self.n)
        if not np.all((S == 0) | (S == 1)):
            return 0.0
        if self.cap is not None and (S.sum(axis=1) > self.cap).any():
            return 0.0            # cap is PER NEST (their card_nested_logit)
        return self.revenue(S) / self.max_rev

    def config(self) -> str:
        """The shipped configuration this instance came from (stratification key)."""
        return self.key.rsplit(":", 1)[0]

    def public_view(self) -> dict:
        return {"n": self.n, "m": self.m, "cap": self.cap,
                "v": self.v.tolist(), "price": self.price.tolist(),
                "v0": float(self.v0), "vi0": self.vi0.tolist(),
                "gamma": self.gamma.tolist()}


def load(sample: int | None = None, seed: int = 0, max_n: int | None = None):
    out = []
    for f in sorted(glob.glob(os.path.join(data_root(), "nl_*.json"))):
        name = os.path.basename(f).replace("_data.json", "")
        is_card = "card" in name
        d = json.load(open(f))
        for combo, e in d.items():
            n, m, cr = e["n"], e["m"], e["cap_rate"]
            if max_n is not None and n > max_n:
                continue
            # Match initialize_args_nl in the source benchmark. In particular,
            # n=25 and rates .1/.5 allow 3/13 products, not Python's rounded 2/12.
            cap = int(np.ceil(cr * n)) if is_card else None   # PER NEST
            has_gh = "best_rev" in e
            denom = e["best_rev"] if has_gh else e["max_rev"]
            ubs = e.get("upper_bound", denom)
            for k, (inst, opt) in enumerate(zip(e["data"], denom)):
                isd = e["seeds"][k] if k < len(e.get("seeds", [])) else k
                out.append(NLInstance(
                    key=f"{name}:{combo}:seed{isd}", n=n, m=m, cap=cap,
                    v=np.array(inst["v"], dtype=float),
                    price=np.array(inst["price"], dtype=float),
                    v0=float(np.array(inst["v0"]).ravel()[0]),
                    vi0=np.array(inst["vi0"], dtype=float).ravel(),
                    gamma=np.array(inst["gamma"], dtype=float).ravel(),
                    max_rev=float(opt), upper_bound=float(ubs[k])))
    if sample is not None and sample < len(out):
        rng = np.random.default_rng(seed)
        idx = rng.choice(len(out), size=sample, replace=False)
        out = [out[i] for i in sorted(idx)]
    return out


# ---------------- reference heuristics (vectorised) ----------------
def _state(inst, S):
    V = (S * inst.v).sum(axis=1) + inst.vi0
    num = (inst.price * inst.v * S).sum(axis=1)
    return V, num


def _total(inst, V, num):
    Vg = V ** inst.gamma
    return float((Vg * (num / V)).sum() / (inst.v0 + Vg.sum()))


def _add_all(inst, S, V, num):
    """Revenue after adding each candidate (i,j), vectorised -> (m, n). Occupied cells = -inf."""
    Vn = V[:, None] + inst.v                       # (m, n)
    numn = num[:, None] + inst.price * inst.v
    Vg = V ** inst.gamma                           # (m,)
    Vgn = Vn ** inst.gamma[:, None]                # (m, n)
    base = Vg * (num / V)                          # (m,)
    T = base.sum(); sumVg = Vg.sum()
    numer = T - base[:, None] + Vgn * (numn / Vn)
    denom = inst.v0 + sumVg - Vg[:, None] + Vgn
    out = numer / denom
    out[S.astype(bool)] = -np.inf
    if inst.cap is not None:
        full = (S.sum(axis=1) >= inst.cap)
        out[full, :] = -np.inf
    return out


def greedy(inst):
    S = np.zeros((inst.m, inst.n))
    V, num = _state(inst, S)
    cur = _total(inst, V, num)
    budget = inst.m * inst.n if inst.cap is None else inst.cap * inst.m
    for _ in range(budget):
        vals = _add_all(inst, S, V, num)
        k = int(np.argmax(vals)); i, j = divmod(k, inst.n)
        if not np.isfinite(vals[i, j]) or vals[i, j] <= cur + 1e-12:
            break
        S[i, j] = 1; cur = vals[i, j]
        V, num = _state(inst, S)
    return S, cur


def greedy_local(inst, max_iter=40):
    S, cur = greedy(inst)
    for _ in range(max_iter):
        improved = False
        V, num = _state(inst, S)
        vals = _add_all(inst, S, V, num)
        k = int(np.argmax(vals)); i, j = divmod(k, inst.n)
        if np.isfinite(vals[i, j]) and vals[i, j] > cur + 1e-12:
            S[i, j] = 1; cur = vals[i, j]; improved = True
        if not improved:                       # DROP
            on = np.argwhere(S > 0)
            for (i, j) in on:
                S[i, j] = 0
                Vd, nd = _state(inst, S)
                v = _total(inst, Vd, nd)
                if v > cur + 1e-12:
                    cur = v; improved = True; break
                S[i, j] = 1
        if not improved:
            break
    return S, cur


def revenue_ordered(inst):
    """Best combination of independent price prefixes, respecting each nest's cap.

    For candidate revenue z, numerator - z*denominator separates by nest.
    Dinkelbach iteration therefore optimizes the finite prefix family without
    enumerating its Cartesian product. Empty prefixes allow unattractive nests
    to offer no products; their within-nest outside weights still enter V.
    """
    order = np.argsort(-inst.price, axis=1)
    lim = inst.n if inst.cap is None else min(inst.n, int(inst.cap))
    v = np.take_along_axis(inst.v, order, axis=1)[:, :lim]
    p = np.take_along_axis(inst.price, order, axis=1)[:, :lim]
    V = inst.vi0[:, None] + np.pad(np.cumsum(v, axis=1), ((0, 0), (1, 0)))
    attraction = V ** inst.gamma[:, None]
    weighted_price = np.pad(np.cumsum(v * p, axis=1), ((0, 0), (1, 0)))
    numerator = np.divide(weighted_price * attraction, V,
                          out=np.zeros_like(V), where=V > 0)
    nests = np.arange(inst.m)
    z = 0.0
    for _ in range(100):
        lengths = np.argmax(numerator - z * attraction, axis=1)
        value = float(numerator[nests, lengths].sum()
                      / (inst.v0 + attraction[nests, lengths].sum()))
        if abs(value - z) <= 1e-12 * max(1.0, abs(value)):
            S = np.zeros((inst.m, inst.n))
            for i, k in enumerate(lengths):
                S[i, order[i, :k]] = 1
            return S, value
        z = value
    raise RuntimeError("nested-logit price-prefix optimization did not converge")
