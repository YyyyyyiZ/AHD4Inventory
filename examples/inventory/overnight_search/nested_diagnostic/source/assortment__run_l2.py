"""
Assortment LEVEL-2 harness (arm W, write-once): ONE query per family. The prompt states the
choice model and the required solve() signature, grants an empty sandbox (no benchmark
instance is ever exposed), and the single submitted artifact is then evaluated on every
instance of the family.

Runtime protocol: the prompt states a 30 s per-instance target for solve();
evaluation RECORDS per-instance wall time and never enforces the target -- only the 600 s
hang guard (infrastructure valve for never-returns) aborts an instance. Crashes and
infeasible outputs score 0 and are counted separately.

Usage:
    python run_l2.py --model gpt-5.6-sol --family mmnl
    python run_l2.py --model gpt-5.6-sol --family nl --reps 3
"""
from __future__ import annotations

import argparse
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from common.extract import extract_def
from common.harness import HangTimeout, compile_code, hang_guard, run_generation, write_record

import prompts as P

# Appended to the prompt ONLY in --web-search mode (2026-08-19 experiment). Everything
# else about the query (budget, tools, output contract) is unchanged; the actual prompt sent
# is stored in the record as always.
WEB_SEARCH_SUFFIX = (
    "\n\nYou also have a web search tool. You may use it as much as you like; there is no "
    "limit on the number of searches. Web searches do not count against the compute budget, "
    "which applies to Python execution only."
)
from families import FAMILIES

MAX_CONSEC_HANGS = 5   # a uniformly-slow artifact is aborted after this many consecutive
                       # guard hits; remaining instances score 0 as "hang" (variance-study
                       # amendment, 2026-08-15) -- one bad artifact cannot consume days
HANG_GUARD_S = 600   # never-return safety valve only; the stated 30 s is a
                     # target -- runtime is measured and reported, not enforced


def solve_inject():
    """The prompt promises numpy as np; math/itertools are injected too because models omit
    imports the dev sandbox provided (an artifact must not die of NameError for that)."""
    import itertools
    import math
    import numpy as np
    import scipy
    return {"np": np, "numpy": np, "scipy": scipy, "math": math, "itertools": itertools}


