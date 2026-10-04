"""Prespecified fresh-family probe with an exhaustive finite-set oracle.

This is diagnostic oracle computation, NOT AIPS training or performance.
All 80 instances are reported. Four generator regimes x 20 seeds, with seeds
0..9 designated discovery and 10..19 held out before evaluating either split.
No generator fitting or hyperparameter selection is performed.
"""
import importlib.util
import json
import time
from pathlib import Path

import numpy as np

from audit import ROOT, SOURCE, scalar_revenue, is_feasible


def generate(regime, seed):
    rng = np.random.default_rng(91626000 + seed)
    m, n, cap = 2, 20, 10
    if regime == "independent":
        v = np.exp(rng.normal(0, 1.5, (m, n)))
        price = np.exp(rng.normal(1, 1.2, (m, n)))
    elif regime == "anticorrelated":
        quality = rng.normal(0, 2, (m, n))
        v = np.exp(quality)
        price = np.exp(1 - 0.8 * quality + rng.normal(0, 0.4, (m, n)))
    elif regime == "clustered":
        classes = rng.integers(0, 4, (m, n))
        quality = rng.normal(0, 2, (m, 4))
        levels = rng.normal(1, 1.5, (m, 4))
        v = np.exp(np.take_along_axis(quality, classes, 1) + rng.normal(0, 0.15, (m, n)))
        price = np.exp(np.take_along_axis(levels, classes, 1) + rng.normal(0, 0.15, (m, n)))
    elif regime == "heterogeneous_nests":
        scales = rng.normal(0, 3, (m, 1))
        v = np.exp(scales + rng.normal(0, 1.5, (m, n)))
        price = np.exp(1 - 0.5 * scales + rng.normal(0, 1.2, (m, n)))
    else:
        raise ValueError(regime)
    return dict(key=f"{regime}:{seed}", n=n, m=m, cap=cap, v=v, price=price,
                vi0=np.exp(rng.normal(0, 2, m)), v0=float(np.exp(rng.normal(1, 2))),
                gamma=rng.uniform(0.15, 0.99, m))


def exact(instance):
    """Enumerate every feasible subset per nest; solve their ratio exactly."""
    count = np.array([0], dtype=np.uint8)
    for _ in range(instance["n"]):
        count = np.concatenate((count, count + 1))
    masks = np.flatnonzero(count <= instance["cap"])
    arrays = []
    for i in range(instance["m"]):
        W, A = np.array([instance["vi0"][i]]), np.array([0.0])
        for j in range(instance["n"]):
            W = np.concatenate((W, W + instance["v"][i, j]))
            A = np.concatenate((A, A + instance["v"][i, j] * instance["price"][i, j]))
        W, A = W[masks], A[masks]
        attraction = W ** instance["gamma"][i]
        arrays.append((A * attraction / W, attraction))
    z = 0.0
    for iteration in range(100):
        choices = [int(np.argmax(N - z * D)) for N, D in arrays]
        new_z = sum(N[k] for (N, D), k in zip(arrays, choices)) / (
            instance["v0"] + sum(D[k] for (N, D), k in zip(arrays, choices)))
        if abs(new_z - z) < 1e-12 * max(1, abs(new_z)):
            break
        z = new_z
    else:
        raise RuntimeError("Exact finite-set ratio solver failed to converge.")
    offers = np.array([[(int(masks[k]) >> j) & 1 for j in range(instance["n"])] for k in choices])
    assert is_feasible(instance, offers)
    assert abs(scalar_revenue(instance, offers) - new_z) < 1e-10 * max(1, abs(new_z))
    residual = sum(float(np.max(N - new_z * D)) for N, D in arrays) - new_z * instance["v0"]
    assert abs(residual) < 1e-8 * max(1, abs(new_z))
    return new_z, offers, residual


def main():
    spec = importlib.util.spec_from_file_location("frozen_baek", SOURCE / "baek_l2_original.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    outpath = ROOT / "synthetic_results.jsonl"
    rows = [json.loads(s) for s in outpath.read_text().splitlines()] if outpath.exists() else []
    seen = {row["key"] for row in rows}
    with outpath.open("a") as out:
        for regime in ("independent", "anticorrelated", "clustered", "heterogeneous_nests"):
            for seed in range(20):
                instance = generate(regime, seed)
                if instance["key"] in seen:
                    continue
                start = time.perf_counter()
                S = np.asarray(mod.solve(*(instance[k] for k in ("v", "price", "v0", "vi0", "gamma", "cap"))))
                seconds = time.perf_counter() - start
                assert is_feasible(instance, S)
                revenue = scalar_revenue(instance, S)
                start = time.perf_counter()
                optimum, optimal_S, residual = exact(instance)
                row = dict(key=instance["key"], regime=regime, seed=seed,
                           split="discovery" if seed < 10 else "holdout", revenue=revenue,
                           exact_optimum=optimum, ratio=revenue / optimum, oracle_residual=residual,
                           solver_seconds=seconds, oracle_seconds=time.perf_counter() - start,
                           offers=S.astype(int).tolist(), optimal_offers=optimal_S.tolist())
                out.write(json.dumps(row) + "\n")
                out.flush()
                rows.append(row)
                print(json.dumps({k: row[k] for k in ("key", "split", "ratio")}), flush=True)
    summary = {"label": "Fresh fixed-generator diagnostic, exact oracle; not AIPS success",
               "n": len(rows), "groups": []}
    for regime in sorted({r["regime"] for r in rows}):
        for split in ("discovery", "holdout"):
            group = [r for r in rows if r["regime"] == regime and r["split"] == split]
            ratios = np.array([r["ratio"] for r in group])
            summary["groups"].append(dict(regime=regime, split=split, n=len(group),
                                          mean_ratio=float(ratios.mean()), min_ratio=float(ratios.min()),
                                          within_0_1_percent=int((ratios >= .999).sum())))
    (ROOT / "synthetic_summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary), flush=True)


if __name__ == "__main__":
    main()
