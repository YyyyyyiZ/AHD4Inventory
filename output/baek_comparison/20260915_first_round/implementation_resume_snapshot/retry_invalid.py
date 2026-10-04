"""Explicit one-time same-prompt retry for a proven invalid generated artifact.

Default invocation only reports eligibility. --execute is required to make a
paid request. No score is read and no original artifact or log is overwritten.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict
from datetime import datetime, timezone
import fcntl
import json
from pathlib import Path
import sys

from .harness import OpenRouterHarness, SessionConfig
from .runner import (DEFAULT_CREDENTIALS, DEFAULT_RUN, LockedBudget, atomic_json,
                     recover_spend, sha256)
from .sandbox import PythonSandbox


class RetryNotEligible(ValueError):
    pass


def _load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _generation_failure_evidence(folder: Path, result: dict) -> list[dict]:
    """A failed final source extraction must follow a genuine inference response."""
    responses = []
    for line in (folder / "events.jsonl").read_text().splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError as exc:
            raise RetryNotEligible("Incomplete original event log requires infrastructure review") from exc
        if event.get("event") == "response":
            responses.append(event.get("response", {}))
        elif event.get("event") in {"request_rejected", "uncertain_paid_failure"}:
            raise RetryNotEligible("Infrastructure failure cannot use an artifact retry")
    if not responses:
        raise RetryNotEligible("No completed inference response proves an invalid output")
    response = responses[-1]
    if response.get("status") not in {"completed", "incomplete"}:
        raise RetryNotEligible("Provider failed before delivering a final artifact")
    if response.get("status") == "incomplete" and response.get("incomplete_details", {}).get("reason") != "max_output_tokens":
        raise RetryNotEligible("Only output-token truncation is an artifact defect")
    if not isinstance(response.get("usage", {}).get("cost"), (float, int)):
        raise RetryNotEligible("Unreconciled inference cost prevents retry")
    return [{"kind": "invalid_final_output", "generation_status": result["status"],
             "response_id": response.get("id"), "response_status": response["status"]}]


def _validation_evidence(run_dir, folder, spec, result, manifest_raw, result_raw, paths):
    code = result.get("final_code")
    if not isinstance(code, str) or not code.strip():
        raise RetryNotEligible("Completed generation lacks frozen source; review the result instead")
    digest = sha256(code.encode())
    if result.get("code_sha256") != digest or not (folder / "policy.py").is_file():
        raise RetryNotEligible("Original artifact hash is missing or mismatched")
    if sha256((folder / "policy.py").read_bytes()) != digest:
        raise RetryNotEligible("Original policy.py differs from frozen source")
    evidence = []
    expected_name = "baek_" + spec["session_id"] + ".json"
    for path in paths:
        path = path.resolve()
        if not path.is_relative_to((run_dir / "validation").resolve()) or path.name != expected_name:
            raise RetryNotEligible("Retry evidence must be this session's synthetic-validation record")
        raw = path.read_bytes()
        validation = json.loads(raw)
        meta = validation.get("metadata", {})
        if (validation.get("evaluation_kind") != "synthetic_contract_validation"
                or validation.get("source") != "baek_generated"
                or validation.get("data_sha256") != {}
                or validation.get("code_sha256") != digest
                or validation.get("manifest_sha256") != sha256(manifest_raw)
                or meta.get("session_id") != spec["session_id"]
                or meta.get("attempt", 1) != 1
                or meta.get("result_sha256") != sha256(result_raw)):
            raise RetryNotEligible("Validation provenance does not match the frozen first attempt")
        state = validation.get("status")
        worker = validation.get("raw_result", {})
        error = worker.get("error", {})
        issues = worker.get("source_review", {}).get("issues", [])
        limits = validation.get("evaluation_limits", {})
        # A worker/system timeout and review-required heuristic flags are not
        # proof that a policy violates the contract.
        invalid = state == "invalid" and worker.get("status") == "invalid"
        invalid = invalid and (bool(error.get("type")) or any(i.get("reason") == "syntax_error" for i in issues))
        policy_timeout = (state == "timeout" and worker.get("status") == "timeout"
                          and error.get("stage") in {"setup", "policy_action"}
                          and bool(error.get("type"))
                          and limits.get("setup_timeout_seconds") == 600
                          and limits.get("action_timeout_seconds") == 1)
        if invalid or policy_timeout:
            evidence.append({"kind": "synthetic_contract_failure", "path": str(path),
                             "validation_sha256": sha256(raw), "status": state,
                             "error": error, "source_issues": issues,
                             "scenario_id": validation.get("scenario_id")})
    if not evidence:
        raise RetryNotEligible("No proven invalid artifact: valid, poor-scoring, review-required, or infrastructure cases cannot retry")
    return evidence


def plan_retry(run_dir: Path, session_id: str, validation_paths=None) -> dict:
    run_dir = Path(run_dir).resolve()
    manifest_raw = (run_dir / "manifest.json").read_bytes()
    manifest = json.loads(manifest_raw)
    matches = [s for s in manifest["sessions"] if s["session_id"] == session_id]
    if len(matches) != 1:
        raise RetryNotEligible("Session must occur exactly once in the frozen first-round manifest")
    spec = matches[0]
    folder = run_dir / "sessions" / session_id
    if (folder / "retry_1").exists() or any(folder.glob("retry_*")):
        raise RetryNotEligible("The single retry slot already exists; it cannot be resumed or replaced automatically")
    result_raw = (folder / "result.json").read_bytes()
    result = json.loads(result_raw)
    if result.get("attempt", 1) != 1:
        raise RetryNotEligible("Only the original first attempt can qualify")
    if any(result.get(k) != spec.get(k) for k in ("session_id", "level", "family", "repeat", "scenario_id", "prompt_sha256")):
        raise RetryNotEligible("Original result metadata differs from the frozen manifest")
    prompt_raw = (folder / "prompt.txt").read_bytes()
    if sha256(prompt_raw) != spec["prompt_sha256"]:
        raise RetryNotEligible("Original prompt differs from its frozen hash")
    if result.get("status") == "invalid_final_output":
        evidence = _generation_failure_evidence(folder, result)
    elif result.get("status") == "completed":
        paths = list(map(Path, validation_paths)) if validation_paths else list(
            (run_dir / "validation").glob("*/baek_" + session_id + ".json"))
        evidence = _validation_evidence(run_dir, folder, spec, result, manifest_raw, result_raw, paths)
    else:
        raise RetryNotEligible("Generation status is not a genuine invalid-artifact outcome: " + str(result.get("status")))
    spent, uncertain = recover_spend(run_dir)
    if uncertain:
        raise RetryNotEligible("Unresolved paid requests must be reconciled before any artifact retry")
    return {"eligible": True, "session_id": session_id, "attempt": 2,
            "parent_session_id": session_id, "spec": spec,
            "retry_directory": str(folder / "retry_1"), "prompt_sha256": spec["prompt_sha256"],
            "retry_of_result_sha256": sha256(result_raw), "manifest_sha256": sha256(manifest_raw),
            "invalidity_evidence": evidence, "spent_usd_before_retry": spent,
            "spend_limit_usd": min(30.0, float(manifest["spend_limit_usd_including_preflight_and_retries"])),
            "selection_rule": "one same-prompt retry only for a proven invalid first artifact; never compare costs"}


def retry_invalid(run_dir: Path, session_id: str, *, execute=False, validation_paths=None,
                  harness_factory=OpenRouterHarness, sandbox_factory=None, key_loader=None) -> dict:
    """Acquire the same process lock as first-round generation; default is dry-run."""
    run_dir = Path(run_dir).resolve()
    with (run_dir / ".runner.lock").open("a") as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        plan = plan_retry(run_dir, session_id, validation_paths)
        if not execute:
            return plan
        budget = LockedBudget(plan["spend_limit_usd"], plan["spent_usd_before_retry"])
        prompt_raw = (run_dir / "sessions" / session_id / "prompt.txt").read_bytes()
        prompt = prompt_raw.decode("utf-8")
        config = SessionConfig(level=plan["spec"]["level"])
        # Refuse before allocating a retry slot if even the first request cannot fit.
        preview = {"input": [{"role": "user", "content": prompt}],
                   "max_output_tokens": config.max_output_tokens}
        # Add a conservative tool/protocol framing reserve before the real harness
        # enforces its full exact-payload reservation immediately before each POST.
        budget.require_available(OpenRouterHarness.cost_upper_bound(preview)[1] + 0.02)
        sandbox = (sandbox_factory or (lambda: PythonSandbox(sys.executable)))()
        sandbox.probe()
        key = (key_loader or (lambda: _load_json(DEFAULT_CREDENTIALS)["api_key"]))()
        retry_folder = Path(plan["retry_directory"])
        retry_folder.mkdir(exist_ok=False)
        (retry_folder / "prompt.txt").write_bytes(prompt_raw)
        atomic_json(retry_folder / "retry_request.json", {**plan, "created_utc": datetime.now(timezone.utc).isoformat()})
        harness = harness_factory(api_key=key, sandbox=sandbox, budget=budget,
                                  log_path=retry_folder / "events.jsonl", config=config)
        try:
            result = harness.run(prompt)
            record = {**plan["spec"], **asdict(result), "attempt": 2,
                      "parent_session_id": session_id, "retry_of_result_sha256": plan["retry_of_result_sha256"],
                      "invalidity_evidence": plan["invalidity_evidence"]}
            if result.final_code:
                (retry_folder / "policy.py").write_text(result.final_code)
                record["code_sha256"] = sha256(result.final_code.encode())
            atomic_json(retry_folder / "result.json", record)
            return record
        finally:
            # A crash/unknown POST remains in its immutable slot and is recovered
            # from recursive event logs; no second artifact retry is permitted.
            spent, uncertain = recover_spend(run_dir)
            atomic_json(run_dir / "budget.json", {"limit_usd": budget.limit_usd, "spent_usd": spent,
                                                  "reserved_usd": budget.reserved_usd, "uncertain_requests": uncertain})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path, default=DEFAULT_RUN)
    parser.add_argument("--session-id", required=True)
    parser.add_argument("--validation", type=Path, nargs="*")
    parser.add_argument("--execute", action="store_true", help="Explicitly run the one permitted paid retry")
    args = parser.parse_args()
    result = retry_invalid(args.run_dir, args.session_id, execute=args.execute, validation_paths=args.validation)
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
