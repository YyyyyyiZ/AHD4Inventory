"""Finish this authorized experiment once existing searches complete.

This is a finite batch continuation, not a recurring task. It never retries a
paid session. Each subprocess uses the original shared budget and test gates.
"""
from concurrent.futures import ThreadPoolExecutor, as_completed
import fcntl
import json
from pathlib import Path
import subprocess
import sys
import time

from ..correlated_benchmark.api_client import atomic_json

ROOT = Path(__file__).resolve().parents[3]
RUN = ROOT / "output/overnight_search/20260917"
PREFIX = "examples.inventory.overnight_search."


def wait_until(predicate, label):
    print("WAIT", label, flush=True)
    while not predicate():
        time.sleep(10)
    print("READY", label, flush=True)


def execute(label, module, *args):
    target = RUN / "continuation" / f"{label}.log"
    target.parent.mkdir(parents=True, exist_ok=True)
    print("START", label, flush=True)
    with target.open("a") as output:
        result = subprocess.run([sys.executable, "-u", "-m", PREFIX + module, *map(str, args)],
                                cwd=ROOT, stdout=output, stderr=subprocess.STDOUT)
    if result.returncode:
        raise RuntimeError(f"{label} failed ({result.returncode}); inspect {target}")
    print("DONE", label, flush=True)


def baek_ready(directory):
    files = [directory / "sessions" / f"l2_r{r}" / "result.json" for r in (1, 2, 3)]
    if not all(p.exists() for p in files):
        return False
    for path in files:
        row = json.loads(path.read_text())
        if row.get("status") != "completed" or not (path.parent / "policy.py").exists():
            raise RuntimeError("Baek session requires review: " + str(path))
    return True


def search_ready(directory):
    files = list((directory / "search").glob("*/completed.json"))
    expected = {(arm, r) for arm in ("one_query", "best_of_n", "evolution") for r in (1, 2, 3)}
    return len(files) == 9 and {(x["arm"], x["repeat"]) for x in map(lambda p: json.loads(p.read_text()), files)} == expected


def extended_baek():
    wait_until(lambda: baek_ready(RUN / "baek"), "primary Baek artifacts")
    # Wait for the already-running primary generator to release its runner lock.
    with (RUN / "baek/.runner.lock").open("a+") as lock:
        while True:
            try:
                fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                fcntl.flock(lock.fileno(), fcntl.LOCK_UN)
                break
            except BlockingIOError:
                time.sleep(2)
    execute("extended_baek_generation", "baek_perishable", "generate", "--run-dir", RUN / "baek/extended",
            "--budget-dir", RUN / "baek", "--workers", 3)
    if not baek_ready(RUN / "baek/extended"):
        raise RuntimeError("Extended Baek generation did not finish all three sessions")


def primary():
    wait_until(lambda: search_ready(RUN), "primary nine search repetitions")
    wait_until(lambda: (RUN / "primary_precompute_2.done").exists(), "existing primary refit precomputation")
    if not (RUN / "numeric_policies_freeze.json").exists():
        execute("primary_import_repair", "repair_imports", "--profile", "primary", "--apply")
    wait_until(lambda: baek_ready(RUN / "baek"), "primary Baek sources before test")
    execute("primary_numeric_evaluation", "evaluate_search")
    execute("primary_baek_scoring", "score_baek")
    # Both numerical and Baek seals were verified by the preceding scorers.
    for filename in ("numeric_policies_freeze.json", "baek_policies_freeze.json"):
        if not (RUN / filename).exists():
            raise RuntimeError("DP final test gate is missing " + filename)
    execute("primary_dp_test", "exact_dp", "test", "--test-authorized")
    execute("primary_report", "report")
    execute("primary_figures", "plot_results", "--run-dir", RUN)


def extended():
    run = RUN / "extended"
    wait_until(lambda: search_ready(run), "extended nine search repetitions")
    if not (run / "numeric_policies_freeze.json").exists():
        execute("extended_import_repair", "repair_imports", "--profile", "extended", "--apply")
    execute("extended_numeric_freeze", "extended", "evaluate", "--freeze-only", "--workers", 2)
    wait_until(lambda: baek_ready(RUN / "baek/extended"), "extended Baek sources before test")
    execute("extended_numeric_evaluation", "extended", "evaluate", "--workers", 2)
    execute("extended_baek_scoring", "extended", "score-baek", "--workers", 2)
    execute("extended_report", "extended", "report")
    execute("extended_figures", "plot_results", "--run-dir", run, "--profile", "extended")


def main():
    target = RUN / "continuation"
    target.mkdir(parents=True, exist_ok=True)
    with (target / ".runner.lock").open("a+") as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        status = {}
        with ThreadPoolExecutor(max_workers=3) as pool:
            futures = {pool.submit(fn): label for fn, label in ((extended_baek, "extended_baek"),
                                                               (primary, "primary"), (extended, "extended"))}
            for future in as_completed(futures):
                label = futures[future]
                try:
                    future.result()
                    status[label] = dict(completed=True)
                except Exception as error:
                    status[label] = dict(completed=False, error=str(error))
                    print("FAILED", label, str(error), flush=True)
                atomic_json(target / "status.json", status)
        execute("resource_summary", "resource_summary")
        if not all(x.get("completed") for x in status.values()):
            raise RuntimeError("Some finite batch stages require review")


if __name__ == "__main__":
    main()
