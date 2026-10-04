"""Independent replay of the corrected, frozen Baek nested-logit artifact.

No LLM calls or new algorithm search. Inputs are public benchmark data at the
commit recorded in source/benchmark_tree.json and the author's public L2 log.
Run with the repository virtual environment. --replay evaluates every instance;
omitting it audits the saved records only. Output is isolated to this folder.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ProcessPoolExecutor
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import platform
import time

import numpy as np

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "source"


def instances():
    result = {}
    for path in sorted(SOURCE.glob("hard_data__nl_*_data.json")):
        family = path.stem.removeprefix("hard_data__").removesuffix("_data")
        for config, block in json.loads(path.read_text()).items():
            cap = math.ceil(block["n"] * block["cap_rate"]) if "card" in family else None
            for seed, data, best, upper in zip(block["seeds"], block["data"], block["best_rev"], block["upper_bound"]):
                key = f"{family}:{config}:seed{seed}"
                item = dict(data)
                item.update(key=key, n=block["n"], m=block["m"], cap=cap,
                            cap_rate=block["cap_rate"], best_rev=float(best), upper_bound=float(upper))
                for name in ("v", "price", "vi0", "gamma"):
                    item[name] = np.asarray(item[name], dtype=float)
                item["vi0"] = item["vi0"].reshape(-1)
                item["gamma"] = item["gamma"].reshape(-1)
                item["v0"] = float(np.asarray(item["v0"]).reshape(-1)[0])
                result[key] = item
    return result


def scalar_revenue(instance, offers):
    """Explicit scalar formula independent of the artifact's scoring code."""
    numerator, denominator = 0.0, instance["v0"]
    for i in range(instance["m"]):
        attraction, value = float(instance["vi0"][i]), 0.0
        for j in range(instance["n"]):
            if offers[i, j]:
                attraction += float(instance["v"][i, j])
                value += float(instance["v"][i, j] * instance["price"][i, j])
        nest_attraction = attraction ** float(instance["gamma"][i])
        denominator += nest_attraction
        numerator += value * nest_attraction / attraction if attraction else 0.0
    return numerator / denominator


def is_feasible(instance, offers):
    return (offers.shape == (instance["m"], instance["n"])
            and bool(np.all((offers == 0) | (offers == 1)))
            and (instance["cap"] is None or bool(np.all(offers.sum(axis=1) <= instance["cap"]))))


