from eoh import eoh
from eoh.utils.getParas import Paras
import sys
import argparse
import os

parser = argparse.ArgumentParser('Inventory Problems')

parser.add_argument('--problem', type=str, default="inventory")

# LLM Config
# parser.add_argument('--llm_api_endpoint', type=str, default="https://generativelanguage.googleapis.com/v1beta/openai/")
# parser.add_argument('--llm_api_endpoint', type=str, default="https://api.openai.com")
parser.add_argument('--llm_api_endpoint', type=str, default="https://api.deepseek.com")
parser.add_argument('--llm_api_key', type=str, default="")
# parser.add_argument('--llm_model', type=str, default="gemini-3-flash-preview")
parser.add_argument('--llm_model', type=str, default="deepseek-chat")
# parser.add_argument('--llm_model', type=str, default="gpt-5-nano")
parser.add_argument(
    '--llm_profile',
    type=str,
    default='none',
    choices=[
        'none',
        'gemini-direct-3.0-flash',
        'openrouter-minimax-fast',
        'openrouter-deepseek-fast',
        'openrouter-gemini-2.5-fast',
        'openrouter-gpt-5-nano',
        'openrouter-gpt-5-mini',
        'openrouter-gemini-3.0-preview',
        'openrouter-grok-4.1-fast',
    ],
    help='Preset endpoint/model for quick provider switching.',
)
parser.add_argument('--llm_reasoning_effort', type=str, default=None,
                    help='Optional reasoning effort level. If omitted, the provider/model default is used.')

parser.add_argument('--repeat', type=int, default=1, help='Repeat.')
parser.add_argument('--filename', type=str, default='res', help='Result Output Filename.')
parser.add_argument('--order_option', type=str, default='order_before_sell', help='order before or after sell.')

# Data related
parser.add_argument('--dist', type=str, default='normal_std30_L6_c1_5', help='Demand distribution.')
parser.add_argument('--n_train', type=int, default=50, help='Number of training trajectories.')
parser.add_argument('--n_horizon', type=int, default=50, help='Number of horizons.')

parser.add_argument('--data_summary', type=str, default='no')
parser.add_argument('--algo_performance', type=str, default='no')
parser.add_argument('--prompt_version', type=str, default='v2', help='Prompt version: v1 (old) or v2 (new)')
parser.add_argument('--prompt_with_explanations', action='store_true',
                    help='Include DESCRIPTION/INTUITION/REASONING sections in m2 prompts.')

# Optimizer
parser.add_argument('--external_opt', type=str, default='no', help='Type of external optimizer.')
parser.add_argument('--iter_opt', type=int, default=15, help='Iterations of external optimizer.')
parser.add_argument('--param_loc', type=str, default='default')
parser.add_argument("--operator", nargs="+", type=str)

# General parameters
parser.add_argument('--ec_pop_size', type=int, default=4, help='number of samples in each population')
parser.add_argument('--ec_n_pop', type=int, default=10, help='number of populations')
parser.add_argument('--ec_m', type=int, default=2, help='number of parents for e1 and e2 operators')
parser.add_argument('--exp_n_proc', type=int, default=4, help='multi-core parallel')
parser.add_argument('--exp_use_continue', type=int, default=1, help='# load existing heuristics.')
parser.add_argument('--exp_continue_path', type=str, default="base_stock.json", help='path to existing heuristics')
parser.add_argument('--initial_base_stock', type=float, default=None,
                    help='Seed base-stock value used to construct the initial continuation policy.')
parser.add_argument('--exp_create_initial', type=int, default=0)
parser.add_argument('--exp_output_path', type=str, default='unknown',
                    help='results wil be saved in "{exp_output_path}/pops')

args = parser.parse_args()
options = vars(args)
# print(options)

OPENROUTER_PRESETS = {
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
        "model": "google/gemini-2.5-flash",
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

if args.llm_profile != "none":
    profile = OPENROUTER_PRESETS[args.llm_profile]
    args.llm_api_endpoint = profile["endpoint"]
    args.llm_model = profile["model"]
    args.llm_reasoning_effort = profile.get("reasoning_effort")
    if not args.llm_api_key:
        args.llm_api_key = os.environ.get(profile["api_key_env"], "")

if not args.llm_api_key:
    raise ValueError(
        "Missing --llm_api_key. Set the provider API key env var or pass --llm_api_key explicitly."
    )

# Automatically select initial pool file based on version if using default
if args.exp_continue_path == "initial_pool.json" and args.prompt_version == 'v1':
    args.exp_continue_path = "initial_pool_v1.json"
    print(f"Note: Using {args.exp_continue_path} for prompt version v1")

args.exp_output_path = '_'.join([args.llm_model, args.dist, str(args.n_train), args.data_summary, args.algo_performance,
                                 args.external_opt, str(args.iter_opt), args.param_loc, '-'.join(args.operator), str(args.ec_m),
                                 'r' + str(args.repeat)])

# Parameter initilization #
paras = Paras()

# Set parameters #
paras.set_paras(method="eoh",
                problem=args.problem,
                dist=args.dist,
                n_train=args.n_train,
                n_horizon=args.n_horizon,
                llm_api_endpoint=args.llm_api_endpoint,  # LLM endpoint
                llm_api_key=args.llm_api_key,  # key
                llm_model=args.llm_model,  # Model
                llm_reasoning_effort=args.llm_reasoning_effort,  # Reasoning effort
                ec_pop_size=args.ec_pop_size,  # number of samples in each population
                ec_n_pop=args.ec_n_pop,  # number of populations
                ec_operators=args.operator,  # Evolution operators
                ec_m=args.ec_m,
                exp_n_proc=args.exp_n_proc,  # multi-core parallel
                exp_use_continue=args.exp_use_continue,  # load existing heuristics
                exp_continue_path=args.exp_continue_path,  # path to existing heuristics
                initial_base_stock=args.initial_base_stock,
                exp_create_initial=args.exp_create_initial,
                exp_output_path=args.exp_output_path,
                data_summary=args.data_summary,
                algo_performance=args.algo_performance,
                external_optimizer=args.external_opt,
                iter_opt=args.iter_opt,
                repeat=args.repeat,
                filename=args.filename,
                order_option=args.order_option,
                param_loc=args.param_loc,
                prompt_version=args.prompt_version,
                prompt_with_explanations=args.prompt_with_explanations,
                )
if args.problem == 'inventory':
    print("Run Inventory")
elif args.problem == 'inventory_ex':
    print("Run Inventory Toy Example")
else:
    raise ValueError("Invalid Problem")

# initilization
evolution = eoh.EVOL(paras)

# run
evolution.run()
