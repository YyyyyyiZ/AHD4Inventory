from pathlib import Path
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed
import json, os, subprocess, sys
folder=Path(__file__).resolve().parent
settings=json.loads((folder/"jobs.json").read_text())
def write(name,value):
    p=folder/name;t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(value,indent=2)+"\n");t.replace(p)
state={"status":"running","pid":os.getpid(),"workers":settings["workers"],"jobs":[],"started_utc":datetime.now(timezone.utc).isoformat()}
write("status.json",state)
def dispatch(job):
    root=Path(job["root"]);rid=job["request_id"]
    if (root/"PAUSE").exists() or (Path(settings["shared_budget_root"])/"PAUSE").exists():
        return {**job,"status":"paused"}
    adaptive=root.name=="20260916_adaptive_pil_seed"
    module="examples.inventory.correlated_benchmark."+("adaptive_pil_runner" if adaptive else "orchestrator")
    command=[sys.executable,"-m",module,"train","--run-dir",str(root),"--scenario",job["scenario"],"--repeat",str(job["repeat"])]
    if not adaptive:command += ["--horizon",str(job["horizon"])]
    with (folder/(rid+".log")).open("a") as log:
        child=subprocess.Popen(command,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT)
        write(rid+".json",{**job,"status":"running","pid":child.pid,"command":command})
        code=child.wait()
    result={**job,"status":"complete" if code==0 else "needs_attention","exit_code":code}
    write(rid+".json",result);return result
with ThreadPoolExecutor(max_workers=settings["workers"]) as pool:
    for task in as_completed([pool.submit(dispatch,j) for j in settings["jobs"]]):
        state["jobs"].append(task.result());write("status.json",state)
state["status"]="complete" if all(j["status"]=="complete" for j in state["jobs"]) else "needs_attention"
state["finished_utc"]=datetime.now(timezone.utc).isoformat();write("status.json",state)
