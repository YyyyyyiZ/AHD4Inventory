import json
import os
import subprocess
import sys
from pathlib import Path


def main() -> int:
    xai_key = os.getenv("XAI_API_KEY")
    if not xai_key:
        print("XAI_API_KEY is required.", file=sys.stderr)
        return 1

    root = Path(__file__).resolve().parent
    repo_root = root.parents[1]
    run_root = root / "cost_measurements_xai_noopt_20260708"
    model_id = "grok-4-1-fast-non-reasoning"
    model_dir = run_root / model_id.replace("-", "_")
    model_dir.mkdir(parents=True, exist_ok=True)

    usage_log = model_dir / "xai_usage.jsonl"
    stdout_log = model_dir / "run_stdout.log"
    stderr_log = model_dir / "run_stderr.log"

    env = os.environ.copy()
    existing_pythonpath = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = (
        str(repo_root / "eoh" / "src")
        if not existing_pythonpath
        else str(repo_root / "eoh" / "src") + os.pathsep + existing_pythonpath
    )
    env["OPENROUTER_API_KEY"] = xai_key
    env["LLM_API_BASE_URL"] = "https://api.x.ai/v1"
    env["OPENROUTER_USAGE_LOG"] = str(usage_log)

    cmd = [
        sys.executable,
        "runEoH.py",
        "--llm_model",
        model_id,
        "--problem",
        "inventory",
        "--ec_pop_size",
        "10",
        "--ec_n_pop",
        "10",
        "--ec_m",
        "2",
        "--dist",
        "normal_std30_L6_c1_2",
        "--external_opt",
        "no",
        "--n_train",
        "50",
        "--n_horizon",
        "50",
        "--order_option",
        "order_before_sell",
        "--iter_opt",
        "15",
        "--param_num",
        "4",
        "--algo_performance",
        "processed",
        "--data_summary",
        "plain",
        "--operator",
        "m2",
        "--repeat",
        "1",
        "--filename",
        "cost_xai_noopt",
    ]

    metadata = {
        "display_name": "Grok 4.1 Fast Non-Reasoning",
        "model_id": model_id,
        "base_url": env["LLM_API_BASE_URL"],
        "usage_log": str(usage_log),
        "command": cmd,
    }
    (model_dir / "metadata.json").write_text(json.dumps(metadata, indent=2))

    print(f"Running {metadata['display_name']} ({model_id})")
    with stdout_log.open("w") as out, stderr_log.open("w") as err:
        result = subprocess.run(cmd, cwd=root, env=env, stdout=out, stderr=err)
    if result.returncode != 0:
        print(f"FAILED: return code {result.returncode}", file=sys.stderr)
        return result.returncode
    print("Finished Grok 4.1 Fast Non-Reasoning")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
