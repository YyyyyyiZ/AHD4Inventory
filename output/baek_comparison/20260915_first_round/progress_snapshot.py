"""Compact read-only run status; omit request bodies and model/tool text."""
from pathlib import Path
import json
import sys
import time

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parents[2]))
from examples.inventory.baek_comparison.runner import recover_spend

completed, active, failures = [], [], []
for path in sorted((ROOT / "sessions").glob("*/events.jsonl")):
    result = path.parent / "result.json"
    if result.exists():
        data = json.loads(result.read_text())
        (completed if data["status"] == "completed" else failures).append(path.parent.name)
        continue
    events = [json.loads(line) for line in path.read_bytes().split(b"\n")[:-1] if line.strip()]
    if not events:
        continue
    executed = [e["result"] for e in events if e["event"] == "tool_result"]
    active.append({"session": path.parent.name, "last_event": events[-1]["event"],
                   "last_event_age_seconds": round(time.time() - events[-1]["timestamp"]),
                   "tools_completed": len(executed),
                   "completed_python_seconds": round(sum(e["elapsed_seconds"] for e in executed))})
accounted, unknown = recover_spend(ROOT)
print(json.dumps({"utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                  "completed_groups": len(completed), "completed_ids": completed,
                  "active": active, "terminal_failures": failures,
                  "known_usd": round(accounted - sum(e["reserved_usd"] for e in unknown), 6),
                  "uncertain_requests": [{"reason": e["reason"], "upper_usd": e["reserved_usd"]}
                                         for e in unknown if e["reason"] != "pending"]}))
