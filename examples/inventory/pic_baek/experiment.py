"""Prepare, run, and report the authorized PIC experiment; no calls on import."""
from __future__ import annotations
import argparse
import csv
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import sys
import time
import urllib.request
import numpy as np
import scipy

from examples.inventory.baek_comparison.harness import OpenRouterHarness, RunBudget, SessionConfig
from examples.inventory.baek_comparison.runner import atomic_json, recover_spend
from examples.inventory.baek_comparison.sandbox import PythonSandbox
from .environment import PARAMS, MATRIX_HASH, load_workbook, sample_demands, baseline_costs, summarize
from .prompts import RANGES, make_prompt
from .scoring import score_code, synthetic_demands

ROOT = Path(__file__).resolve().parents[3]
RUN = ROOT / "output/pic_baek/20260923_instance13"
CREDENTIALS = Path.home()/".config/ahd4inventory/pic_instance13_openrouter.json"
XLSX = Path("/Users/fenghua/Downloads/pic_instance_13_demand_seed_111.xlsx")
SOURCE = "https://raw.githubusercontent.com/Multi-Shot-Approximation-of-MDPs/Self-Guided-ALPs-Discounted-Cost/992d43d61f22317df2532cf67fb5547685bf394a/"


def digest(data):
    return hashlib.sha256(data).hexdigest()


class PreloadedSandbox(PythonSandbox):
    def __init__(self, level):
        self.level = level
        super().__init__(sys.executable)

    def run(self, code, timeout_seconds, max_output_bytes=65536):
        preamble = "import numpy as np, scipy, math, itertools\n"
        if self.level == "L1":
            preamble += "params=" + repr(PARAMS) + "\nglobals().update(params)\n"
        return super().run(preamble + code, timeout_seconds, max_output_bytes)


def specs():
    yield dict(id="l1_main", level="L1", role="main", repeat=0)
    yield dict(id="l2_main", level="L2", role="main", repeat=0)
    for i in range(1, 11):
        yield dict(id=f"l2_repeat_{i:02d}", level="L2", role="stability", repeat=i)


def prepare():
    RUN.mkdir(parents=True, exist_ok=True)
    if (RUN/"protocol.json").exists():
        print("Protocol already frozen", flush=True)
        return
    data = load_workbook(XLSX)
    np.save(RUN/"excel_demands.npy", data)
    np.save(RUN/"validation_demands.npy", sample_demands(41001))
    np.save(RUN/"fresh_demands.npy", sample_demands(51001))
    (RUN/"source").mkdir(exist_ok=True)
    for path in ("MDP/PIC/Instances/instance_13.py", "MDP/PIC/perishableInventory.py", "Bound/greedyPolicyUpperBound.py", "utils.py"):
        raw = urllib.request.urlopen(SOURCE+path, timeout=30).read()
        (RUN/"source"/path.replace("/", "__")).write_bytes(raw)
    for s in specs():
        d = RUN/"sessions"/s["id"]
        d.mkdir(parents=True, exist_ok=True)
        (d/"prompt.txt").write_text(make_prompt(s["level"]))
    sources = {str(p.relative_to(RUN)): digest(p.read_bytes()) for p in (RUN/"source").iterdir()}
    # Resource authorization is the paper's bounded calls/compute, not the old
    # unrelated run's $30 cap. This ceiling is a conservative total token-price
    # bound, not an expected charge or a new user-requested monetary budget.
    ceiling = 12 * 51 * (1050000*4 + 32768*15) / 1e6
    protocol = dict(created_at=datetime.now(timezone.utc).isoformat(),
        params=PARAMS, l2_ranges=RANGES, model="openai/gpt-5.6-sol", reasoning_effort="high",
        sessions=list(specs()), python_seconds_per_session=3600, tool_calls_per_session=50,
        l1_output_tokens_per_request=16384, l2_output_tokens_per_request=32768,
        initialization_target_seconds=30, initialization_hang_guard_seconds=600,
        generation_workers=2, numerical_threads_per_worker=1,
        first_valid_main=True, max_defect_requeries_per_main=1,
        l2_repeats="Ten additional L2 queries, following paper section 6.3; primary artifact kept separate.",
        repetition_source_note="Repository RUNS.md describes ten total draws; paper v1 explicitly says ten additional inventory draws. This run follows the paper.",
        class_adaptation="Truncated-normal perishable partial-backlog discounted PIC replaces Poisson nonperishable average-cost lost sales; lost-sales range extended to 1000 by explicit user instruction. New parameter bounds shown in l2_ranges.",
        added_parameter_notes="lifetime/holding/disposal/backlog/std/discount ranges cover the supplied PIC paper family. purchase_cost [0,20] is an explicit adaptation. Original shared lead_time [2,12] and parent mean <=50 preserved.",
        evaluation="Excel settings, rounded policy observation only, 200x1000, t CI df=199, no terminal cost; purchase coefficient 9.025.",
        policy_seed=732019, validation_seed=41001, independent_test_seed=51001,
        input_file=str(XLSX), workbook_sha256=digest(XLSX.read_bytes()), matrix_sha256=MATRIX_HASH,
        source_hashes=sources,
        prompt_hashes={s["id"]:digest(make_prompt(s["level"]).encode()) for s in specs()},
        source_links=["https://arxiv.org/html/2608.27296v1", "https://arxiv.org/pdf/2001.02798v2", SOURCE],
        environment=dict(python=sys.version, numpy=np.__version__, scipy=scipy.__version__, machine=platform.machine(), platform=platform.platform()),
        monetary_budget_policy="No separate USD cap specified. Enforce authorized session count, per-query calls/time and original output-token caps; log all actual charges.",
        conservative_aggregate_price_ceiling_usd=ceiling)
    atomic_json(RUN/"protocol.json", protocol)
    # Freeze the implementation used for this run as well as external source.
    dest=RUN/"implementation"
    dest.mkdir(exist_ok=True)
    for p in Path(__file__).parent.glob("*.py"):
        shutil.copy2(p,dest/p.name)
    print("Prepared and verified Excel instance", flush=True)


