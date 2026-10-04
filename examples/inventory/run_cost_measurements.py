import json
import os
import subprocess
import sys
from pathlib import Path


MODELS = [
    ("DeepSeek V3-0324", "deepseek/deepseek-chat-v3-0324"),
    ("Gemini 2.5 Flash Lite", "google/gemini-2.5-flash-lite"),
    ("Gemini 3 Flash Preview", "google/gemini-3-flash-preview"),
    ("GPT-5 Mini", "openai/gpt-5-mini"),
    ("GPT-5 Nano", "openai/gpt-5-nano"),
]


def safe_name(model_id: str) -> str:
    return model_id.replace("/", "__").replace(".", "_").replace("-", "_")


def main() -> int:
    if not os.getenv("OPENROUTER_API_KEY"):
        print("OPENROUTER_API_KEY is required.", file=sys.stderr)
        return 1

    root = Path(__file__).resolve().parent
    run_root = root / "cost_measurements_noopt_20260708"
    run_root.mkdir(exist_ok=True)

    base_env = os.environ.copy()
    repo_root = root.parents[1]
    existing_pythonpath = base_env.get("PYTHONPATH", "")
    base_env["PYTHONPATH"] = (
        str(repo_root / "eoh" / "src")
        if not existing_pythonpath
        else str(repo_root / "eoh" / "src") + os.pathsep + existing_pythonpath
    )

    for display_name, model_id in MODELS:
        model_dir = run_root / safe_name(model_id)
        model_dir.mkdir(exist_ok=True)
        usage_log = model_dir / "openrouter_usage.jsonl"
        stdout_log = model_dir / "run_stdout.log"
        stderr_log = model_dir / "run_stderr.log"

        env = base_env.copy()
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
            "cost_exact_noopt",
        ]

        metadata = {
            "display_name": display_name,
            "model_id": model_id,
            "usage_log": str(usage_log),
            "command": cmd,
        }
        (model_dir / "metadata.json").write_text(json.dumps(metadata, indent=2))

        print(f"Running {display_name} ({model_id})")
        with stdout_log.open("w") as out, stderr_log.open("w") as err:
            result = subprocess.run(cmd, cwd=root, env=env, stdout=out, stderr=err)
        if result.returncode != 0:
            print(f"FAILED {display_name}: return code {result.returncode}", file=sys.stderr)
            return result.returncode
        print(f"Finished {display_name}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
