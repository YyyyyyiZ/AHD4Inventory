"""Finite, read-only-input watcher for final resource and report aggregation.

No policy, evaluation, test, model or API entry point is called. The only child
commands are resource_summary.summarize and combined_report. This does not
replace or modify the authoritative experiment continuation.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import uuid


REPO = Path(__file__).resolve().parents[3]
DEFAULT_RUN = REPO / "output/overnight_search/20260917"
PREFIX = "examples.inventory.overnight_search."
TABLES = ("group_summary.csv", "paired_comparisons.csv", "optimizer_ablation.csv")


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def write_json(path, record):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + "." + uuid.uuid4().hex + ".tmp")
    temporary.write_text(json.dumps(record, ensure_ascii=False, indent=2, allow_nan=False) + "\n")
    temporary.replace(path)


def read_json(path):
    return json.loads(path.read_text())


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def continuation_running(root):
    """Probe, never wait while holding the authoritative runner's lock."""
    path = root / "continuation/.runner.lock"
    if not path.exists():
        return False
    with path.open("r") as handle:
        try:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return True
        fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
    return False


def readiness(root):
    missing, fingerprints = [], {}
    for profile, count in (("primary", 12), ("extended", 8)):
        folder = root if profile == "primary" else root / "extended"
        summary_path = folder / "report_summary.json"
        manifest_path = folder / "figures/plot_manifest.json"
        report_path = folder / "report.md"
        try:
            summary = read_json(summary_path)
            manifest = read_json(manifest_path)
            if summary.get("complete_primary_comparison") is not True or summary.get("n_scenarios") != count:
                missing.append(f"{profile}: complete {count}-scenario report")
            if not report_path.is_file() or report_path.stat().st_size == 0:
                missing.append(f"{profile}: report.md")
            if (manifest.get("profile") != profile or manifest.get("scenarios") != count
                    or manifest.get("expected_scenarios") != count or manifest.get("synthetic_fixture") is not False
                    or manifest.get("test_best_generation_selected") is not False):
                missing.append(f"{profile}: compatible final figure manifest")
            comparison = manifest.get("comparison", {})
            ablation = manifest.get("optimizer_ablation", {})
            if comparison.get("principal_cells") != count * 4 or comparison.get("paired_comparisons") != count:
                missing.append(f"{profile}: complete cost/comparison figures")
            if ablation.get("generation_pairs") != count * 9 or ablation.get("three_generation_means") != count * 3:
                missing.append(f"{profile}: complete optimizer figures")
            for section in (comparison, ablation):
                files = section.get("files", [])
                if len(files) != 3 or {Path(name).suffix for name in files} != {".png", ".pdf", ".svg"}:
                    missing.append(f"{profile}: all three figure formats")
                for name in files:
                    if Path(name).name != name:
                        raise ValueError("Unexpected figure filename")
                    path = folder / "figures" / name
                    if not path.is_file() or path.stat().st_size == 0:
                        missing.append(f"{profile}: figure {name}")
            for name in TABLES:
                path = folder / "tables" / name
                digest = sha256(path)
                if manifest.get("input_sha256", {}).get(name) != digest:
                    missing.append(f"{profile}: figure/table fingerprint {name}")
                fingerprints[str(path)] = digest
            for path in (summary_path, manifest_path, report_path, folder / "tables/per_run.csv"):
                fingerprints[str(path)] = sha256(path)
        except (OSError, ValueError, TypeError, KeyError) as error:
            missing.append(f"{profile}: final report/manifest not ready ({type(error).__name__})")
    if continuation_running(root):
        missing.append("authoritative continuation still running")
    return missing, fingerprints


def execute_stage(root, stage, timeout):
    if stage == "resource_summary":
        command = [sys.executable, "-u", "-c",
                   "from pathlib import Path; import sys; "
                   "from examples.inventory.overnight_search.resource_summary import summarize; "
                   "summarize(Path(sys.argv[1]))", str(root)]
    elif stage == "combined_report":
        command = [sys.executable, "-u", "-m", PREFIX + "combined_report", "--run-dir", str(root)]
    else:
        raise ValueError("Non-postprocessing stage prohibited")
    log_path = root / "postprocessing" / f"{stage}.log"
    with log_path.open("a") as output:
        child = subprocess.Popen(command, cwd=REPO, stdout=output, stderr=subprocess.STDOUT,
                                 start_new_session=True)
        try:
            code = child.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            child.kill()
            child.wait()
            raise TimeoutError(f"{stage} exceeded remaining watcher time; inspect {log_path}")
    if code:
        raise RuntimeError(f"{stage} failed ({code}); inspect {log_path}")
    return dict(returncode=code, log=str(log_path))


