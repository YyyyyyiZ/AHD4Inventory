"""Resumable first-round generation. Never sends credentials to the sandbox."""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import sys
import threading

from .environment import Scenario, discover_scenarios, DEFAULT_DATA_DIR
from .harness import OpenRouterHarness, RunBudget, SessionConfig
from .prompts import make_prompt, session_specs
from .sandbox import PythonSandbox


REPO = Path(__file__).resolve().parents[3]
DEFAULT_RUN = REPO / "output/baek_comparison/20260915_first_round"
DEFAULT_CREDENTIALS = Path.home() / ".config/ahd4inventory/openrouter_credentials.json"


def atomic_json(path: Path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + f".{threading.get_ident()}.tmp")
    temporary.write_text(json.dumps(obj, indent=2, ensure_ascii=False, allow_nan=False) + "\n")
    temporary.replace(path)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def numeric_params(scenario: Scenario) -> dict:
    return {key: value for key, value in scenario.to_params().items()
            if key not in {"scenario_id", "distribution"} and value is not None}


class LockedBudget(RunBudget):
    def __post_init__(self):
        self._lock = threading.RLock()

    def __init__(self, limit_usd, spent_usd=0):
        super().__init__(limit_usd, spent_usd)
        self._lock = threading.RLock()

    def reserve(self, upper_cost):
        with self._lock:
            return super().reserve(upper_cost)

    def settle(self, upper_cost, actual_cost):
        with self._lock:
            return super().settle(upper_cost, actual_cost)