def evaluate_artifact(fam, solve, fout, limit=None):
    """Score one artifact on every instance of the family; returns the summary dict.
    `limit` truncates the instance list -- for smoke tests only, never for reported runs."""
    insts = fam.load()
    if limit:
        insts = insts[:limit]
    n_by_status = {}
    scores = []
    times = []
    consec_hangs = 0
    aborted = False
    for inst in insts:
        row = {"kind": "eval", "key": inst.key, "n": inst.n, "m": inst.m}
        if aborted:
            row.update(status="hang", revenue=0.0, score=0.0,
                       error=f"artifact aborted after {MAX_CONSEC_HANGS} consecutive hang-guard "
                             "hits; not run")
            n_by_status["hang"] = n_by_status.get("hang", 0) + 1
            scores.append(0.0)
            write_record(fout, row)
            continue
        try:
            with hang_guard(HANG_GUARD_S):
                t0 = time.time()
                S = fam.call_solve(solve, inst)
                secs = time.time() - t0
            times.append(secs)
            row["solve_seconds"] = round(secs, 3)
            if not fam.feasible(inst, S):
                row.update(status="infeasible", revenue=0.0, score=0.0)
            else:
                rev = fam.revenue(inst, S)
                row.update(status="ok", revenue=rev)
                den = fam.denominator(inst)
                if den:
                    row["score"] = rev / den
        except HangTimeout:
            row.update(status="hang", revenue=0.0, score=0.0,
                       error=f"exceeded the {HANG_GUARD_S}s hang guard")
            consec_hangs += 1
            if consec_hangs >= MAX_CONSEC_HANGS:
                aborted = True
                print(f"   ARTIFACT ABORTED: {MAX_CONSEC_HANGS} consecutive hang-guard hits; "
                      f"remaining instances scored 0")
        except Exception as e:  # noqa: BLE001
            row.update(status="error", revenue=0.0, score=0.0,
                       error=f"{type(e).__name__}: {e}"[:200])
        if row["status"] != "hang":
            consec_hangs = 0
        n_by_status[row["status"]] = n_by_status.get(row["status"], 0) + 1
        if "score" in row:
            scores.append(row["score"])
        write_record(fout, row)

    summary = {"kind": "eval_summary", "n_instances": len(insts), "status": n_by_status,
               "aborted": aborted,
               "solve_seconds": {"mean": round(sum(times) / len(times), 3) if times else None,
                                 "max": round(max(times), 3) if times else None}}
    if scores:
        import numpy as np
        s = np.array(scores)
        summary["scores"] = {"n": len(s), "mean": float(s.mean()),
                             "median": float(np.median(s)), "min": float(s.min()),
                             "p5": float(np.percentile(s, 5)),
                             "frac_below_99": float((s < 0.99).mean()),
                             "frac_zero": float((s == 0).mean())}
    return summary


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="gpt-5.6-sol")
    ap.add_argument("--family", choices=sorted(FAMILIES), required=True)
    ap.add_argument("--compute", type=float, default=3600.0)
    ap.add_argument("--budget", type=int, default=50)
    ap.add_argument("--max-tokens", type=int, default=32768,
                    help="L2 default raised 16384 -> 32768 (2026-08-11): 5.4/5.1 level-2\n                    final answers bound the 16k cap four times; see RUNS.md")
    ap.add_argument("--reps", type=int, default=1, help="replicate ARTIFACTS (regenerated)")
    ap.add_argument("--limit", type=int, default=None,
                    help="evaluate on only the first N instances (SMOKE TESTS ONLY)")
    ap.add_argument("--out", default=None)
    ap.add_argument("--web-search", action="store_true",
                    help="EXPERIMENT: also give the model OpenAI's built-in web_search tool "
                         "(unlimited), and say so in the prompt; writes to results/websearch_l2_*.jsonl")
    a = ap.parse_args()
    fam = FAMILIES[a.family]
    if a.web_search:
        from common import llm as _llm
        _llm.WEB_SEARCH = True
    a.out = a.out or (f"results/websearch_l2_{a.family}_{a.model}.jsonl" if a.web_search
                      else f"results/l2_{a.family}_{a.model}.jsonl")
    os.makedirs("results", exist_ok=True)
    f = open(a.out, "a")

    for rep in range(a.reps):
        print(f"=== assortment L2 (write-once) | {a.family} | model={a.model} | rep {rep} ===")
        prompt = P.write_once(a.family, total_s=a.compute, n_calls=a.budget)
        if a.web_search:
            prompt = prompt + WEB_SEARCH_SUFFIX
        rec, runner, final, tr = run_generation(
            prompt, a.model, sandbox_data={}, leakage_setting="assortment",
            compute=a.compute, budget=a.budget, max_tokens=a.max_tokens)
        rec.update(kind="llm_level2", family=a.family, rep=rep, web_search=bool(a.web_search))
        solve = None
        if rec["ok"]:
            try:
                code = extract_def("solve", final, tr)
                solve = compile_code(code, solve_inject(), "solve")
                rec.update(artifact_code=code)
                print(f"   artifact: {runner.n_calls} cells, "
                      f"{(rec['exec_summary'] or {}).get('compute_used', 0):.0f}s compute, "
                      f"{rec['gen_elapsed_s']:.0f}s wall")
            except Exception as e:  # noqa: BLE001
                import traceback
                rec.update(ok=False, error=f"{type(e).__name__}: {e}",
                           trace=traceback.format_exc())
        write_record(f, rec)
        if solve is None:
            print(f"   GENERATION FAILED: {rec['error'][:200]}")
            continue

        summary = evaluate_artifact(fam, solve, f, limit=a.limit)
        summary.update(family=a.family, model=a.model, rep=rep,
                       **({"limit": a.limit} if a.limit else {}))
        write_record(f, summary)
        sc = summary.get("scores")
        print(f"   evaluated {summary['n_instances']} instances | status {summary['status']} | "
              f"solve s mean {summary['solve_seconds']['mean']} max "
              f"{summary['solve_seconds']['max']}"
              + (f" | score mean {sc['mean']:.4f} min {sc['min']:.4f}" if sc else ""))
    f.close()
    print(f"wrote {a.out}")


if __name__ == "__main__":
    main()