def validate_outputs(root):
    resources = read_json(root / "resource_summary.json")
    summary = read_json(root / "night_summary.json")
    markdown = root / "night_summary.md"
    if not markdown.is_file() or markdown.stat().st_size == 0:
        raise ValueError("Combined Markdown report is missing or empty")
    required = ("complete", "comparison_complete", "optimizer_complete", "resource_summary_complete")
    if any(summary.get(key) is not True for key in required):
        raise ValueError("Combined report is incomplete: " + json.dumps({key: summary.get(key) for key in required}))
    if (summary.get("synthetic_fixture") is not False or summary.get("validated_principal_runs") != 240
            or summary.get("validated_three_draw_groups") != 80 or len(summary.get("scenarios", [])) != 20):
        raise ValueError("Combined report does not cover all 20 x 4 x 3 principal results")
    if summary.get("problems"):
        raise ValueError("Combined report validation problems: " + json.dumps(summary["problems"], ensure_ascii=False))
    budget = summary.get("resources", {}).get("budget", {})
    if budget.get("available") is not True or budget.get("within_50") is not True:
        raise ValueError("Shared cumulative budget is unavailable or exceeds $50")
    known, held = (float(resources[key]) for key in ("total_known_usd", "total_held_usd"))
    if not all(math.isfinite(value) and value >= 0 for value in (known, held)) or known + held > 50.000001:
        raise ValueError("Invalid cumulative resource totals")
    if not math.isclose(known + held, budget["committed_usd"], abs_tol=1e-8):
        raise ValueError("Combined summary and cumulative resource ledger disagree")
    for key, expected in (("numeric", 18), ("baek", 6)):
        rows = resources.get(key, [])
        if len(rows) != expected or any(row.get("completed") is not True for row in rows):
            raise ValueError(f"Incomplete resource records: {key}")
    for filename, digest in summary.get("input_sha256", {}).items():
        if sha256(Path(filename)) != digest:
            raise ValueError(f"Combined report input changed during postprocessing: {filename}")
    return dict(principal_runs=240, three_draw_groups=80, scenarios=20,
                known_usd=known, held_usd=held, committed_usd=known + held,
                output_sha256={name: sha256(root / name) for name in
                               ("resource_summary.json", "night_summary.json", "night_summary.md")})


def watch(root, *, max_seconds=14400., poll_seconds=30., stage_runner=execute_stage):
    root = Path(root).resolve()
    directory = root / "postprocessing"
    directory.mkdir(parents=True, exist_ok=True)
    status_path = directory / "status.json"
    started = time.monotonic()
    deadline = started + max_seconds
    status = dict(state="waiting", started_utc=utc_now(), pid=os.getpid(), nice=os.getpriority(os.PRIO_PROCESS, 0),
                  max_seconds=max_seconds, poll_seconds=poll_seconds, paid_calls=0,
                  policy_evaluation_calls=0, test_calls=0, stages=[])
    with (directory / ".runner.lock").open("a+") as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        if status_path.exists():
            previous = read_json(status_path)
            if previous.get("state") == "completed":
                validate_outputs(root)
                print("ALREADY COMPLETED; no stages rerun", flush=True)
                return previous
            if previous.get("stages"):
                raise RuntimeError("Prior postprocessing attempt exists; refusing automatic rerun")
        write_json(status_path, status)
        previous_missing, previous_ready = None, None
        try:
            while True:
                if time.monotonic() >= deadline:
                    raise TimeoutError("Four-hour postprocessing deadline reached before completion")
                missing, fingerprints = readiness(root)
                if not missing and fingerprints == previous_ready:
                    status["input_sha256"] = fingerprints
                    break
                previous_ready = None if missing else fingerprints
                waiting = missing or ["confirming stable complete report and figure inputs"]
                if waiting != previous_missing:
                    print("WAIT " + "; ".join(waiting), flush=True)
                    previous_missing = waiting
                status.update(waiting_for=waiting, updated_utc=utc_now(), elapsed_seconds=time.monotonic() - started)
                write_json(status_path, status)
                time.sleep(min(poll_seconds, max(0., deadline - time.monotonic())))
            status.pop("waiting_for", None)
            status["state"] = "postprocessing"
            for stage in ("resource_summary", "combined_report"):
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise TimeoutError("Postprocessing deadline reached")
                attempt = dict(stage=stage, started_utc=utc_now(), state="running")
                status["stages"].append(attempt)
                write_json(status_path, status)
                print("START " + stage, flush=True)
                attempt.update(stage_runner(root, stage, remaining))
                attempt.update(state="completed", finished_utc=utc_now())
                write_json(status_path, status)
                print("DONE " + stage, flush=True)
            status["validation"] = validate_outputs(root)
            missing, fingerprints = readiness(root)
            if missing or fingerprints != status["input_sha256"]:
                raise ValueError("Report/figure inputs changed during postprocessing")
            status.update(state="completed", finished_utc=utc_now(), elapsed_seconds=time.monotonic() - started)
            write_json(status_path, status)
            print("COMPLETED validated 240 principal results, 80 groups, 20 scenarios and one cumulative budget", flush=True)
            return status
        except Exception as error:
            status.update(state="timed_out" if isinstance(error, TimeoutError) else "failed",
                          finished_utc=utc_now(), elapsed_seconds=time.monotonic() - started,
                          error=f"{type(error).__name__}: {error}")
            if status["stages"] and status["stages"][-1]["state"] == "running":
                status["stages"][-1]["state"] = status["state"]
            write_json(status_path, status)
            print(status["state"].upper() + " " + status["error"], flush=True)
            raise