def recover_spend(run_dir: Path) -> tuple[float, list[dict]]:
    """Return known charges plus held upper bounds, with request-level evidence.

    Unknown charges retain their full request reservation. A verified explicit
    reconciliation may either replace that bound with an authoritative charge,
    or approve continuation while retaining the entire bound. The latter stays
    in ``uncertain`` and must never be reported as an observed zero charge.
    """
    def valid_cost(value):
        return (isinstance(value, (int, float)) and not isinstance(value, bool)
                and math.isfinite(value) and value >= 0)

    spent = 0.0
    uncertain = []
    for path in sorted(run_dir.glob("api_smoke*response.json")):
        cost = json.loads(path.read_text()).get("usage", {}).get("cost", 0)
        if not valid_cost(cost):
            raise ValueError("Invalid recorded preflight cost: " + str(path))
        spent += float(cost)
    for path in sorted(run_dir.glob("sessions/**/events.jsonl")):
        requests = {}
        pending_index = None
        reconciled_indices = set()
        raw = path.read_bytes()
        offset = 0
        for line in raw.splitlines(keepends=True):
            event_start = offset
            offset += len(line)
            try:
                event = json.loads(line)
            except (json.JSONDecodeError, UnicodeDecodeError):
                # A partial final write leaves any outstanding reservation intact.
                continue
            kind = event.get("event")
            if kind == "request":
                # Older read-only fixtures may omit an index. Such journals can
                # still retain funds, but cannot pass explicit reconciliation.
                index = event.get("request_index", len(requests))
                if isinstance(index, bool) or not isinstance(index, int) or index < 0 or index in requests:
                    raise ValueError("Ambiguous request index in " + str(path))
                reservation = event.get("max_request_cost_usd")
                if not valid_cost(reservation):
                    raise ValueError("Invalid request reservation in " + str(path))
                requests[index] = {
                    "reserved_usd": float(reservation), "amount": float(reservation),
                    "uncertain": True, "state": "pending", "blocks_resume": True,
                }
                pending_index = index
            elif kind == "response":
                if pending_index is None:
                    raise ValueError("Response without an outstanding request in " + str(path))
                request = requests[pending_index]
                cost = event.get("response", {}).get("usage", {}).get("cost")
                if valid_cost(cost):
                    request.update(amount=float(cost), uncertain=False, state="response", blocks_resume=False)
                else:
                    request["state"] = "missing_authoritative_cost"
                pending_index = None
            elif kind in {"uncertain_paid_failure", "request_interrupted"}:
                if pending_index is None:
                    raise ValueError("Failure without an outstanding request in " + str(path))
                request = requests[pending_index]
                if event.get("request_index", pending_index) != pending_index:
                    raise ValueError("Failure request index mismatch in " + str(path))
                charge = event.get("reserved_cost_retained_usd", request["reserved_usd"])
                if not valid_cost(charge) or float(charge) != request["reserved_usd"]:
                    raise ValueError("Failure reservation differs from its request in " + str(path))
                request["state"] = kind
                pending_index = None
            elif kind == "request_rejected" and event.get("known_pre_inference"):
                if pending_index is None:
                    raise ValueError("Rejection without an outstanding request in " + str(path))
                requests[pending_index].update(amount=0.0, uncertain=False, state="rejected", blocks_resume=False)
                pending_index = None
            elif kind == "request_reconciled":
                # Share the harness's exact hashes, terminal/context checks and
                # evidence-file verification; an unproven event releases nothing.
                from .harness import validate_request_reconciliation
                verified = validate_request_reconciliation(event, raw[:event_start])
                index = verified["request_index"]
                if index not in requests or index in reconciled_indices:
                    raise ValueError("Unknown or repeated request reconciliation in " + str(path))
                request = requests[index]
                if not request["uncertain"] or request["state"] != "uncertain_paid_failure":
                    raise ValueError("Reconciliation does not match an uncertain failed request in " + str(path))
                if verified["reserved_cost_retained_usd"] != request["reserved_usd"]:
                    raise ValueError("Reconciliation reservation mismatch in " + str(path))
                mode = verified["charge_resolution"]
                if mode == "authoritative_cost":
                    request.update(amount=float(verified["actual_cost_usd"]), uncertain=False,
                                   state="authoritative_cost", blocks_resume=False)
                elif mode == "conservative_bound":
                    request.update(state="conservative_bound", blocks_resume=False,
                                   reconciled_for_resume=True, charge_resolution=mode,
                                   actual_cost_usd=None, retained_cost_upper_usd=request["reserved_usd"],
                                   reconciliation_id=verified["reconciliation_id"])
                else:
                    raise ValueError("Unknown reconciliation mode in " + str(path))
                reconciled_indices.add(index)
        for index, request in requests.items():
            spent += request["amount"]
            if request["uncertain"]:
                uncertain.append({
                    "log": str(path), "request_index": index,
                    "reserved_usd": request["reserved_usd"], "reason": request["state"],
                    "blocks_resume": request["blocks_resume"],
                    **{key: request[key] for key in (
                        "reconciled_for_resume", "charge_resolution", "actual_cost_usd",
                        "retained_cost_upper_usd", "reconciliation_id",
                    ) if key in request},
                })
    return spent, uncertain


