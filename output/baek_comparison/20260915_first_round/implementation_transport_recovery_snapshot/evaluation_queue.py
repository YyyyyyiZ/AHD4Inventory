"""Evaluate each frozen first-round submission while generation continues.

This process makes no model requests and never returns scores to generation.
It preserves existing validation and score records. Review-required artifacts
remain pending for an explicit review; this queue never repairs or retries them.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import time

from .report import generate_report
from .runner import DEFAULT_RUN, atomic_json
from .scoring import score_artifacts, validate_artifacts


def run_queue(run_dir: Path, generation_pid: int):
    manifest = json.loads((run_dir / "manifest.json").read_text())
    progress = run_dir / "evaluation_queue_progress.json"
    done = json.loads(progress.read_text()) if progress.exists() else {}
    print(json.dumps({"event": "evaluation_queue_started", "pid": os.getpid(),
                      "planned": len(manifest["sessions"]), "previously_processed": len(done)}), flush=True)
    while True:
        changed = False
        for spec in manifest["sessions"]:
            sid = spec["session_id"]
            result_path = run_dir / "sessions" / sid / "result.json"
            if sid in done or not result_path.exists():
                continue
            result = json.loads(result_path.read_text())
            if result["status"] != "completed":
                done[sid] = {"status": "generation_not_completed", "generation_status": result["status"]}
            else:
                print(json.dumps({"event": "validation_started", "session_id": sid}), flush=True)
                validate_artifacts(run_dir, workers=2, include_generated=True,
                                   include_historical=False, session_ids=[sid])
                records = [json.loads(path.read_text()) for path in
                           (run_dir / "validation").glob("*/baek_" + sid + ".json")]
                statuses = [record["status"] for record in records]
                if not records or any(status != "ok" for status in statuses):
                    done[sid] = {"status": "validation_needs_review", "validation_statuses": statuses}
                else:
                    print(json.dumps({"event": "scoring_started", "session_id": sid,
                                      "instances": len(records)}), flush=True)
                    score_artifacts(run_dir, workers=2, include_generated=True,
                                    include_historical=False, session_ids=[sid])
                    scored = [json.loads(path.read_text()) for path in
                              (run_dir / "scores").glob("*/baek_" + sid + ".json")]
                    done[sid] = {"status": "scored", "instances": len(records),
                                 "scoring_statuses": [record["status"] for record in scored]}
            atomic_json(progress, done)
            changed = True
            print(json.dumps({"event": "session_evaluation_complete", "session_id": sid,
                              **done[sid]}), flush=True)
        if changed:
            summary = generate_report(run_dir)
            print(json.dumps({"event": "report_updated", "report_path": summary["report_path"],
                              "warnings": summary["warnings"]}), flush=True)
        if len(done) == len(manifest["sessions"]):
            break
        try:
            os.kill(generation_pid, 0)
        except ProcessLookupError:
            # A final result may have appeared after this iteration scanned it.
            if any(spec["session_id"] not in done and
                   (run_dir / "sessions" / spec["session_id"] / "result.json").exists()
                   for spec in manifest["sessions"]):
                continue
            break
        time.sleep(5)
    print(json.dumps({"event": "evaluation_queue_finished", "processed": len(done),
                      "planned": len(manifest["sessions"])}), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path, default=DEFAULT_RUN)
    parser.add_argument("--generation-pid", type=int, required=True)
    args = parser.parse_args()
    run_queue(args.run_dir.resolve(), args.generation_pid)


if __name__ == "__main__":
    main()
