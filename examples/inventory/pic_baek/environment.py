"""The Excel contract, with continuous transitions and rounded observations."""
from __future__ import annotations

import hashlib
import io
from pathlib import Path
from zipfile import ZipFile
import xml.etree.ElementTree as ET
import numpy as np
from scipy.stats import truncnorm, sem, t

PARAMS = dict(lead_time=4, lifetime=2, discount=0.95, purchase_cost=9.025,
              holding_cost=1.0, backlog_cost=2.0, disposal_cost=8.0,
              lost_sales_cost=1000.0, max_order=10, max_backlog=10,
              demand_mean=5.0, demand_std=5.0, demand_low=0.0,
              demand_high=10.0, initial_component=5.0, horizon=1000)
MATRIX_HASH = "d3487d26a8340f1a7fbc410e6c563b3af6c67843167958b5a6bb63e11e61b278"


def load_workbook(path):
    ns = {"s": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    with ZipFile(path) as z:
        strings = ["".join(x.itertext()) for x in ET.fromstring(
            z.read("xl/sharedStrings.xml")).findall("s:si", ns)]
        root = ET.fromstring(z.read("xl/worksheets/sheet3.xml"))
        rows = []
        for row in root.findall("s:sheetData/s:row", ns):
            vals = []
            for c in row.findall("s:c", ns):
                v = c.find("s:v", ns)
                if v is None:
                    raise ValueError("Missing demand cell: " + c.attrib["r"])
                vals.append(strings[int(v.text)] if c.get("t") == "s" else float(v.text))
            rows.append(vals)
    assert rows[0] == ["trajectory_id", "trajectory_seed"] + [f"period_{i}" for i in range(1, 1001)]
    a = np.asarray(rows[1:], dtype=np.float64)
    assert a.shape == (200, 1002)
    np.testing.assert_array_equal(a[:, 0], np.arange(1, 201))
    np.testing.assert_array_equal(a[:, 1], np.arange(111, 311))
    d = np.ascontiguousarray(a[:, 2:], dtype="<f8")
    assert np.isfinite(d).all() and d.min() >= 0 and d.max() <= 10
    assert hashlib.sha256(d.tobytes()).hexdigest() == MATRIX_HASH
    np.testing.assert_array_equal(d, sample_demands(111, 200, 1000))
    return d


def sample_demands(seed, paths=200, horizon=1000):
    return np.asarray([truncnorm.rvs(-1, 1, loc=5, scale=5, size=horizon,
                                   random_state=seed+i) for i in range(paths)])


def step(state, action, demand, params=PARAMS):
    s = np.asarray(state, dtype=float)
    if isinstance(action, (bool, np.bool_)) or not np.isscalar(action):
        raise ValueError("Order must be a scalar integer quantity")
    q = float(action)
    if not np.isfinite(q) or q != round(q) or not 0 <= q <= params["max_order"]:
        raise ValueError("Invalid order quantity")
    m = params["lifetime"]
    unmet = demand - s[:m].sum()
    parts = np.array([
        params["purchase_cost"] * q,
        params["holding_cost"] * max(0, s[1:m].sum() - max(0, demand-s[0])),
        params["backlog_cost"] * max(0, unmet),
        params["disposal_cost"] * max(0, s[0]-demand),
        params["lost_sales_cost"] * max(0, unmet-params["max_backlog"]),
    ])
    nxt = np.r_[max(s[1] - max(0, demand-s[0]),
                   -params["max_backlog"] - s[2:m].sum()), s[2:], q]
    return nxt, parts


def evaluate(policy, demands, params=PARAMS):
    totals = np.zeros((len(demands), 5))
    for i, path in enumerate(demands):
        s = np.full(params["lead_time"] + params["lifetime"] - 1,
                    params["initial_component"], dtype=float)
        for k, d in enumerate(path):
            q = policy(tuple(np.rint(s)))
            s, parts = step(s, q, d, params)
            totals[i] += params["discount"] ** k * parts
    return totals


def summarize(values):
    a = np.asarray(values, dtype=float)
    if not np.isfinite(a).all() or len(a) < 2:
        raise ValueError("Need at least two finite path costs")
    mean, se = float(a.mean()), float(sem(a))
    half = float(t.ppf(0.975, len(a)-1) * se)
    return dict(n=len(a), mean=mean, standard_error=se,
                ci95_low=mean-half, ci95_high=mean+half)


def baseline_costs(demands, candidates):
    """Batch score simple references without sharing results with the LLM."""
    n, k = len(demands), len(candidates)
    states = np.full((n, k, 5), 5.0)
    total = np.zeros((n, k))
    values = np.array([c[1] for c in candidates])[None, :]
    kind = np.array([c[0] == "constant" for c in candidates])[None, :]
    for j in range(demands.shape[1]):
        observed = np.rint(states)
        q = np.where(kind, values, np.clip(values-observed.sum(axis=2), 0, 10))
        d = demands[:, j, None]
        a, b = states[:, :, 0], states[:, :, 1]
        unmet = d-a-b
        cost = (9.025*q + np.maximum(0, b-np.maximum(0, d-a))
                + 2*np.maximum(0, unmet) + 8*np.maximum(0, a-d)
                + 1000*np.maximum(0, unmet-10))
        total += 0.95**j * cost
        first = np.maximum(b-np.maximum(0, d-a), -10)
        states = np.concatenate((first[:, :, None], states[:, :, 2:], q[:, :, None]), axis=2)
    return total