def prepare(run_dir: Path):
    run_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = run_dir / "manifest.json"
    expected = []
    for spec in session_specs():
        params = numeric_params(Scenario.from_id(spec["scenario_id"])) if spec["level"] == "L1" else None
        prompt = make_prompt(spec["level"], spec["family"], params)
        folder = run_dir / "sessions" / spec["session_id"]
        folder.mkdir(parents=True, exist_ok=True)
        target = folder / "prompt.txt"
        if target.exists() and target.read_text() != prompt:
            raise RuntimeError(f"Frozen prompt mismatch for {spec['session_id']}")
        target.write_text(prompt)
        expected.append({**spec, "prompt_sha256": sha256(prompt.encode())})
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text())
        if manifest["sessions"] != expected:
            raise RuntimeError("Existing run manifest differs; do not overwrite experiment")
        return manifest
    import numpy, scipy
    data_hashes = {}
    for scenario in discover_scenarios():
        for split in ("train", "test"):
            path = DEFAULT_DATA_DIR / f"{scenario.scenario_id}_{split}.json"
            # Raw-byte hashing records provenance; no test outcomes enter generation.
            data_hashes[path.name] = sha256(path.read_bytes())
    manifest = {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "user_approved_first_round": True,
        "model": "openai/gpt-5.6-sol", "reasoning_effort": "high",
        "spend_limit_usd_including_preflight_and_retries": 30.0,
        "protocol": "Baek-2026-08-adapted-finite-stationary-v1",
        "python": sys.version, "numpy": numpy.__version__, "scipy": scipy.__version__,
        "hardware": platform.platform(), "cpu_count": os.cpu_count(),
        "seed_fresh_test": 2026091501, "seed_validation": 2026091502,
        "seed_long_run": 2026091503, "seed_paired_bootstrap": 2026091504,
        "fresh_test_paths": 1000, "long_run_paths": 20, "long_run_periods": 10000,
        "long_run_burn_in": 2000,
        "sessions": expected, "data_sha256": data_hashes,
        "differences_from_original": [
            "50 selling periods after L zero-demand planning periods",
            "nonnegative finite real actions without an order cap",
            "known Poisson, rounded Exponential, or clipped-rounded Normal demand with nominal mean100",
            "stationary deterministic policy to match the archived AHD policy class",
            "three independent planned draws; at most one invalid-artifact retry",
            "OpenRouter Responses API routed to OpenAI; local newer Python/NumPy/SciPy",
            "global USD30 spend ceiling; a ceiling interruption is incomplete, not a policy failure",
        ],
    }
    atomic_json(manifest_path, manifest)
    return manifest


def generate(run_dir: Path, *, workers: int = 2, only: str | None = None, resume: bool = False):
    if workers not in (1, 2, 3):
        raise ValueError("workers must be 1, 2, or 3")
    manifest = prepare(run_dir)
    key = json.loads(DEFAULT_CREDENTIALS.read_text())["api_key"]
    spent, uncertain = recover_spend(run_dir)
    if resume and any(item.get("blocks_resume", True) for item in uncertain):
        raise RuntimeError("Unresolved model requests must be reconciled before checkpoint continuation")
    budget = LockedBudget(30.0, spent)
    sandbox = PythonSandbox(python_executable=sys.executable)
    sandbox.probe()
    specs = [spec for spec in manifest["sessions"] if only is None or spec["session_id"] == only]
    pending = []
    for spec in specs:
        folder = run_dir / "sessions" / spec["session_id"]
        if (folder / "result.json").exists():
            continue
        if (folder / "events.jsonl").exists() and not resume:
            raise RuntimeError(f"Unfinished log for {spec['session_id']}; inspect before resuming, never duplicate automatically")
        pending.append(spec)

    infrastructure_stop = threading.Event()

    def run_one(spec):
        if infrastructure_stop.is_set():
            return {**spec, "status": "not_started_infrastructure_stop"}
        try:
            folder = run_dir / "sessions" / spec["session_id"]
            had_log = (folder / "events.jsonl").exists()
            marker = folder / "recovered_tool_pending.json"
            if marker.exists():
                print(json.dumps({"event": "waiting_for_preserved_tool", "session_id": spec["session_id"]}), flush=True)
                while not infrastructure_stop.is_set():
                    recovery = json.loads(marker.read_text())
                    if recovery.get("status") == "completed":
                        break
                    if recovery.get("status") != "running":
                        raise RuntimeError("Tool recovery requires review: " + spec["session_id"])
                    try:
                        os.kill(int(recovery["monitor_pid"]), 0)
                    except (ProcessLookupError, ValueError, KeyError) as exc:
                        raise RuntimeError("Preserved-tool monitor is unavailable; do not duplicate its execution") from exc
                    infrastructure_stop.wait(1)
            if infrastructure_stop.is_set():
                return {**spec, "status": "not_started_infrastructure_stop"}
            print(json.dumps({"event": "resuming" if had_log else "starting", "session_id": spec["session_id"]}), flush=True)
            harness = OpenRouterHarness(api_key=key, sandbox=sandbox, budget=budget,
                log_path=folder / "events.jsonl", config=SessionConfig(level=spec["level"]))
            prompt = (folder / "prompt.txt").read_text()
            result = harness.resume_from_log(prompt) if had_log else harness.run(prompt)
        except Exception:
            infrastructure_stop.set()
            raise
        if result.status in {
            "api_rejected", "transport_rejected", "uncertain_paid_failure", "missing_authoritative_cost",
            "cost_bound_exceeded", "unexpected_model", "invalid_response",
        }:
            infrastructure_stop.set()
        record = {**spec, **asdict(result), "resumed_from_checkpoint": had_log}
        if result.final_code:
            (folder / "policy.py").write_text(result.final_code)
            record["code_sha256"] = sha256(result.final_code.encode())
        atomic_json(folder / "result.json", record)
        print(json.dumps({"event": "finished", "session_id": spec["session_id"],
                          "status": result.status, "cost_usd": result.cost_usd,
                          "python_seconds": result.python_seconds, "tool_calls": result.tool_calls}), flush=True)
        return record

    completed = []
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(run_one, spec): spec for spec in pending}
        for future in as_completed(futures):
            completed.append(future.result())
            with budget._lock:
                atomic_json(run_dir / "budget.json", {
                    "limit_usd": budget.limit_usd, "spent_usd": budget.spent_usd,
                    "reserved_usd": budget.reserved_usd, "uncertain_requests": uncertain,
                })
    return completed


