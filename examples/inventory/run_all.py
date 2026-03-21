import os
import json
import subprocess
import sys
from pathlib import Path
from itertools import product


# =========================
# Direct Setup Section
# =========================
# 1) Choose one or more LLM profiles below.
# 2) Set the provider API key in your shell, or set an override here.
# 3) Edit dataset/operator/iteration knobs directly in this section.

# OPENROUTER_API_KEY_OVERRIDE = x
GEMINI_API_KEY_OVERRIDE = "AIzaSyAJoKQ25KcfSfMQEoZ_rYvLMXNYqe3vLOg"  # Optional: paste Gemini key here. Prefer env var for safety.

LLM_PROFILES = {
    "gemini-direct-3.0-flash": {
        "endpoint": "https://generativelanguage.googleapis.com/v1beta/openai",
        "model": "gemini-3-flash-preview",
        "api_key_env": "GEMINI_API_KEY",
    },
    "openrouter-minimax-fast": {
        "endpoint": "https://openrouter.ai/api/v1",
        "model": "minimax/minimax-m2.5",
        "reasoning_effort": "low",
        "api_key_env": "OPENROUTER_API_KEY",
    },
    "openrouter-deepseek-fast": {
        "endpoint": "https://openrouter.ai/api/v1",
        "model": "deepseek/deepseek-chat",
        "reasoning_effort": "low",
        "api_key_env": "OPENROUTER_API_KEY",
    },
    "openrouter-gemini-2.5-fast": {
        "endpoint": "https://openrouter.ai/api/v1",
        "model": "google/gemini-2.5-flash-lite",
        "reasoning_effort": "low",
        "api_key_env": "OPENROUTER_API_KEY",
    },
    "openrouter-gpt-5-nano": {
        "endpoint": "https://openrouter.ai/api/v1",
        "model": "openai/gpt-5-nano",
        "reasoning_effort": "low",
        "api_key_env": "OPENROUTER_API_KEY",
    },
    "openrouter-gpt-5-mini": {
        "endpoint": "https://openrouter.ai/api/v1",
        "model": "openai/gpt-5-mini",
        "reasoning_effort": "low",
        "api_key_env": "OPENROUTER_API_KEY",
    },
    "openrouter-gemini-3.0-preview": {
        "endpoint": "https://openrouter.ai/api/v1",
        # Keep legacy profile name, but map to the current OpenRouter model slug.
        "model": "google/gemini-3-flash-preview",
        "reasoning_effort": "low",
        "api_key_env": "OPENROUTER_API_KEY",
    },
    "openrouter-grok-4.1-fast": {
        "endpoint": "https://openrouter.ai/api/v1",
        "model": "x-ai/grok-4.1-fast",
        "reasoning_effort": "low",
        "api_key_env": "OPENROUTER_API_KEY",
    },
}

SELECTED_PROFILES = [
    "openrouter-deepseek-fast",
    "openrouter-gemini-2.5-fast",
    "gemini-direct-3.0-flash",
    "openrouter-gpt-5-mini",
    "openrouter-gpt-5-nano",
    "openrouter-grok-4.1-fast",
]

# Optional: add custom configs not in presets.
CUSTOM_LLM_CONFIGS = [
    # {
    #     "name": "my-custom-model",
    #     "endpoint": "https://generativelanguage.googleapis.com/v1beta/openai",
    #     "model": "provider/model",
    #     "reasoning_effort": "low",  # Optional; omit to use the provider default.
    #     "api_key_env": "GEMINI_API_KEY",
    #     "api_key": "",  # if empty, uses the provider env var/override
    # },
]

problem = "inventory"
dist_list = [
    # "normal_std30_L6_c1_2",
    # "poisson_L6_c1_2",
    "exponential_L6_c1_2",
]
operator_list = ["m2"]  # e.g. ["e1", "e2", "m2"]
repeat_num = 3

ec_pop_size = 10
ec_n_pop = 20
ec_m_list = [2]
external_opt_list = ["no"]  # ["no", "scipy"]
algo_performance_list = ["processed"]  # ["no", "plain", "processed"]
data_summary_list = ["plain"]  # ["no", "plain", "processed"]
n_train_list = [50]
n_horizon_list = [50]
iter_opt_list = [15]
param_loc_list = ["default"]  # ["start", "default"]
order_option_list = ["order_before_sell"]
prompt_with_explanations = False
filename_tag = "all_in_one_exponential"
# Tuneable initial base-stock levels for the seeded base-stock policy.
initial_base_stock_list = [300, 402, 500, 700]


def build_llm_configs():
    llm_configs = []
    for profile_name in SELECTED_PROFILES:
        if profile_name not in LLM_PROFILES:
            raise ValueError(f"Unknown profile in SELECTED_PROFILES: {profile_name}")
        cfg = dict(LLM_PROFILES[profile_name])
        cfg["name"] = profile_name
        cfg["api_key"] = ""
        llm_configs.append(cfg)

    llm_configs.extend(CUSTOM_LLM_CONFIGS)
    return llm_configs


