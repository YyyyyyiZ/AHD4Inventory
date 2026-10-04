from pathlib import Path
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed
import json, os, subprocess, sys
folder = Path(__file__).resolve().parent
settings = json.loads((folder / "jobs.json").read_text())
root = Path(settings["root"])
def write(name, data):
    path = folder / name
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(data, indent=2) + "\n")
    temp.replace(path)
state = {"status": "running", "pid": os.getpid(), "workers": 2, "jobs": [], "started_utc": datetime.now(timezone.utc).isoformat()}
write("status.json", state)
def dispatch(scenario):
    if (root / "PAUSE").exists() or (root.parent / "20260916_unrestricted_params" / "PAUSE").exists():
        return {"scenario": scenario, "status": "paused"}
    command = [sys.executable, "-m", "examples.inventory.correlated_benchmark.adaptive_pil_runner", "train", "--run-dir", str(root), "--scenario", scenario, "--repeat", "1"]
    with (folder / (scenario + ".log")).open("a") as log:
        process = subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT)
        write(scenario + ".json", {"status": "running", "pid": process.pid, "command": command})
        code = process.wait()
    answer = {"scenario": scenario, "status": "complete" if code == 0 else "needs_attention", "exit_code": code}
    write(scenario + ".json", answer)
    return answer
with ThreadPoolExecutor(max_workers=2) as executor:
    for item in as_completed([executor.submit(dispatch, s) for s in settings["scenarios"]]):
        state["jobs"].append(item.result())
        write("status.json", state)
state["status"] = "complete" if all(x["status"] == "complete" for x in state["jobs"]) else "needs_attention"
state["finished_utc"] = datetime.now(timezone.utc).isoformat()
write("status.json", state)
