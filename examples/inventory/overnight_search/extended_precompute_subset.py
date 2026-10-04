"""One finite, serial training-only pass over three completed extended arms."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import fcntl
import json
import os
from pathlib import Path
import tempfile
import time

from ..correlated_benchmark.api_client import atomic_json
from .extended_precompute import emit, pending_repairs, process_available, validation_denominators


EXPECTED = (("best_of_n", 1), ("evolution", 1), ("evolution", 2))


def preflight(run):
    if (run / "numeric_policies_freeze.json").exists():
        return "numeric_freeze"
    for arm, repeat in EXPECTED:
        path = run / "search" / f"{arm}_r{repeat}" / "completed.json"
        if not path.exists():
            raise ValueError("Requested completed arm is missing: " + str(path))
        row = json.loads(path.read_text())
        if (row.get("arm"), row.get("repeat")) != (arm, repeat):
            raise ValueError("Completed arm identity differs from requested subset")
        if pending_repairs(row):
            raise ValueError("Requested arm has a pending neutral repair: " + path.parent.name)
    return None


def run():
    # Fresh process only: leave the running selectors/evaluators untouched.
    from .extended import configure, scenario_list
    search, evaluation, config = configure()
    root = search.RUN
    directory = root / "precompute_additional"
    directory.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    status = dict(kind="extended_completed_subset_training_only", workers=1, paid_calls=0,
                  final_test_calls=0, pid=os.getpid(), nice=os.getpriority(os.PRIO_PROCESS, 0),
                  order=[f"{arm}_r{repeat}" for arm, repeat in EXPECTED], cached={}, status="starting")

    def checkpoint():
        status.update(updated_utc=datetime.now(timezone.utc).isoformat(), elapsed_seconds=time.monotonic() - started)
        atomic_json(directory / "status.json", status)

    with (directory / ".runner.lock").open("a+") as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        checkpoint()
        try:
            if json.loads((root / "protocol.json").read_text()) != config:
                raise ValueError("Fresh extended settings differ from the frozen protocol")
            stop = preflight(root)
            if stop:
                status.update(status="stopped", reason=stop)
                checkpoint()
                emit("stopped", reason=stop)
                return status
            emit("starting", pid=status["pid"], nice=status["nice"], workers=1, order=status["order"])
            denominators = validation_denominators(root, search, evaluation, scenario_list())
            status["status"] = "running"
            checkpoint()
            progress = process_available(root, evaluation, denominators, status["cached"], expected=EXPECTED,
                                         logger=emit, checkpoint=checkpoint)
            if progress["blocked"] or progress["waiting"]:
                raise ValueError("Completed subset became blocked or incomplete: " + json.dumps(progress))
            status.update(status="stopped", reason="completed_requested_subset" if len(status["cached"]) == len(EXPECTED)
                          else progress["stop"] or "single_pass_finished", progress=progress)
            checkpoint()
            emit("stopped", reason=status["reason"], cached=len(status["cached"]))
            return status
        except Exception as error:
            status.update(status="failed", error=f"{type(error).__name__}: {error}")
            checkpoint()
            emit("failed", error=status["error"], cached=len(status["cached"]))
            raise


def self_test():
    with tempfile.TemporaryDirectory(prefix="completed_subset_qa_") as temporary:
        root = Path(temporary)
        try:
            preflight(root)
        except ValueError:
            pass
        else:
            raise AssertionError("Missing completed arms were not rejected")
        for arm, repeat in EXPECTED:
            atomic_json(root / "search" / f"{arm}_r{repeat}" / "completed.json", dict(arm=arm, repeat=repeat, pool=[]))
        assert preflight(root) is None
        path = root / "search/evolution_r2/completed.json"
        row = json.loads(path.read_text())
        row["pool"] = [dict(valid=False, error="Imports must be at module scope")]
        atomic_json(path, row)
        try:
            preflight(root)
        except ValueError:
            pass
        else:
            raise AssertionError("Pending repair was not rejected")
        atomic_json(root / "numeric_policies_freeze.json", {})
        assert preflight(root) == "numeric_freeze"
    return dict(synthetic_only=True, ordered_subset=[f"{arm}_r{repeat}" for arm, repeat in EXPECTED],
                missing_repair_and_freeze_guards="passed", api_calls=0, final_test_calls=0)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        print(json.dumps(self_test(), indent=2))
    else:
        run()
