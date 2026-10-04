"""Run the confirmed Flash experiment, with at most three numerical workers."""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import os
from pathlib import Path

from .model_comparison import prepare, run_model, select_and_freeze, test_all
from .model_comparison_client import atomic_json


def run(root):
    config = prepare(root)
    if (config.get("comparison_mode"), config.get("generations"),
            config.get("proposals_per_generation"), config.get("repetitions")) != (
            "standalone_flash", 10, 10, 3):
        raise ValueError("This launcher requires the confirmed Flash 10 x 10 x 3 protocol")
    status = {"started_utc": datetime.now(timezone.utc).isoformat(),
              "pid": os.getpid(), "status": "running", "phase": "search", "repetitions": {}, "errors": []}

    def save():
        status["updated_utc"] = datetime.now(timezone.utc).isoformat()
        atomic_json(root / "orchestration_status.json", status)

    save()
    for phase, function in (("search", run_model), ("freeze", select_and_freeze)):
        status["phase"] = phase
        save()
        with ThreadPoolExecutor(max_workers=3) as pool:
            jobs = {pool.submit(function, root, "deepseek_flash", repeat): repeat for repeat in (1, 2, 3)}
            for future in as_completed(jobs):
                repeat = jobs[future]
                try:
                    future.result()
                    status["repetitions"].setdefault(str(repeat), {})[phase] = "complete"
                    print("PHASE_COMPLETE", phase, repeat, flush=True)
                except Exception as error:
                    # Detailed sanitized failure receipts remain in the run.
                    status["repetitions"].setdefault(str(repeat), {})[phase] = "incomplete"
                    status["errors"].append({"phase": phase, "repeat": repeat,
                                              "error_type": type(error).__name__})
                    print("PHASE_FAILED", phase, repeat, type(error).__name__, flush=True)
                save()
        if status["errors"]:
            status["status"] = "incomplete"
            save()
            raise RuntimeError("Experiment incomplete; inspect retained run diagnostics before resuming")
    status["phase"] = "test"
    save()
    try:
        test_all(root)
        status["phase"] = "report"
        save()
        from .flash_reporting import build_report
        build_report(root)
    except Exception as error:
        status["status"] = "incomplete"
        status["errors"].append({"phase": status["phase"], "error_type": type(error).__name__})
        save()
        raise
    status["phase"] = "complete"
    status["status"] = "complete"
    save()
    print("FLASH_EXPERIMENT_COMPLETE", str(root), flush=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", type=Path, required=True)
    args = parser.parse_args()
    run(args.run.resolve())


if __name__ == "__main__":
    main()