def baseline():
    dest=RUN/"baselines.json"
    if dest.exists():
        return
    candidates=[("constant",q) for q in range(11)]+[("base_stock",s) for s in range(71)]
    train=baseline_costs(sample_demands(61001), candidates)
    selected=[]
    for name in ("constant", "base_stock"):
        ix=[i for i,c in enumerate(candidates) if c[0]==name]
        j=min(ix,key=lambda i:train[:,i].mean())
        selected.append(candidates[j])
    result={}
    for file,name in [("excel_demands.npy","excel"),("validation_demands.npy","validation"),("fresh_demands.npy","fresh")]:
        costs=baseline_costs(np.load(RUN/file), selected)
        result[name]=[{"family":c[0],"parameter":c[1],**summarize(costs[:,j]),
                       "path_costs":costs[:,j].tolist()} for j,c in enumerate(selected)]
    atomic_json(dest,dict(training_seed=61001,selected=selected,datasets=result,
                         note="Simple references trained independently; not claimed to be optimal."))


def run_one(s, key, budget, resume=False):
    d=RUN/"sessions"/s["id"]
    if (d/"result.json").exists():
        return s["id"], json.loads((d/"result.json").read_text())["status"]
    prompt=(d/"prompt.txt").read_text()
    protocol=json.loads((RUN/"protocol.json").read_text())
    assert digest(prompt.encode())==protocol["prompt_hashes"][s["id"]]
    harness=OpenRouterHarness(api_key=key, sandbox=PreloadedSandbox(s["level"]), budget=budget,
        log_path=d/"events.jsonl", config=SessionConfig(level=s["level"]))
    if (d/"events.jsonl").exists():
        if not resume:
            raise RuntimeError("Unfinished journal; explicit --resume required")
        result=harness.resume_from_log(prompt)
    else:
        result=harness.run(prompt)
    atomic_json(d/"result.json", asdict(result))
    if result.final_code:
        (d/"policy.py").write_text(result.final_code)
        atomic_json(d/"frozen.json",dict(sha256=digest(result.final_code.encode()),at=time.time()))
    print(s["id"],result.status,"cost",result.cost_usd,"tools",result.tool_calls,flush=True)
    return s["id"],result.status