def resolve_api_key(llm_cfg):
    key = (llm_cfg.get("api_key") or "").strip()
    if key:
        return key

    api_key_env = llm_cfg.get("api_key_env", "OPENROUTER_API_KEY")
    override_map = {
        "OPENROUTER_API_KEY": OPENROUTER_API_KEY_OVERRIDE.strip(),
        "GEMINI_API_KEY": GEMINI_API_KEY_OVERRIDE.strip(),
    }
    override = override_map.get(api_key_env, "").strip()
    if override:
        return override

    return os.environ.get(api_key_env, "").strip()


def ensure_base_stock_continue_file(script_dir: Path, base_stock_value: float) -> str:
    generated_dir = script_dir / "_generated_continue"
    generated_dir.mkdir(parents=True, exist_ok=True)

    safe_tag = str(base_stock_value).replace(".", "p")
    out_path = generated_dir / f"base_stock_{safe_tag}.json"
    base_stock_value = float(base_stock_value)

    payload = [
        {
            "algorithm": (
                "The algorithm implements Base Stock Policy where the inventory level is always brought "
                "back to a fixed target level 'base_stock' at the beginning of each period."
            ),
            "code": (
                "def compute_order_amount(on_hand_inventory, pipeline_orders):\n"
                f"    base_stock = {base_stock_value}  # OPT_PARAM: {{'initial': {base_stock_value}, "
                "'min': 10, 'max': 1000, 'type': 'float'}}\n"
                "    order_amount = max(0, base_stock - on_hand_inventory - sum(pipeline_orders))\n"
                "    return order_amount"
            ),
            "objective": None,
            "other_inf": None,
        }
    ]

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=5)
    return str(out_path.resolve())


def main():
    print(f"Python executable: {sys.executable}")
    script_dir = Path(__file__).resolve().parent

    llm_configs = build_llm_configs()
    if not llm_configs:
        raise ValueError("No LLM configs selected. Set SELECTED_PROFILES or CUSTOM_LLM_CONFIGS.")

    total_jobs = (
        repeat_num
        * len(llm_configs)
        * len(dist_list)
        * len(initial_base_stock_list)
        * len(external_opt_list)
        * len(n_train_list)
        * len(n_horizon_list)
        * len(order_option_list)
        * len(ec_m_list)
        * len(param_loc_list)
        * len(iter_opt_list)
        * len(algo_performance_list)
        * len(data_summary_list)
    )
    print(f"Planned jobs: {total_jobs}")

    job_idx = 0
    for repeat in range(repeat_num):
        for initial_base_stock in initial_base_stock_list:
            continue_path = ensure_base_stock_continue_file(script_dir, initial_base_stock)

            for llm_cfg in llm_configs:
                api_key = resolve_api_key(llm_cfg)
                if not api_key:
                    print(f"Skipping {llm_cfg['name']}: missing API key.")
                    continue

                for (
                    dist,
                    external_opt,
                    n_train,
                    n_horizon,
                    order_option,
                    ec_m,
                    param_loc,
                    iter_opt,
                    algo_performance,
                    data_summary,
                ) in product(
                    dist_list,
                    external_opt_list,
                    n_train_list,
                    n_horizon_list,
                    order_option_list,
                    ec_m_list,
                    param_loc_list,
                    iter_opt_list,
                    algo_performance_list,
                    data_summary_list,
                ):
                    job_idx += 1
                    command = [
                        sys.executable,
                        "runEoH.py",
                        "--llm_api_endpoint",
                        llm_cfg["endpoint"],
                        "--llm_model",
                        llm_cfg["model"],
                        "--llm_api_key",
                        api_key,
                        "--problem",
                        problem,
                        "--ec_pop_size",
                        str(ec_pop_size),
                        "--ec_n_pop",
                        str(ec_n_pop),
                        "--ec_m",
                        str(ec_m),
                        "--dist",
                        dist,
                        "--external_opt",
                        external_opt,
                        "--n_train",
                        str(n_train),
                        "--n_horizon",
                        str(n_horizon),
                        "--order_option",
                        order_option,
                        "--iter_opt",
                        str(iter_opt),
                        "--algo_performance",
                        algo_performance,
                        "--data_summary",
                        data_summary,
                        "--operator",
                        *operator_list,
                        "--repeat",
                        str(repeat),
                        "--filename",
                        filename_tag,
                        "--param_loc",
                        param_loc,
                        "--exp_continue_path",
                        continue_path,
                        "--initial_base_stock",
                        str(initial_base_stock),
                    ]
                    reasoning_effort = llm_cfg.get("reasoning_effort")
                    if reasoning_effort:
                        command.extend(["--llm_reasoning_effort", reasoning_effort])
                    if prompt_with_explanations:
                        command.append("--prompt_with_explanations")

                    print(
                        f"[{job_idx}/{total_jobs}] Running {llm_cfg['name']} on {dist} "
                        f"(base_stock={initial_base_stock}, repeat={repeat})"
                    )
                    try:
                        subprocess.run(
                            command,
                            check=True,
                            cwd=script_dir,
                            env={**os.environ, "PYTHONPATH": f"../../eoh/src:{os.environ.get('PYTHONPATH', '')}"},
                        )
                    except subprocess.CalledProcessError as e:
                        print(
                            f"Command failed for {llm_cfg['name']} on {dist}, "
                            f"base_stock={initial_base_stock}, repeat={repeat}"
                        )
                        print(f"Error: {e}")


if __name__ == "__main__":
    main()
