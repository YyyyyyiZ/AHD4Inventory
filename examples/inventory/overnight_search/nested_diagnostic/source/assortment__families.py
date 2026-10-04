"""
The three assortment families behind one interface, so the two harnesses (run_l2 write-once,
run_l1 instance-level) contain no per-family branching.

Each family provides:
  load()               the evaluation instances
  call_solve(fn, inst) invoke a submitted solve() with that family's signature
  to_S(decision, inst) convert an arm-I FINAL-line decision into the family's S shape
  sandbox_data(inst)   the arrays preloaded for arm I -- keys match the frozen prompt's list
  denominator(inst)    scoring denominator, or None when only best-known-at-analysis applies

`score` handling: revenue and feasibility are always recorded; a ratio is recorded only where
the family ships a denominator (MMNL max_rev, NL best_rev, certified constrained optima).
Constrained pools at n > 50 carry no certified optimum by design (EXPERIMENT_DESIGN.md 10.4) --
their denominators are assembled at analysis time from best-known across all methods.
"""
from __future__ import annotations

import re

import numpy as np


def _as_index_list(S):
    return [int(x) for x in np.asarray(S).ravel().tolist()]


class _MMNL:
    key = "mmnl"

    def load(self):
        import mmnl_env
        return mmnl_env.load()

    def call_solve(self, fn, inst):
        return _as_index_list(fn(inst.u, inst.price, inst.v0, inst.omega, inst.cap))

    def to_S(self, decision, inst):
        return _as_index_list(decision)

    def sandbox_data(self, inst):
        return inst.public_view()

    def denominator(self, inst):
        return inst.max_rev

    def revenue(self, inst, S):
        return inst.revenue(S)

    def feasible(self, inst, S):
        S = list(S)
        return (len(set(S)) == len(S) and all(0 <= i < inst.n for i in S)
                and (inst.cap is None or len(S) <= inst.cap))


class _NL:
    key = "nl"

    def load(self):
        import nl_env
        return nl_env.load()

    def call_solve(self, fn, inst):
        return np.asarray(fn(inst.v, inst.price, inst.v0, inst.vi0, inst.gamma, inst.cap),
                          dtype=float)

    def to_S(self, decision, inst):
        """Arm-I decisions are (nest, product) pairs."""
        S = np.zeros((inst.m, inst.n))
        for i, j in decision:
            S[int(i), int(j)] = 1
        return S

    def sandbox_data(self, inst):
        return inst.public_view()

    def denominator(self, inst):
        return inst.max_rev

    def revenue(self, inst, S):
        S = np.asarray(S, dtype=float).reshape(inst.m, inst.n)
        if not np.all((S == 0) | (S == 1)):
            raise ValueError("offer matrix must be binary")
        return inst.revenue(S)

    def feasible(self, inst, S):
        S = np.asarray(S, dtype=float).reshape(inst.m, inst.n)
        if not np.all((S == 0) | (S == 1)):
            return False
        return inst.cap is None or not (S.sum(axis=1) > inst.cap).any()


class _ConstrainedMMNL:
    key = "mmnl_c"

    def load(self):
        import build_constrained
        return build_constrained.load_built()

    def call_solve(self, fn, inst):
        return _as_index_list(fn(inst.u, inst.price, inst.v0, inst.omega, inst.A, inst.B))

    def to_S(self, decision, inst):
        return _as_index_list(decision)

    def sandbox_data(self, inst):
        return {"u": inst.u.tolist(), "price": inst.price.tolist(), "v0": inst.v0.tolist(),
                "omega": inst.omega.tolist(), "A": inst.A.tolist(), "B": inst.B.tolist(),
                "n": inst.n, "m": inst.m}

    def denominator(self, inst):
        return inst.opt          # None for uncertified (n > 50) pools

    def revenue(self, inst, S):
        return inst.revenue(S)

    def feasible(self, inst, S):
        return inst.feasible(S)


FAMILIES = {f.key: f for f in (_MMNL(), _NL(), _ConstrainedMMNL())}


def one_per_config(instances):
    """The lowest-generation-seed instance in every shipped configuration (2026-08-13 rule:
    deterministic, trivially describable, and the seed label cannot correlate with difficulty
    within a config -- it is just the authors' generation RNG seed)."""
    def seed_no(inst):
        m = re.search(r"seed(\d+)$", inst.key)
        return int(m.group(1)) if m else 0
    groups = {}
    for inst in instances:
        c = inst.config()
        if c not in groups or seed_no(inst) < seed_no(groups[c]):
            groups[c] = inst
    return [groups[c] for c in sorted(groups)]


def lowest_k_seeds(instances, k=2):
    """The k lowest-source-seed instances in every configuration (2026-08-14 rule for the
    constrained family: covers the FULL (m, n) grid rather than only the certified n=50
    slice; the seed label is the source generator's RNG seed, so the rule is a priori and
    cannot select on difficulty). Ties broken by key string."""
    def seed_no(inst):
        m = re.search(r"seed(\d+)", inst.key)
        return int(m.group(1)) if m else 0
    groups = {}
    for inst in instances:
        groups.setdefault(inst.config(), []).append(inst)
    out = []
    for c in sorted(groups):
        out += sorted(groups[c], key=lambda i: (seed_no(i), i.key))[:k]
    return out


def stratified_sample(instances, k=40, seed=0):
    """Deterministic stratified sample: group by shipped configuration, round-robin across
    groups (each group's order shuffled by the seeded rng) until k instances are drawn."""
    rng = np.random.default_rng(seed)
    groups = {}
    for inst in instances:
        groups.setdefault(inst.config(), []).append(inst)
    pools = [list(g) for _, g in sorted(groups.items())]
    for g in pools:
        rng.shuffle(g)
    out = []
    i = 0
    while len(out) < min(k, len(instances)):
        pool = pools[i % len(pools)]
        if pool:
            out.append(pool.pop())
        i += 1
        if all(not p for p in pools):
            break
    return out