def generate(only=None,resume=False):
    protocol=json.loads((RUN/"protocol.json").read_text())
    spend,unknown=recover_spend(RUN)
    if any(item.get("blocks_resume", True) for item in unknown):
        raise RuntimeError("Unresolved model requests; inspect before resuming")
    budget=RunBudget(protocol["conservative_aggregate_price_ceiling_usd"],spend)
    key=json.loads(CREDENTIALS.read_text())["api_key"]
    selected=[s for s in specs() if only is None or s["id"] in only]
    lock=(RUN/"generation.lock").open("a")
    fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    # Queue only two sessions at a time and stop scheduling after infrastructure
    # failures; don't burn the whole queue on a provider error.
    with ThreadPoolExecutor(max_workers=2) as pool:
        for offset in range(0,len(selected),2):
            tasks=[pool.submit(run_one,s,key,budget,resume) for s in selected[offset:offset+2]]
            results=[f.result() for f in as_completed(tasks)]
            atomic_json(RUN/"budget.json",asdict(budget))
            if any(status not in {"completed","invalid_final_output"} for _,status in results):
                print("Generation paused after infrastructure/budget failure",flush=True)
                break
    fcntl.flock(lock,fcntl.LOCK_UN)
    lock.close()


def score():
    sandbox=PythonSandbox(sys.executable)
    sandbox.probe()
    datasets={name:np.load(RUN/file) for file,name in [
        ("excel_demands.npy","excel"),("validation_demands.npy","validation"),("fresh_demands.npy","fresh")]}
    for s in specs():
        d=RUN/"sessions"/s["id"]
        if not (d/"frozen.json").exists() or not (d/"policy.py").exists() or (d/"scores.json").exists():
            continue
        code=(d/"policy.py").read_text()
        assert digest(code.encode())==json.loads((d/"frozen.json").read_text())["sha256"]
        try:
            validation=score_code(sandbox,code,s["level"],{"synthetic":synthetic_demands()},validate_only=True)
            atomic_json(d/"validation.json",validation)
            if validation["status"]!="valid":
                atomic_json(d/"scores.json",validation)
                continue
            result=score_code(sandbox,code,s["level"],datasets)
        except Exception as exc:
            result=dict(status="invalid",error=f"{type(exc).__name__}: {exc}")
        atomic_json(d/"scores.json",result)
        print("SCORED",s["id"],result["status"],
              result.get("datasets",{}).get("excel",{}).get("mean"),flush=True)


