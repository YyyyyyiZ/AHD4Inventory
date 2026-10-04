"""Finish authorized evaluation as each frozen artifact arrives; never calls an API."""
import fcntl
import json
import time
import traceback
from .experiment import RUN, specs, score, report, atomic_json


def fully_processed():
    for s in specs():
        d = RUN / "sessions" / s["id"]
        if not (d / "result.json").exists():
            return False
        result = json.loads((d / "result.json").read_text())
        if result.get("final_code") and not all((d / name).exists() for name in ("frozen.json", "scores.json")):
            return False
    return True


def main():
    with (RUN/"scoring.lock").open("a") as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        while True:
            ready=[s for s in specs() if
                (RUN/"sessions"/s["id"]/"frozen.json").exists()
                and not (RUN/"sessions"/s["id"]/"scores.json").exists()]
            if ready:
                score()
                report()
            finished=fully_processed()
            if finished:
                report()
                atomic_json(RUN/"completion.json",dict(status="all_planned_sessions_processed",timestamp=time.time()))
                break
            # A generation lock is held for the whole queue. If generation has
            # stopped early, finalize the partial report rather than spin forever.
            with (RUN/"generation.lock").open("a") as glock:
                try:
                    fcntl.flock(glock,fcntl.LOCK_EX|fcntl.LOCK_NB)
                except BlockingIOError:
                    pass
                else:
                    fcntl.flock(glock,fcntl.LOCK_UN)
                    # A final artifact may have appeared after this iteration's
                    # first ready scan. Recheck once generation is fully stopped.
                    score()
                    report()
                    status = "all_planned_sessions_processed" if fully_processed() else "generation_stopped_with_unprocessed_sessions"
                    atomic_json(RUN/"completion.json",dict(status=status,timestamp=time.time()))
                    break
            time.sleep(15)


if __name__=="__main__":
    try:
        main()
    except Exception:
        atomic_json(RUN/"scoring_failure.json",dict(traceback=traceback.format_exc(),timestamp=time.time()))
        raise
