"""Read saved Flash progress without model calls or policy evaluation."""
import argparse
from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path


def progress(root):
    root = Path(root)
    output = {"repeats": {}, "api": None}
    status = root / "orchestration_status.json"
    if status.exists():
        output["orchestration"] = json.loads(status.read_text())
    ledger_path = root / "api_budget/budget.json"
    if ledger_path.exists():
        ledger = json.loads(ledger_path.read_text())
        rows = list(ledger.get("requests", {}).values())
        actual = sum(float(r.get("actual_cost_usd") or 0) for r in rows if r["state"] == "actual")
        upper = sum(float(r.get("estimated_upper_usd") or 0) for r in rows if r["state"] == "pricing_upper_estimate")
        held = sum(float(r["reserved_usd"]) for r in rows if r["state"] not in {"actual", "pricing_upper_estimate"})
        pending = [r for r in rows if r["state"] == "pending"]
        now = datetime.now(timezone.utc)
        output["api"] = {"requests": len(rows), "states": dict(Counter(r["state"] for r in rows)),
            "actual_usd": round(actual, 7), "price_upper_usd": round(upper, 7),
            "held_usd": round(held, 7), "paused_reason": ledger.get("paused_reason"),
            "oldest_pending_seconds": round(max(((now-datetime.fromisoformat(r["reserved_utc"])).total_seconds()
                                                  for r in pending), default=0)),
            "returned_models": dict(Counter(r.get("returned_model") for r in rows if r.get("returned_model")))}
    for repeat in (1, 2, 3):
        folder = root / "runs/deepseek_flash" / f"r{repeat}"
        summaries = [json.loads(p.read_text()) for p in sorted(folder.glob("generations/*/summary.json"))]
        records = [json.loads(p.read_text()) for p in sorted(folder.glob("candidates/*/record.json"))]
        output["repeats"][str(repeat)] = {
            "candidate_records": len(records), "valid": sum(bool(r.get("valid")) for r in records),
            "invalid": sum(not r.get("valid") for r in records),
            "completed_generations": sum(s["status"] == "complete" for s in summaries),
            "current_generation": summaries[-1]["generation_number"] if summaries else None,
            "best_training": summaries[-1].get("best_after") if summaries else None,
            "search_complete": (folder / "completed.json").exists(),
            "frozen": (folder / "freeze.json").exists(), "tested": (folder / "test.json").exists(),
            "api_incomplete": (folder / "api_incomplete.json").exists()}
    return output


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(progress(args.run), ensure_ascii=False))