def report():
    rows=[]
    for s in specs():
        d=RUN/"sessions"/s["id"]
        row=dict(s)
        for file,key in [("result.json","generation"),("scores.json","scoring")]:
            if (d/file).exists(): row[key]=json.loads((d/file).read_text())
        rows.append(row)
    valid=[r for r in rows if r.get("scoring",{}).get("status")=="valid"]
    chosen=min(valid,key=lambda r:r["scoring"]["datasets"]["validation"]["mean"]) if valid else None
    spend,unknown=recover_spend(RUN)
    result=dict(rows=rows,selected_by_validation=chosen["id"] if chosen else None,
                known_plus_reserved_cost_usd=spend,uncertain_requests=unknown)
    main={r["level"]:r for r in valid if r["role"]=="main"}
    if set(main)=={"L1","L2"}:
        a=main["L1"]["scoring"]["datasets"]["excel"]
        b=main["L2"]["scoring"]["datasets"]["excel"]
        result["paired_main_L2_minus_L1"]={**summarize(np.array(b["path_costs"])-a["path_costs"]),
            "L2_cost_reduction_percent":100*(a["mean"]-b["mean"])/a["mean"]}
    repeats=[r for r in valid if r["role"]=="stability"]
    if repeats:
        values=np.array([r["scoring"]["datasets"]["excel"]["mean"] for r in repeats])
        result["L2_stability"]={"valid":len(repeats),"planned":10,"mean":float(values.mean()),
            "median":float(np.median(values)),"minimum":float(values.min()),"maximum":float(values.max()),
            "between_draw_sd":float(values.std(ddof=1)) if len(values)>1 else None}
    if chosen:
        reference=json.loads((RUN/"baselines.json").read_text()) if (RUN/"baselines.json").exists() else None
        if reference:
            differences=[]
            for ref in reference["datasets"]["excel"]:
                diff=np.array(chosen["scoring"]["datasets"]["excel"]["path_costs"])-np.array(ref["path_costs"])
                differences.append(dict(reference=ref["family"],**summarize(diff)))
            result["paired_differences_selected_minus_reference"]=differences
    atomic_json(RUN/"summary.json",result)
    lines=["# PIC instance 13: Jackie-style Level 1 / Level 2", "",
           "Excel specification: purchase coefficient 9.025, 200 paths × 1000 periods, discount 0.95. Lower cost is better.",
           "L1 and the main L2 are separate from ten additional L2 draws. L2 ranges are explicitly adapted to PIC.", "",
           "| Run | Status | Excel mean | SE | 95% t interval | Setup seconds | API USD |",
           "|---|---|---:|---:|---|---:|---:|"]
    for r in rows:
        g=r.get("generation",{}); sc=r.get("scoring",{}); x=sc.get("datasets",{}).get("excel")
        if x:
            lines.append(f"| {r['id']} | {sc['status']} | {x['mean']:.6f} | {x['standard_error']:.6f} | [{x['ci95_low']:.6f}, {x['ci95_high']:.6f}] | {sc['setup_seconds']:.3f} | {g.get('cost_usd',0):.6f} |")
        else:
            lines.append(f"| {r['id']} | {sc.get('status',g.get('status','pending'))} | — | — | — | — | {g.get('cost_usd',0):.6f} |")
    lines += ["",f"Actual charges plus unresolved conservative reservations: ${spend:.6f}.",
              f"Selected using the independent validation set: {chosen['id'] if chosen else 'pending'}.",
              "All generated artifacts, including invalid ones, are retained. No policy is tuned using Excel test costs.",
              "These are policy costs, not certified optimality gaps. The paper's original PIC numerical settings differ."]
    if "paired_main_L2_minus_L1" in result:
        x=result["paired_main_L2_minus_L1"]
        lines += ["",f"Main L2 minus L1 paired cost difference: {x['mean']:.6f}, 95% t CI [{x['ci95_low']:.6f}, {x['ci95_high']:.6f}].",
                  f"Main L2 cost reduction relative to L1: {x['L2_cost_reduction_percent']:.3f}%."]
    if "L2_stability" in result:
        x=result["L2_stability"]
        lines += ["",f"Additional L2 draws: {x['valid']}/10 valid so far; mean {x['mean']:.6f}, median {x['median']:.6f}, range [{x['minimum']:.6f}, {x['maximum']:.6f}].",
                  "Between-draw variation is separate from each policy's demand-path standard error."]
    if (RUN/"baselines.json").exists():
        refs=json.loads((RUN/"baselines.json").read_text())["datasets"]["excel"]
        lines += ["", "Independently trained simple references:"]
        lines += [f"- {r['family']} (parameter {r['parameter']}): {r['mean']:.6f}, SE {r['standard_error']:.6f}, 95% CI [{r['ci95_low']:.6f}, {r['ci95_high']:.6f}]." for r in refs]
    (RUN/"report.md").write_text("\n".join(lines)+"\n")
    with (RUN/"results.csv").open("w",newline="") as f:
        writer=csv.DictWriter(f,fieldnames=["run","level","role","dataset","mean","standard_error","ci95_low","ci95_high","setup_seconds","api_cost_usd"])
        writer.writeheader()
        for r in valid:
            for name,x in r["scoring"]["datasets"].items():
                writer.writerow(dict(run=r["id"],level=r["level"],role=r["role"],dataset=name,
                    **{k:x[k] for k in ["mean","standard_error","ci95_low","ci95_high"]},
                    setup_seconds=r["scoring"]["setup_seconds"],api_cost_usd=r.get("generation",{}).get("cost_usd",0)))
    print("Report",RUN/"report.md",flush=True)


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("command",choices=["prepare","generate","baselines","score","report","all"])
    ap.add_argument("--only",action="append")
    ap.add_argument("--resume",action="store_true")
    args=ap.parse_args()
    if args.command in {"prepare","all"}: prepare()
    if args.command in {"baselines","all"}: baseline()
    if args.command in {"generate","all"}: generate(args.only,args.resume)
    if args.command in {"score","all"}: score()
    if args.command in {"report","all"}: report()


if __name__=="__main__":
    main()
