"""Repair two specific import-harness failures on training data, without LLMs.

Run in a fresh process after all nine searches finish and before selecting any
affected arm. Existing unrelated selections/refits are allowed. Default is a
read-only plan; --apply archives prior records and updates completed pools.
"""
import argparse
from copy import deepcopy
import fcntl
import hashlib
import json
from pathlib import Path
import re
import time

from ..correlated_benchmark.api_client import atomic_json
from .normalization import IMPORT_NORMALIZATION_REVISION


ERROR = "Imports must be at module scope"


def repair_reason(record):
    """Recognize only the disclosed scope rejection and transient metadata bug."""
    if record.get("valid"):
        return None
    error = record.get("error", "").strip()
    if ERROR in error:
        return "leading_import_scope"
    if (error.splitlines()[-1:] in (["KeyError: 'import_normalization'"],
                                  ['KeyError: "import_normalization"'])
            and "in run_numeric_job" in error
            and re.search(r"prepared\[['\"]import_normalization['\"]\]", error)):
        return "transient_missing_import_normalization_metadata"
    return None


def digest(value):
    return hashlib.sha256(value if isinstance(value, bytes) else value.encode()).hexdigest()


def archive(path, directory, run):
    target = directory / "archive" / path.relative_to(run)
    if not target.exists():
        target.parent.mkdir(parents=True, exist_ok=True)
        # Never replace an earlier audit record on restart.
        with target.open("xb") as handle:
            handle.write(path.read_bytes())
    return target


