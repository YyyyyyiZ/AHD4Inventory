"""Read-only numerical/provenance audit; never calls a model or a policy."""
from pathlib import Path
from datetime import datetime, timezone
import csv
import hashlib
import json
import math
import statistics
import sys

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
sys.path.insert(0, str(REPO))
from examples.inventory.baek_comparison.runner import recover_spend


def read(path):
    return json.loads(Path(path).read_text())


def table(name):
    with (ROOT / "tables" / name).open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def audit():
    issues, counts = [], {}
    def check(condition, message):
        if not condition:
            issues.append(message)
    def close(a, b):
        return math.isclose(float(a), float(b), rel_tol=1e-10, abs_tol=1e-8)
    manifest = read(ROOT / "manifest.json")
    prompt_groups = {}
    for spec in manifest["sessions"]:
        prompt_groups.setdefault((spec["level"], spec["family"]), []).append(spec["prompt_sha256"])
    check(len(prompt_groups) == 6 and all(len(v) == 3 and len(set(v)) == 1 for v in prompt_groups.values()),
          "Each of six conditions must have three identical frozen prompts")
    completed = 0
    for spec in manifest["sessions"]:
        sid = spec["session_id"]
        folder = ROOT / "sessions" / sid
        check(digest(folder / "prompt.txt") == spec["prompt_sha256"], sid + ": frozen prompt changed")
        result_path = folder / "result.json"
        if not result_path.exists():
            continue
        result = read(result_path)
        if result["status"] != "completed":
            issues.append(sid + ": terminal generation status " + result["status"])
            continue
        completed += 1
        check(digest(folder / "policy.py") == result["code_sha256"], sid + ": source digest differs")
        check(result["tool_calls"] <= 50, sid + ": tool count exceeded")
        check(result["python_seconds"] <= 3600.05, sid + ": Python wall allowance exceeded")
        check(result["actual_models"] == [manifest["model"]], sid + ": actual model differs")
    selections = table("draw_selection.csv")
    selected = {x["session_id"]: x for x in selections if x["status"] == "selected"}
    score_cache = {}
    def score(path):
        if path not in score_cache:
            score_cache[path] = read(path)
        return score_cache[path]
    instances = 0
    setups = []
    for sid, sel in selected.items():
        aid = sel["selected_artifact_id"]
        for scenario in json.loads(sel["required_scenario_ids"]):
            path = ROOT / "scores" / scenario / ("baek_" + aid + ".json")
            if not path.exists():
                continue
            record = score(str(path))
            instances += 1
            check(record["status"] == "ok", aid + "/" + scenario + ": scoring status")
            check(record["manifest_sha256"] == digest(ROOT / "manifest.json"), aid + ": manifest digest")
            check(record["code_sha256"] == digest(record["metadata"]["policy_path"]), aid + ": score source digest")
            setups.append(record.get("setup_seconds", 0))
            for name, batch in record["batches"].items():
                summary, values = batch["summary"], batch["per_path"]["total_cost"]
                check(batch["status"] == "ok", aid + "/" + name + ": batch status")
                check(len(values) == summary["n_paths"], aid + ": path count")
                check(close(statistics.mean(values), summary["mean_total_cost"]), aid + ": path mean")
                check(close(summary["mean_total_cost"] / summary["periods_scored"], summary["mean_cost_per_period"]), aid + ": per-period mean")
                check(summary["n_paths"] == (20 if name == "long_run" else 1000), aid + ": planned path count")
                check(summary["periods_scored"] == (8000 if name == "long_run" else 50), aid + ": scored horizon")
    pairs = [x for x in table("paired_comparisons.csv") if x["analysis_role"] == "main"]
    for row in pairs:
        a = score(row["candidate_score_path"])["batches"][row["batch"]]
        b = score(row["reference_score_path"])["batches"][row["batch"]]
        check(a["demand_sha256"] == b["demand_sha256"], row["artifact_id"] + ": paired demands differ")
        am, bm = statistics.mean(a["per_path"]["total_cost"]), statistics.mean(b["per_path"]["total_cost"])
        check(close(am, row["candidate_mean_cost"]) and close(bm, row["reference_mean_cost"]), row["artifact_id"] + ": CSV means differ")
        check(close(100 * (bm - am) / bm, row["improvement_pct"]), row["artifact_id"] + ": percentage differs")
        check(close(am - bm, row["mean_cost_difference"]), row["artifact_id"] + ": difference sign")
    for row in table("repeat_summary.csv"):
        values = [v for v in json.loads(row["draw_costs"]).values() if v is not None]
        check(len(values) == int(row["n_valid"]), row["scenario_id"] + ": repeat denominator")
        if values:
            check(close(statistics.mean(values), row["mean_cost"]), row["scenario_id"] + ": repeat mean")
        if len(values) > 1:
            check(close(statistics.stdev(values), row["sd_cost_across_draws"]), row["scenario_id"] + ": repeat sample SD")
    accounted, unresolved = recover_spend(ROOT)
    held = sum(x["reserved_usd"] for x in unresolved)
    check(accounted <= manifest["spend_limit_usd_including_preflight_and_retries"], "Global USD cap exceeded")
    counts.update(completed_generation_groups=completed, selected_groups=len(selected), scored_instances=instances,
                  main_paired_comparisons=len(pairs), max_setup_seconds=max(setups, default=0),
                  setups_over_30_seconds=sum(x > 30 for x in setups), known_actual_usd=accounted-held,
                  held_upper_usd=held, accounted_upper_usd=accounted,
                  unresolved_requests=len(unresolved), blocking_unresolved_requests=sum(x.get("blocks_resume", True) for x in unresolved))
    complete = completed == 18 and len(selected) == 18 and instances == 99 and len(pairs) == 540
    return {"checked_utc": datetime.now(timezone.utc).isoformat(), "complete_expected_coverage": complete,
            "status": "pass" if complete and not issues else ("issues" if issues else "incomplete"),
            "counts": counts, "issues": issues,
            "scope": "Saved source/prompt hashes, all path means, paired demand hashes, percentages, repeat means/sample SD, coverage and request ledger. No model or policy execution; no bootstrap resampling rerun."}


if __name__ == "__main__":
    print(json.dumps(audit(), indent=2, ensure_ascii=False))
