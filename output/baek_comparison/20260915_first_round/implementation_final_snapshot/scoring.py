"""Resume isolated scoring of frozen generated and historical policy sources.

Generation, retries, parameter fitting and source repair never occur here.
Contract validation uses synthetic demands only; scoring opens frozen test data.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import fcntl
import json
from pathlib import Path
import sys

import numpy as np

from .environment import DEFAULT_DATA_DIR, discover_scenarios, load_demands
from .evaluation import evaluate_artifact_batches
from .pipeline import scenario_batches
from .runner import DEFAULT_RUN, atomic_json, sha256
from .sandbox import PythonSandbox


SCHEMA_VERSION = 1


def demand_fingerprint(demands) -> dict:
    """Canonical array bytes for checking that paired scores share paths."""
    array = np.ascontiguousarray(demands, dtype="<f8")
    return {"demand_sha256": sha256(array.tobytes()), "demand_shape": list(array.shape)}


def synthetic_validation_batches(scenario) -> list[dict]:
    """Three fixed valid demand traces; never draw/load training or test data."""
    mean = float(np.rint(scenario.mean_demand))
    horizon = scenario.horizon
    demands = np.zeros((3, horizon), dtype=float)
    demands[1] = mean
    demands[2, 1::2] = 3 * mean
    return [{"name": "synthetic_contract", "demands": demands}]


def _read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _selected_scenarios(only=None):
    # Keep the FULL ordered grid index even when selecting a subset: it is part
    # of the fresh-demand seed definition shared with the classical pipeline.
    indexed = list(enumerate(discover_scenarios()))
    selected = {only} if isinstance(only, str) else set(only or ())
    unknown = selected - {scenario.scenario_id for _, scenario in indexed}
    if unknown:
        raise ValueError("Unknown scenarios: " + ", ".join(sorted(unknown)))
    return [(index, scenario) for index, scenario in indexed if not selected or scenario.scenario_id in selected]


def _generated_artifacts(run_dir: Path, manifest: dict, session_ids=None):
    selected = {session_ids} if isinstance(session_ids, str) else set(session_ids or ())
    known = {spec["session_id"] for spec in manifest["sessions"]}
    if selected - known:
        raise ValueError("Unknown sessions: " + ", ".join(sorted(selected - known)))
    artifacts, skipped = [], []
    for spec in manifest["sessions"]:
        session_id = spec["session_id"]
        if selected and session_id not in selected:
            continue
        parent_folder = run_dir / "sessions" / session_id
        parent_path = parent_folder / "result.json"
        parent_bytes = parent_path.read_bytes() if parent_path.exists() else None
        variants = [(1, session_id, parent_folder)]
        retry_folder = parent_folder / "retry_1"
        if (retry_folder / "result.json").exists():
            variants.append((2, session_id + "_retry_1", retry_folder))
        for attempt, artifact_id, folder in variants:
            result_path = folder / "result.json"
            if not result_path.exists():
                skipped.append({"session_id": session_id, "artifact_id": artifact_id, "attempt": attempt,
                                "reason": "generation_result_not_available"})
                continue
            result_bytes = parent_bytes if attempt == 1 else result_path.read_bytes()
            result = json.loads(result_bytes)
            if result.get("status") != "completed" or not isinstance(result.get("final_code"), str) or not result["final_code"].strip():
                skipped.append({"session_id": session_id, "artifact_id": artifact_id, "attempt": attempt,
                                "reason": "no_completed_final_code", "generation_status": result.get("status")})
                continue
            code = result["final_code"]
            digest = sha256(code.encode())
            error = None
            if result.get("code_sha256") != digest:
                error = "Final code differs from result.json code_sha256"
            policy_path = folder / "policy.py"
            if not policy_path.is_file() or sha256(policy_path.read_bytes()) != digest:
                error = "Frozen policy.py is missing or does not match final code"
            for field in ("session_id", "level", "family", "repeat", "scenario_id", "prompt_sha256"):
                if result.get(field) != spec.get(field):
                    error = "Session result differs from manifest field " + field
            if result.get("attempt", 1) != attempt:
                error = "Attempt metadata differs from its frozen directory"
            if attempt == 2:
                if result.get("parent_session_id") != session_id:
                    error = "Retry parent_session_id differs from its planned draw"
                if parent_bytes is None or result.get("retry_of_result_sha256") != sha256(parent_bytes):
                    error = "Retry does not reference the frozen original result"
                evidence = result.get("invalidity_evidence")
                if not isinstance(evidence, list) or not evidence or not all(isinstance(item, dict) for item in evidence):
                    error = "Retry has no recorded original-artifact invalidity evidence"
                else:
                    for item in evidence:
                        if item.get("kind") == "synthetic_contract_failure":
                            evidence_path = Path(item.get("path", "")).resolve()
                            if (not evidence_path.is_relative_to((run_dir / "validation").resolve())
                                    or not evidence_path.is_file()
                                    or sha256(evidence_path.read_bytes()) != item.get("validation_sha256")):
                                error = "Retry synthetic-invalidity evidence is missing, outside validation, or changed"
                        elif item.get("kind") == "invalid_final_output":
                            if parent_bytes is None or json.loads(parent_bytes).get("status") != "invalid_final_output":
                                error = "Retry generation-defect evidence differs from its parent result"
                        else:
                            error = "Retry invalidity evidence has an unsupported kind"
                prompt_path = folder / "prompt.txt"
                if not prompt_path.is_file() or sha256(prompt_path.read_bytes()) != spec.get("prompt_sha256"):
                    error = "Retry prompt differs from the frozen original prompt"
            metadata = {
                **spec, "artifact_id": artifact_id, "parent_session_id": session_id,
                "attempt": attempt, "generation_status": result["status"],
                "model": manifest.get("model"), "reasoning_effort": manifest.get("reasoning_effort"),
                "actual_models": result.get("actual_models", []), "cost_usd": result.get("cost_usd"),
                "tool_calls": result.get("tool_calls"), "python_seconds": result.get("python_seconds"),
                "requests": result.get("requests"), "usage": result.get("usage", {}),
                "result_path": str(result_path), "result_sha256": sha256(result_bytes),
                "policy_path": str(policy_path),
                "retry_of_result_sha256": result.get("retry_of_result_sha256"),
                "invalidity_evidence": result.get("invalidity_evidence"),
            }
            artifacts.append({
                "method": "Baek-" + spec["level"], "source": "baek_generated", "level": spec["level"],
                "code": code, "code_sha256": digest, "filename": "baek_" + artifact_id + ".json",
                "scenario_id": spec.get("scenario_id"), "family": spec["family"],
                "metadata": metadata, "freeze_error": error,
            })
    return artifacts, skipped


def _historical_artifacts(run_dir: Path):
    path = run_dir / "historical_inventory.json"
    if not path.is_file():
        return [], [{"source": "historical_training_selected", "reason": "historical_inventory_missing"}]
    raw = path.read_bytes()
    inventory = json.loads(raw)
    artifacts = []
    for scenario_id, item in inventory.get("scenario_train_best", {}).items():
        code = item.get("code")
        digest = sha256(code.encode()) if isinstance(code, str) else None
        error = None
        if not isinstance(code, str) or not code.strip():
            error = "Historical inventory has no frozen policy code"
        elif item.get("candidate_code_sha256") != digest:
            error = "Historical code differs from frozen candidate_code_sha256"
        if item.get("scenario_id") != scenario_id:
            error = "Historical scenario key differs from its metadata"
        artifacts.append({
            "method": "AHD-historical", "source": "historical_training_selected", "level": "L1",
            "code": code, "code_sha256": digest, "filename": "ahd_historical.json",
            "scenario_id": scenario_id, "family": None,
            "metadata": {**{key: value for key, value in item.items() if key != "code"},
                         "inventory_path": str(path), "inventory_sha256": sha256(raw),
                         "reference_label": inventory.get("reference_label")},
            "freeze_error": error,
        })
    return artifacts, []


def _applies(artifact: dict, scenario) -> bool:
    if artifact["level"] == "L2":
        return artifact["family"] == scenario.distribution
    return artifact["scenario_id"] == scenario.scenario_id


def _verify_existing_result(previous: dict, artifact: dict, manifest_hash: str, path: Path):
    if previous.get("code_sha256") != artifact["code_sha256"] or previous.get("manifest_sha256") != manifest_hash:
        raise ValueError("Existing score has different frozen source/manifest: " + str(path))
    if artifact["freeze_error"] and previous.get("status") != "hash_mismatch":
        raise ValueError("Current source no longer satisfies its frozen provenance: " + artifact["freeze_error"])
    expected_result = artifact["metadata"].get("result_sha256")
    if expected_result and previous.get("metadata", {}).get("result_sha256") != expected_result:
        raise ValueError("Generation result changed after this evaluation: " + str(path))


def _verify_data(scenario, manifest: dict) -> dict:
    """Validate raw bytes against the preregistered manifest before scoring."""
    hashes = {}
    for split in ("train", "test"):
        path = DEFAULT_DATA_DIR / f"{scenario.scenario_id}_{split}.json"
        digest = sha256(path.read_bytes())
        if manifest.get("data_sha256", {}).get(path.name) != digest:
            raise ValueError("Frozen dataset hash mismatch: " + path.name)
        hashes[path.name] = digest
    return hashes


def _training_audit(artifact: dict, batches: dict, *, tolerance: float = 0.011) -> dict:
    recorded = artifact["metadata"].get("recorded_train_objective")
    observed = batches.get("training_audit", {}).get("summary", {}).get("mean_total_cost")
    if recorded is None or observed is None:
        return {"status": "unavailable", "recorded_train_objective": recorded,
                "evaluated_train_objective": observed, "absolute_tolerance": tolerance}
    difference = float(observed) - float(recorded)
    matches = abs(difference) <= tolerance
    return {
        "status": "match" if matches else "mismatch_requires_report",
        "recorded_train_objective": recorded, "evaluated_train_objective": observed,
        "difference": difference, "absolute_tolerance": tolerance,
        "matches_within_tolerance": matches,
        "explanation": "First 50 training paths; tolerance accommodates recorded scores rounded to cents. A mismatch does not silently reject, retune, or repair the frozen policy.",
    }


def _score_one(artifact, scenario, batches, sandbox, *, manifest_hash, data_hashes,
               validation, timeout_seconds, setup_timeout_seconds, action_timeout_seconds):
    record = {
        "schema_version": SCHEMA_VERSION, "method": artifact["method"], "source": artifact["source"],
        "scenario_id": scenario.scenario_id, "scenario": scenario.to_params(),
        "code_sha256": artifact["code_sha256"], "metadata": artifact["metadata"],
        "manifest_sha256": manifest_hash, "data_sha256": data_hashes,
        "evaluation_kind": "synthetic_contract_validation" if validation else "frozen_policy_scoring",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "evaluation_limits": {
            "setup_timeout_seconds": min(setup_timeout_seconds, timeout_seconds),
            "requested_setup_timeout_seconds": setup_timeout_seconds,
            "action_timeout_seconds": action_timeout_seconds,
            "worker_timeout_seconds": timeout_seconds,
        },
        "construction_scope": "One initialization for this artifact/scenario and all batches in this record. Synthetic validation and later scoring construct independently; initialization randomness is controlled by the submitted source.",
        "callable_contract": "L1 defines a Python function; L2 design(params) returns a Python function. Callable objects require separate review.",
        "main_report_selection": "One attempt for the entire planned designer draw, qualified only by synthetic validation over every required scenario. Original partial results remain diagnostic; never stitch original and retry across scenarios or select by test cost.",
    }
    if artifact["freeze_error"]:
        raw = {"status": "hash_mismatch", "batches": {}, "setup_seconds": None,
               "error": {"message": artifact["freeze_error"]}}
    else:
        try:
            raw = evaluate_artifact_batches(
                artifact["code"], artifact["level"], scenario, batches, sandbox,
                timeout_seconds=timeout_seconds, setup_timeout_seconds=setup_timeout_seconds,
                action_timeout_seconds=action_timeout_seconds,
            )
        except Exception as exc:
            raw = {"status": "worker_failed", "batches": {}, "setup_seconds": None,
                   "error": {"type": type(exc).__name__, "message": str(exc)[:2000]}}
    normalized = {}
    for batch in batches:
        value = raw.get("batches", {}).get(batch["name"])
        batch_record = {
            "status": raw["status"], **demand_fingerprint(batch["demands"]),
            "mode": batch.get("mode", "finite"), "burn_in": batch.get("burn_in", 0),
            "integer_orders": batch.get("integer_orders", False),
        }
        if value is not None:
            batch_record.update(value)
            # A later stationarity violation invalidates earlier partial costs.
            batch_record["status"] = raw["status"]
        elif raw.get("error"):
            batch_record["error"] = raw["error"]
        normalized[batch["name"]] = batch_record
    record.update({
        "status": raw["status"], "raw_result": raw, "batches": normalized,
        "setup_seconds": raw.get("setup_seconds"),
        "setup_exceeded_30_seconds": raw.get("setup_exceeded_30_seconds"),
        "setup_exceeded_60_seconds": raw.get("setup_seconds") is not None and raw["setup_seconds"] > 60,
    })
    if artifact["source"] == "historical_training_selected" and not validation:
        record["training_audit"] = _training_audit(artifact, normalized)
    return record


def _run_artifacts(run_dir, *, validation, only=None, workers=2, include_generated=True,
                   include_historical=True, session_ids=None, overwrite=False,
                   timeout_seconds=1200, setup_timeout_seconds=600, action_timeout_seconds=1,
                   sandbox_factory=None):
    if workers not in (1, 2, 3):
        raise ValueError("workers must be 1, 2, or 3")
    run_dir = Path(run_dir).resolve()
    manifest_bytes = (run_dir / "manifest.json").read_bytes()
    manifest = json.loads(manifest_bytes)
    artifacts, skipped = [], []
    if include_generated:
        generated, omitted = _generated_artifacts(run_dir, manifest, session_ids)
        artifacts.extend(generated)
        skipped.extend(omitted)
    if include_historical:
        historical, omitted = _historical_artifacts(run_dir)
        artifacts.extend(historical)
        skipped.extend(omitted)
    indexed = _selected_scenarios(only)
    destination = run_dir / ("validation" if validation else "scores")
    pending = []
    for index, scenario in indexed:
        applicable = [artifact for artifact in artifacts if _applies(artifact, scenario)]
        for artifact in applicable:
            path = destination / scenario.scenario_id / artifact["filename"]
            if path.exists() and not overwrite:
                previous = _read_json(path)
                _verify_existing_result(previous, artifact, sha256(manifest_bytes), path)
                skipped.append({"path": str(path), "reason": "existing_result_preserved", "status": previous.get("status")})
                continue
            pending.append((index, scenario, artifact, path))
    if not pending:
        return {"evaluation_kind": "validation" if validation else "scoring", "written": [], "skipped": skipped}

    # No evaluation worker can start before its frozen datasets have passed.
    per_scenario_batches, per_scenario_hashes = {}, {}
    for index, scenario, _, _ in pending:
        if scenario.scenario_id in per_scenario_batches:
            continue
        if validation:
            per_scenario_batches[scenario.scenario_id] = synthetic_validation_batches(scenario)
            per_scenario_hashes[scenario.scenario_id] = {}
        else:
            per_scenario_hashes[scenario.scenario_id] = _verify_data(scenario, manifest)
            per_scenario_batches[scenario.scenario_id] = scenario_batches(scenario, index, manifest)
    sandbox = (sandbox_factory or (lambda: PythonSandbox(sys.executable)))()
    sandbox.probe()

    def execute(job):
        _index, scenario, artifact, path = job
        batches = list(per_scenario_batches[scenario.scenario_id])
        if artifact["source"] == "historical_training_selected" and not validation:
            batches = [{"name": "training_audit", "demands": load_demands(scenario, "train", n_paths=50)}] + batches
        record = _score_one(
            artifact, scenario, batches, sandbox, manifest_hash=sha256(manifest_bytes),
            data_hashes=per_scenario_hashes[scenario.scenario_id], validation=validation,
            timeout_seconds=timeout_seconds, setup_timeout_seconds=setup_timeout_seconds,
            action_timeout_seconds=action_timeout_seconds,
        )
        atomic_json(path, record)
        summary = {"path": str(path), "scenario_id": scenario.scenario_id, "method": artifact["method"],
                   "session_id": artifact["metadata"].get("session_id"),
                   "artifact_id": artifact["metadata"].get("artifact_id"),
                   "attempt": artifact["metadata"].get("attempt"), "status": record["status"],
                   "setup_seconds": record["setup_seconds"]}
        print(json.dumps({"event": "artifact_validated" if validation else "artifact_scored", **summary}), flush=True)
        return summary

    written = []
    lock_path = run_dir / (".validation.lock" if validation else ".scoring.lock")
    with lock_path.open("a") as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        # A different completed invocation may have written these files while
        # this invocation was preparing data/probing its sandbox.
        still_pending = []
        for job in pending:
            _, _, artifact, path = job
            if path.exists() and not overwrite:
                previous = _read_json(path)
                _verify_existing_result(previous, artifact, sha256(manifest_bytes), path)
                skipped.append({"path": str(path), "reason": "existing_result_preserved", "status": previous.get("status")})
            else:
                still_pending.append(job)
        with ThreadPoolExecutor(max_workers=workers) as pool:
            for future in as_completed([pool.submit(execute, job) for job in still_pending]):
                written.append(future.result())
    return {"evaluation_kind": "validation" if validation else "scoring", "written": written, "skipped": skipped}


def score_artifacts(run_dir=DEFAULT_RUN, *, only=None, workers=2, include_generated=True,
                    include_historical=True, session_ids=None, overwrite=False,
                    timeout_seconds=1200, setup_timeout_seconds=600, action_timeout_seconds=1,
                    sandbox_factory=None):
    """Score frozen sources; explicit overwrite is required to replace records."""
    return _run_artifacts(
        run_dir, validation=False, only=only, workers=workers, include_generated=include_generated,
        include_historical=include_historical, session_ids=session_ids, overwrite=overwrite,
        timeout_seconds=timeout_seconds, setup_timeout_seconds=setup_timeout_seconds,
        action_timeout_seconds=action_timeout_seconds, sandbox_factory=sandbox_factory,
    )


def validate_artifacts(run_dir=DEFAULT_RUN, *, only=None, workers=2, include_generated=True,
                       include_historical=False, session_ids=None, overwrite=False,
                       timeout_seconds=1200, setup_timeout_seconds=600, action_timeout_seconds=1,
                       sandbox_factory=None):
    """Detect contract defects on synthetic paths before any optional retry.

    Review flags, including potentially benign caches, are retained for manual
    interpretation. This action never retries, rewrites, or selects policies.
    """
    return _run_artifacts(
        run_dir, validation=True, only=only, workers=workers, include_generated=include_generated,
        include_historical=include_historical, session_ids=session_ids, overwrite=overwrite,
        timeout_seconds=timeout_seconds, setup_timeout_seconds=setup_timeout_seconds,
        action_timeout_seconds=action_timeout_seconds, sandbox_factory=sandbox_factory,
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("score", "validate-artifacts"))
    parser.add_argument("--run-dir", type=Path, default=DEFAULT_RUN)
    parser.add_argument("--only", action="append", help="Scenario ID; may be repeated")
    parser.add_argument("--session", action="append", help="Generated session ID; may be repeated")
    parser.add_argument("--workers", type=int, choices=(1, 2, 3), default=2)
    parser.add_argument("--source", choices=("generated", "historical", "both"))
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--timeout-seconds", type=float, default=1200)
    parser.add_argument("--setup-timeout-seconds", type=float, default=600)
    parser.add_argument("--action-timeout-seconds", type=float, default=1)
    args = parser.parse_args()
    source = args.source or ("generated" if args.action == "validate-artifacts" else "both")
    action = validate_artifacts if args.action == "validate-artifacts" else score_artifacts
    result = action(
        args.run_dir, only=args.only, workers=args.workers, session_ids=args.session,
        include_generated=source in {"generated", "both"}, include_historical=source in {"historical", "both"},
        overwrite=args.overwrite, timeout_seconds=args.timeout_seconds,
        setup_timeout_seconds=args.setup_timeout_seconds, action_timeout_seconds=args.action_timeout_seconds,
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