def worker(item):
    instance, saved, comparator = item
    spec = importlib.util.spec_from_file_location("frozen_baek_nl", SOURCE / "baek_l2_original.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    start = time.perf_counter()
    offers = np.asarray(mod.solve(*(instance[k] for k in ("v", "price", "v0", "vi0", "gamma", "cap"))))
    seconds = time.perf_counter() - start
    feasible = is_feasible(instance, offers)
    revenue = scalar_revenue(instance, offers) if feasible else 0.0
    return {
        "key": instance["key"], "n": instance["n"], "m": instance["m"], "cap": instance["cap"],
        "feasible": feasible, "revenue": revenue, "saved_revenue": saved["revenue"],
        "replay_minus_saved": revenue - saved["revenue"], "best_existing": comparator,
        "ratio": revenue / comparator, "upper_bound": instance["upper_bound"],
        "seconds": seconds, "offered_product_indices": [np.flatnonzero(r).tolist() for r in offers],
    }


def summarize(rows):
    ratios = np.array([r["ratio"] for r in rows])
    return {"n": len(rows), "mean_ratio": float(ratios.mean()), "minimum_ratio": float(ratios.min()),
            "median_ratio": float(np.median(ratios)), "within_0_1_percent": int(np.sum(ratios >= 0.999)),
            "below_0_99": int(np.sum(ratios < 0.99)),
            "all_feasible": all(r.get("feasible", True) for r in rows),
            "max_absolute_replay_difference": max(abs(r.get("replay_minus_saved", 0)) for r in rows),
            "sum_seconds": sum(r.get("seconds", 0) for r in rows)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--replay", action="store_true")
    parser.add_argument("--workers", type=int, default=2)
    args = parser.parse_args()
    inputs = instances()
    log_path = SOURCE / "assortment__results__l2_nl_gpt-5.6-sol.jsonl"
    records = [json.loads(line) for line in log_path.read_text().splitlines()]
    queries = [row for row in records if row.get("kind") == "llm_level2" and row.get("ok")]
    # Published artifact-selection rule: first valid replicate, never best score.
    assert len(queries) == 3
    assert queries[0]["artifact_code"] == (SOURCE / "baek_l2_original.py").read_text()
    groups = []
    for row in records:
        if row.get("kind") == "llm_level2":
            groups.append([])
        elif row.get("kind") == "eval":
            groups[-1].append(row)
    evals = {row["key"]: row for row in groups[0]}
    assert len(evals) == 971 and set(evals) == set(inputs)
    comparator = json.loads((SOURCE / "assortment__results__best_existing.json").read_text())["nl"]
    assert set(evals) == set(comparator)
    rows = []
    decision_checks = []
    for key, row in evals.items():
        assert row["status"] == "ok"
        rows.append(dict(key=key, ratio=row["revenue"] / comparator[key]))
        if "offered_product_indices" in row:
            instance = inputs[key]
            S = np.zeros((instance["m"], instance["n"]), dtype=int)
            for i, products in enumerate(row["offered_product_indices"]):
                S[i, products] = 1
            check = dict(key=key, feasible=is_feasible(instance, S),
                         difference=scalar_revenue(instance, S) - row["revenue"])
            decision_checks.append(check)
    summary = {"purpose": "Corrected-public-artifact diagnostic; not AIPS success or a new LLM run.",
               "python": platform.python_version(), "numpy": np.__version__,
               "selected_artifact_rule": "first valid replicate (rep=0), matching the author's rule",
               "saved_records": summarize(rows),
               "all_saved_replicates": [summarize([dict(key=r["key"], ratio=r["revenue"] / comparator[r["key"]])
                                                    for r in group]) for group in groups],
               "saved_decision_checks": {"n": len(decision_checks),
                    "all_feasible": all(r["feasible"] for r in decision_checks),
                    "max_absolute_difference": max(abs(r["difference"]) for r in decision_checks)},
               "benchmark_commit": json.loads((SOURCE / "benchmark_tree.json").read_text())["sha"],
               "sha256": {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                          for p in sorted(SOURCE.iterdir()) if p.is_file()}}
    (ROOT / "saved_audit.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps({k: v for k, v in summary.items() if k != "sha256"}), flush=True)
    if args.replay:
        existing = {}
        result_path = ROOT / "replay.jsonl"
        if result_path.exists():
            existing = {r["key"]: r for r in (json.loads(s) for s in result_path.read_text().splitlines())}
        tasks = [(instance, evals[key], comparator[key]) for key, instance in inputs.items() if key not in existing]
        with result_path.open("a") as output, ProcessPoolExecutor(max_workers=args.workers) as pool:
            for result in pool.map(worker, tasks):
                output.write(json.dumps(result) + "\n")
                output.flush()
                existing[result["key"]] = result
                if len(existing) % 25 == 0:
                    print(json.dumps({"completed": len(existing), "of": len(inputs), "last": result["key"]}), flush=True)
        assert set(existing) == set(inputs)
        summary["replay"] = summarize(list(existing.values()))
        summary["by_configuration"] = {
            config: summarize([r for k, r in existing.items() if k.rsplit(":", 1)[0] == config])
            for config in sorted({k.rsplit(":", 1)[0] for k in existing})}
        (ROOT / "replay_summary.json").write_text(json.dumps(summary, indent=2) + "\n")
        print(json.dumps(summary["replay"]), flush=True)


if __name__ == "__main__":
    main()
