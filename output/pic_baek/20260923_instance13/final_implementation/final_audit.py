"""Verify saved experiment records without requesting or reevaluating policies."""
import hashlib
import json
from pathlib import Path

import numpy as np

from .experiment import RUN, CREDENTIALS, specs
from .environment import MATRIX_HASH, summarize
from examples.inventory.baek_comparison.runner import atomic_json, recover_spend


def audit():
    protocol = json.loads((RUN / "protocol.json").read_text())
    assert hashlib.sha256(Path(protocol["input_file"]).read_bytes()).hexdigest() == protocol["workbook_sha256"]
    data = np.ascontiguousarray(np.load(RUN / "excel_demands.npy"), dtype="<f8")
    assert data.shape == (200, 1000)
    assert hashlib.sha256(data.tobytes()).hexdigest() == MATRIX_HASH
    for name, digest in protocol["source_hashes"].items():
        assert hashlib.sha256((RUN / name).read_bytes()).hexdigest() == digest
    rows = []
    for spec in specs():
        d = RUN / "sessions" / spec["id"]
        assert hashlib.sha256((d / "prompt.txt").read_bytes()).hexdigest() == protocol["prompt_hashes"][spec["id"]]
        result = json.loads((d / "result.json").read_text())
        events = [json.loads(line) for line in (d / "events.jsonl").read_text().splitlines()]
        requests = [e for e in events if e["event"] == "request"]
        responses = [e for e in events if e["event"] == "response"]
        tools = [e for e in events if e["event"] == "tool_result"]
        assert len(requests) == result["requests"]
        assert result["tool_calls"] <= 50
        assert result["python_seconds"] <= 3600
        assert np.isclose(sum(e["result"].get("elapsed_seconds", 0) for e in tools), result["python_seconds"])
        assert np.isclose(sum(e["response"]["usage"]["cost"] for e in responses), result["cost_usd"])
        for e in requests:
            payload = e["payload"]
            assert payload["model"] == "openai/gpt-5.6-sol"
            assert payload["reasoning"]["effort"] == "high"
            assert payload["max_output_tokens"] == (16384 if spec["level"] == "L1" else 32768)
        for e in responses:
            assert e["response"]["model"] == "openai/gpt-5.6-sol"
        scoring_status = None
        if result.get("final_code"):
            assert (d / "frozen.json").exists()
        if (d / "frozen.json").exists():
            frozen = json.loads((d / "frozen.json").read_text())
            assert hashlib.sha256((d / "policy.py").read_bytes()).hexdigest() == frozen["sha256"]
            score = json.loads((d / "scores.json").read_text())
            scoring_status = score["status"]
            if scoring_status == "valid":
                assert score["policy_calls"] == 600000
                for dataset in ["excel", "validation", "fresh"]:
                    x = score["datasets"][dataset]
                    assert len(x["path_costs"]) == 200
                    recomputed = summarize(x["path_costs"])
                    for key, value in recomputed.items():
                        assert np.isclose(value, x[key], rtol=1e-12, atol=1e-10)
                    assert np.isclose(sum(x["component_means"]), x["mean"])
        rows.append(dict(session=spec["id"], generation_status=result["status"],
                         scoring_status=scoring_status, requests=len(requests),
                         responses=len(responses), tool_calls=result["tool_calls"],
                         python_seconds=result["python_seconds"],
                         confirmed_cost_usd=result["cost_usd"]))
    retained, unresolved = recover_spend(RUN)
    assert not any(x.get("blocks_resume", True) for x in unresolved)
    # Check only our new artifacts, and never print the credential or matches.
    credential = json.loads(CREDENTIALS.read_text())["api_key"].encode()
    files = [p for p in RUN.rglob("*") if p.is_file()]
    files += [p for p in Path(__file__).parent.rglob("*") if p.is_file()]
    assert all(credential not in p.read_bytes() for p in files), "Credential found in an output artifact"
    report = dict(status="passed", sessions=rows,
                  excel_matrix_sha256=MATRIX_HASH,
                  all_saved_statistics_recomputed=True,
                  frozen_prompts_policies_and_source_hashes_match=True,
                  model_reasoning_and_output_caps_verified_per_request=True,
                  no_api_key_in_output_artifacts=True,
                  confirmed_plus_conservatively_retained_cost_usd=retained,
                  unresolved_cost_records=unresolved)
    atomic_json(RUN / "reproducibility_audit.json", report)
    print("Final audit passed:", len(rows), "sessions;")
    print(RUN / "reproducibility_audit.json")


if __name__ == "__main__":
    audit()