def status(run_dir: Path):
    manifest = json.loads((run_dir / "manifest.json").read_text())
    rows = []
    for spec in manifest["sessions"]:
        folder = run_dir / "sessions" / spec["session_id"]
        path = folder / "result.json"
        if path.exists():
            result = json.loads(path.read_text())
            rows.append({"session_id": spec["session_id"], **{key: result.get(key) for key in
                ("status", "cost_usd", "tool_calls", "python_seconds", "requests")}})
        elif (folder / "events.jsonl").exists():
            events = [json.loads(line) for line in (folder / "events.jsonl").read_text().splitlines() if line]
            rows.append({"session_id": spec["session_id"], "status": "running_or_interrupted",
                         "last_event": events[-1]["event"], "requests": sum(e["event"] == "request" for e in events),
                         "tool_calls": sum(e["event"] == "tool_result" for e in events)})
        else:
            rows.append({"session_id": spec["session_id"], "status": "pending"})
    spent, uncertain = recover_spend(run_dir)
    held = sum(item["reserved_usd"] for item in uncertain)
    return {"sessions": rows, "charged_or_conservatively_reserved_usd": spent,
            "known_actual_cost_usd": spent - held, "unresolved_cost_upper_usd": held,
            "blocking_unresolved_requests": sum(item.get("blocks_resume", True) for item in uncertain),
            "uncertain": uncertain}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("prepare", "generate", "status"))
    parser.add_argument("--run-dir", type=Path, default=DEFAULT_RUN)
    parser.add_argument("--workers", type=int, default=2)
    parser.add_argument("--only")
    parser.add_argument("--resume", action="store_true", help="Continue verified unfinished journals without repeating completed model or tool steps")
    args = parser.parse_args()
    if args.action == "status":
        print(json.dumps(status(args.run_dir), indent=2))
        return
    args.run_dir.mkdir(parents=True, exist_ok=True)
    with (args.run_dir / ".runner.lock").open("a") as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        if args.action == "prepare":
            manifest = prepare(args.run_dir)
            print(json.dumps({"sessions": len(manifest["sessions"]), "run_dir": str(args.run_dir)}))
        else:
            generate(args.run_dir, workers=args.workers, only=args.only, resume=args.resume)


if __name__ == "__main__":
    main()