def self_test():
    def fixtures(root):
        for profile, count in (("primary", 12), ("extended", 8)):
            folder = root if profile == "primary" else root / "extended"
            write_json(folder / "report_summary.json", dict(complete_primary_comparison=True, n_scenarios=count))
            (folder / "report.md").write_text("synthetic report\n")
            (folder / "tables").mkdir(parents=True)
            for name in TABLES + ("per_run.csv",):
                (folder / "tables" / name).write_text("synthetic,input\n")
            (folder / "figures").mkdir()
            files = {}
            for stem in ("comparison", "ablation"):
                files[stem] = [stem + ext for ext in (".png", ".pdf", ".svg")]
                for name in files[stem]:
                    (folder / "figures" / name).write_text("synthetic figure placeholder\n")
            write_json(folder / "figures/plot_manifest.json", dict(profile=profile, scenarios=count,
                expected_scenarios=count, synthetic_fixture=False, test_best_generation_selected=False,
                comparison=dict(principal_cells=4 * count, paired_comparisons=count, files=files["comparison"]),
                optimizer_ablation=dict(generation_pairs=9 * count, three_generation_means=3 * count, files=files["ablation"]),
                input_sha256={name: sha256(folder / "tables" / name) for name in TABLES}))

    calls = []

    def fake_stage(root, stage, timeout):
        calls.append(stage)
        assert timeout > 0
        if stage == "resource_summary":
            write_json(root / "resource_summary.json", dict(total_known_usd=12., total_held_usd=1.,
                       numeric=[dict(completed=True)] * 18, baek=[dict(completed=True)] * 6))
        else:
            write_json(root / "night_summary.json", dict(complete=True, comparison_complete=True,
                optimizer_complete=True, resource_summary_complete=True, synthetic_fixture=False,
                validated_principal_runs=240, validated_three_draw_groups=80, scenarios=[{}] * 20,
                problems=[], resources=dict(budget=dict(available=True, within_50=True, committed_usd=13.))))
            (root / "night_summary.md").write_text("synthetic combined summary\n")
        return dict(returncode=0)

    with tempfile.TemporaryDirectory(prefix="postprocess_watch_qa_") as temporary:
        root = Path(temporary)
        assert readiness(root)[0]
        fixtures(root)
        assert not readiness(root)[0]
        target = root / "tables/group_summary.csv"
        original = target.read_text()
        target.write_text("changed\n")
        assert readiness(root)[0]
        target.write_text(original)
        result = watch(root, max_seconds=5., poll_seconds=.001, stage_runner=fake_stage)
        assert result["state"] == "completed" and calls == ["resource_summary", "combined_report"]
        watch(root, max_seconds=5., poll_seconds=.001, stage_runner=fake_stage)
        assert len(calls) == 2
        for mode in ("timeout", "failure"):
            folder = root / mode
            if mode == "failure":
                fixtures(folder)
            def failure(*args):
                raise RuntimeError("synthetic first-stage failure")
            try:
                watch(folder, max_seconds=.01 if mode == "timeout" else 5., poll_seconds=.001, stage_runner=failure)
            except (RuntimeError, TimeoutError):
                pass
            else:
                raise AssertionError("Expected bounded stop")
            status = read_json(folder / "postprocessing/status.json")
            assert status["state"] == ("timed_out" if mode == "timeout" else "failed")
            assert len(status["stages"]) == (0 if mode == "timeout" else 1)
    return dict(synthetic_only=True, readiness="passed", stale_figures="rejected", stages="once each",
                completed_restart="no rerun", timeout="explicit", first_failure="stopped", real_final_data_read=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path, default=DEFAULT_RUN)
    parser.add_argument("--max-seconds", type=float, default=14400.)
    parser.add_argument("--poll-seconds", type=float, default=30.)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        print(json.dumps(self_test(), indent=2))
        return
    if not 0 < args.max_seconds <= 14400 or not 0 < args.poll_seconds <= 60:
        parser.error("Runtime must be at most four hours; polling must be between zero and sixty seconds")
    watch(args.run_dir, max_seconds=args.max_seconds, poll_seconds=args.poll_seconds)


if __name__ == "__main__":
    main()