def repair_search(run, config, make_job, evaluate, score, seed_names, *, apply=False):
    """Dependency-injected core; synthetic checks need neither tapes nor APIs."""
    run = Path(run).resolve()
    if (run / "numeric_policies_freeze.json").exists() or any((run / "test").glob("*.json")):
        raise ValueError("Import repair is forbidden after numerical freeze or any final test")
    protocol = json.loads((run / "protocol.json").read_text())
    if protocol != config:
        raise ValueError("Repair settings differ from the prospective protocol")
    completed = [(path, json.loads(path.read_text()))
                 for path in sorted((run / "search").glob("*/completed.json"))]
    expected = {(arm, repeat) for arm in ("one_query", "best_of_n", "evolution") for repeat in (1, 2, 3)}
    if len(completed) != 9 or {(row["arm"], row["repeat"]) for _, row in completed} != expected:
        raise ValueError("All nine arm repetitions must finish before import repair")
    planned = []
    represented = set()
    for path, row in completed:
        affected = []
        for index, entry in enumerate(row["pool"]):
            reason = repair_reason(entry)
            if reason is None:
                continue
            origin = entry["origin"]
            folder = (run / origin).resolve()
            if not folder.is_relative_to(run / "search"):
                raise ValueError("Repair candidate origin is outside this search")
            fit = json.loads((folder / "fit.json").read_text())
            code = entry["code"]
            if fit.get("code") != code:
                raise ValueError("Candidate fit and completed pool source differ")
            for source, expected_code in ((folder / "policy.py", code),):
                if source.read_text() != expected_code:
                    raise ValueError("Submitted policy source differs from completed pool")
            if json.loads((folder / "source.json").read_text()).get("code") != code:
                raise ValueError("Submitted source metadata differs from completed pool")
            affected.append(dict(index=index, origin=origin, folder=folder, code=code, reason=reason))
            represented.add(origin)
        if affected:
            selected = run / "selected" / f"{row['arm']}_r{row['repeat']}.json"
            if selected.exists():
                raise ValueError("Affected arm already selected: " + selected.name)
            planned.append((path, row, affected))
    for fit_path in (run / "search").glob("*/candidate_*/fit.json"):
        row = json.loads(fit_path.read_text())
        if repair_reason(row) is not None and not row.get("evaluation_correction"):
            if str(fit_path.parent.relative_to(run)) not in represented:
                raise ValueError("Unrepresented repairable harness failure: " + str(fit_path))
    plan = dict(revision=IMPORT_NORMALIZATION_REVISION, profile=config.get("profile", "primary"),
                candidates=[item["origin"] for _, _, cases in planned for item in cases],
                reasons={item["origin"]:item["reason"] for _, _, cases in planned for item in cases},
                training_settings=config["train"],
                timeout_seconds=900 if config.get("profile") == "extended" else 240,
                final_test_access=False, paid_calls=0,
                feedback_replayed=False, applied=bool(apply))
    if not apply or not planned:
        return plan
    baselines = [json.loads((run / "baselines" / name / "fit.json").read_text()) for name in seed_names]
    names = list(baselines[0]["results"])
    denominators = {name: min(row["results"][name]["cost"] for row in baselines) for name in names}
    directory = run / "normalization_repair" / IMPORT_NORMALIZATION_REVISION
    directory.mkdir(parents=True, exist_ok=True)
    records = []
    for completed_path, original, cases in planned:
        archived_completed = archive(completed_path, directory, run)
        corrected = deepcopy(original)
        for case in cases:
            folder, code = case["folder"], case["code"]
            fit_path = folder / "fit.json"
            request = make_job(code)
            request_hash = digest(json.dumps(request, sort_keys=True))
            previous = json.loads(fit_path.read_text())
            correction = previous.get("evaluation_correction", {})
            if correction:
                if correction.get("revision") != IMPORT_NORMALIZATION_REVISION or correction.get("request_sha256") != request_hash:
                    raise ValueError("Existing correction does not match this exact training request")
                result = previous
                archived_fit = directory / "archive" / fit_path.relative_to(run)
                if not archived_fit.exists():
                    raise ValueError("Correction is missing its original archived fit")
            else:
                archived_fit = archive(fit_path, directory, run)
                started = time.monotonic()
                try:
                    result = evaluate(request, timeout=plan["timeout_seconds"])
                    result.update(valid=True, score=score(result, denominators), code=code)
                except Exception as error:
                    result = dict(valid=False, error=str(error)[-3500:], code=code)
                result["evaluation_correction"] = dict(
                    revision=IMPORT_NORMALIZATION_REVISION, request_sha256=request_hash,
                    reason=case["reason"],
                    original_fit_sha256=digest(archived_fit.read_bytes()), code_sha256=digest(code),
                    elapsed_seconds=time.monotonic() - started, timeout_seconds=plan["timeout_seconds"],
                    training_settings=config["train"], feedback_replayed=False)
                atomic_json(fit_path, result)
            corrected["pool"][case["index"]] = dict(result, origin=case["origin"])
            records.append(dict(origin=case["origin"], valid=result["valid"],
                                code_sha256=digest(code), archived_fit=str(archived_fit.relative_to(run)),
                                corrected_fit_sha256=digest(fit_path.read_bytes()),
                                correction=result["evaluation_correction"]))
        corrected["best_training"] = min((row for row in corrected["pool"] if row["valid"]), key=lambda row: row["score"])
        corrected["evaluation_correction"] = dict(
            revision=IMPORT_NORMALIZATION_REVISION, candidates=[case["origin"] for case in cases],
            original_completed_sha256=digest(archived_completed.read_bytes()), feedback_replayed=False,
            explanation="Only the disclosed leading-import rejection or transient missing import-normalization "
                        "metadata KeyError was repaired. The same raw sources were reevaluated with original "
                        "training budgets; no LLM feedback was replayed.")
        atomic_json(completed_path, corrected)
    plan["records"] = records
    # Append a separate invocation record; never replace the historical correction.
    target = directory / f"repair_{time.time_ns()}.json"
    atomic_json(target, plan)
    return plan


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", choices=("primary", "extended"), required=True)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    from . import search, evaluator
    if args.profile == "extended":
        from .extended import configure
        search, _, _ = configure()
    run = search.RUN
    if args.apply:
        with (run / ".import_repair.lock").open("a+") as lock:
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            result = repair_search(run, search.CONFIG, search.job, evaluator.evaluate,
                                   search.score, search.seed_codes(), apply=True)
    else:
        result = repair_search(run, search.CONFIG, search.job, evaluator.evaluate,
                               search.score, search.seed_codes(), apply=False)
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
