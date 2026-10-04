"""Finite, serial validation/refit precomputation for finished extended arms.

This helper never generates policies, freezes artifacts, or calls final tests.
It delegates selection/refitting to the standard functions and their caches.
Launch with nice -n 10; the authoritative continuation may reuse the same files.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import tempfile
import time
import traceback
from types import SimpleNamespace

from ..correlated_benchmark.api_client import atomic_json
from .repair_imports import repair_reason


EXPECTED = tuple((arm, repeat) for arm in ("one_query", "best_of_n", "evolution") for repeat in (1, 2, 3))


def emit(event, **fields):
    print(json.dumps(dict(utc=datetime.now(timezone.utc).isoformat(), event=event, **fields), ensure_ascii=False), flush=True)


def pending_repairs(completed):
    return [dict(origin=row.get("origin"), reason=reason)
            for row in completed["pool"]
            if (reason := repair_reason(row)) is not None and not row.get("evaluation_correction")]


def validation_denominators(run, search, evaluation, discovery_specs):
    """The same calculation and baseline set used by extended.freeze_numeric."""
    bases = {}
    for path in sorted((run / "baselines").glob("*/fit.json")):
        row = json.loads(path.read_text())
        theta = {name: value["theta"] for name, value in row["results"].items()}
        validation = evaluation.validate(row["code"], theta, path.parent.name)
        bases[path.parent.name] = dict(code=row["code"], validation=validation)
    seeds = search.seed_codes()
    if not all(name in bases for name in seeds):
        raise ValueError("A common seed baseline is missing")
    return {spec["name"]: min(row["validation"]["results"][spec["name"]]["cost"]
                             for name, row in bases.items() if name in seeds)
            for spec in discovery_specs}


def process_available(run, evaluation, denominators, cached, *, expected=EXPECTED, logger=emit, checkpoint=None):
    """One sequential pass; an affected arm is never selected before repair."""
    blocked, waiting = {}, []
    for arm, repeat in expected:
        if (run / "numeric_policies_freeze.json").exists():
            return dict(stop="numeric_freeze", blocked=blocked, waiting=waiting)
        key = f"{arm}_r{repeat}"
        path = run / "search" / key / "completed.json"
        if not path.exists():
            waiting.append(key)
            continue
        raw = path.read_bytes()
        digest = hashlib.sha256(raw).hexdigest()
        completed = json.loads(raw)
        if (completed.get("arm"), completed.get("repeat")) != (arm, repeat):
            raise ValueError("Completed arm identity differs from directory: " + key)
        if key in cached:
            if cached[key]["completed_sha256"] != digest:
                raise ValueError("Previously precomputed completion record changed: " + key)
            continue
        repairs = pending_repairs(completed)
        if repairs:
            blocked[key] = repairs
            continue
        logger("select_and_refit", arm=arm, repeat=repeat)
        selected = evaluation.select_one(completed, denominators)
        if (selected.get("arm"), selected.get("repeat")) != (arm, repeat):
            raise ValueError("Cached selection belongs to a different arm")
        choice = selected["selected"]
        if not any(row.get("valid") and row.get("code") == choice["code"]
                   and row.get("origin") == choice["origin"] for row in completed["pool"]):
            raise ValueError("Cached selection is not an eligible member of the completed pool")
        if (run / "numeric_policies_freeze.json").exists():
            return dict(stop="numeric_freeze", blocked=blocked, waiting=waiting)
        # Standard refit owns a per-code lock and validates the full request hash.
        # It preserves the current independent scenario checkpoints and guards.
        started = time.monotonic()
        fitted = evaluation.refit(choice["code"])
        cached[key] = dict(completed_sha256=digest, source_sha256=hashlib.sha256(choice["code"].encode()).hexdigest(),
                           origin=choice["origin"], scenarios=len(fitted["results"]),
                           cache_access_seconds=time.monotonic()-started)
        logger("cached", arm=arm, repeat=repeat, **cached[key])
        if checkpoint is not None:
            checkpoint()
    return dict(stop="all_nine_cached" if len(cached) == len(expected) else None, blocked=blocked, waiting=waiting)


def run(max_runtime_seconds, poll_seconds):
    # Fresh-process configuration changes only this process's module globals.
    from .extended import configure, scenario_list
    search, evaluation, config = configure()
    root = search.RUN
    directory = root / "precompute"
    directory.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    state = dict(kind="extended_training_only_precompute", workers=1, paid_calls=0, final_test_calls=0,
                 pid=os.getpid(), nice=os.getpriority(os.PRIO_PROCESS, 0), cached={}, status="starting",
                 max_runtime_seconds=max_runtime_seconds)
    def checkpoint():
        state["updated_utc"] = datetime.now(timezone.utc).isoformat()
        state["elapsed_seconds"] = time.monotonic()-started
        atomic_json(directory / "status.json", state)
    with (directory / ".runner.lock").open("a+") as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        checkpoint()
        try:
            if json.loads((root / "protocol.json").read_text()) != config:
                raise ValueError("Fresh extended settings differ from the frozen protocol")
            emit("starting", pid=state["pid"], nice=state["nice"], workers=1)
            if (root / "numeric_policies_freeze.json").exists():
                state.update(status="stopped", reason="numeric_freeze")
                checkpoint()
                return
            denominators = validation_denominators(root, search, evaluation, scenario_list())
            state.update(status="running", denominators=denominators)
            checkpoint()
            previous_waiting = None
            while True:
                if time.monotonic()-started >= max_runtime_seconds:
                    state.update(status="stopped", reason="runtime_deadline")
                    checkpoint()
                    emit("stopped", reason=state["reason"], cached=len(state["cached"]))
                    return
                progress = process_available(root, evaluation, denominators, state["cached"], checkpoint=checkpoint)
                state.update(progress)
                if progress["stop"]:
                    state.update(status="stopped", reason=progress["stop"])
                    checkpoint()
                    emit("stopped", reason=state["reason"], cached=len(state["cached"]))
                    return
                state["status"] = "waiting"
                checkpoint()
                signature = json.dumps(dict(blocked=progress["blocked"], waiting=progress["waiting"]), sort_keys=True)
                if signature != previous_waiting:
                    emit("waiting", blocked=progress["blocked"], unfinished=progress["waiting"], cached=len(state["cached"]))
                    previous_waiting = signature
                time.sleep(min(poll_seconds, max(0., max_runtime_seconds-(time.monotonic()-started))))
                state["status"] = "running"
        except Exception as error:
            state.update(status="failed", error=f"{type(error).__name__}: {error}")
            checkpoint()
            emit("failed", error=state["error"], cached=len(state["cached"]))
            raise


def self_test():
    with tempfile.TemporaryDirectory(prefix="extended_precompute_synthetic_") as temporary:
        root = Path(temporary)
        for name, cost in (("a", 9.), ("b", 7.), ("extra", 1.)):
            path = root / "baselines" / name / "fit.json"
            path.parent.mkdir(parents=True)
            path.write_text(json.dumps(dict(code=name, results={"s":dict(theta=[cost])})))
        seen = []
        def validate(code, theta, label):
            seen.append(label)
            return dict(results={"s":dict(cost=theta["s"][0])})
        e = SimpleNamespace(validate=validate)
        den = validation_denominators(root, SimpleNamespace(seed_codes=lambda:{"a":"", "b":""}), e, [dict(name="s")])
        assert den == {"s":7.} and set(seen) == {"a", "b", "extra"}
        expected = (("one_query",1), ("one_query",2))
        for arm, repeat in expected:
            folder = root / "search" / f"{arm}_r{repeat}"
            folder.mkdir(parents=True)
            pool = [dict(valid=True, code="same", origin="common_baseline:a")]
            if repeat == 2:
                pool.append(dict(valid=False, code="rejected", origin="candidate", error="Imports must be at module scope"))
            (folder / "completed.json").write_text(json.dumps(dict(arm=arm, repeat=repeat, pool=pool)))
        calls = []
        def select(row, denominators):
            assert denominators == den
            calls.append(("select", row["repeat"]))
            return dict(arm=row["arm"], repeat=row["repeat"], selected=row["pool"][0])
        def refit(code):
            calls.append(("refit", code))
            return dict(results={"s":{}})
        e.select_one, e.refit = select, refit
        cached = {}
        progress = process_available(root,e,den,cached,expected=expected,logger=lambda *args,**kwargs:None)
        assert len(cached)==1 and "one_query_r2" in progress["blocked"]
        assert calls==[("select",1),("refit","same")]
        path=root / "search/one_query_r2/completed.json"
        row=json.loads(path.read_text());row["pool"][1]["evaluation_correction"]={"revision":"fixed"}
        path.write_text(json.dumps(row))
        progress=process_available(root,e,den,cached,expected=expected,logger=lambda *args,**kwargs:None)
        assert len(cached)==2 and progress["stop"]=="all_nine_cached"
        (root / "numeric_policies_freeze.json").write_text('{}')
        before=list(calls)
        assert process_available(root,e,den,{},expected=expected,logger=lambda *args,**kwargs:None)["stop"]=="numeric_freeze"
        assert calls==before
    return dict(standard_denominators="passed", pending_repair_skipped="passed", corrected_failure_remains_invalid="passed",
                serial_standard_selection_refit="passed", freeze_stop="passed", actual_policy_runs=0, api_calls=0)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--poll-seconds",type=float,default=15.)
    parser.add_argument("--max-runtime-seconds",type=float,default=21600.)
    parser.add_argument("--self-test",action="store_true")
    args=parser.parse_args()
    if args.self_test:
        print(json.dumps(self_test(),indent=2))
        return
    if not 1 <= args.poll_seconds <= 60 or args.max_runtime_seconds <= 0:
        parser.error("Polling must be 1..60 seconds; runtime deadline must be positive")
    run(args.max_runtime_seconds,args.poll_seconds)


if __name__=="__main__":
    main()
