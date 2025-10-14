from eoh import eoh
from eoh.utils.getParas import Paras
import sys
import argparse

parser = argparse.ArgumentParser('Run Inventory_ex')

# LLM Config
parser.add_argument('--llm_api_endpoint', type=str, default="api.deepseek.com")
# api.openai.com, api.deepseek.com
parser.add_argument('--llm_api_key', type=str, default="")
# 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
parser.add_argument('--llm_model', type=str, default="deepseek-chat")
# gpt-4.1, deepseek-chat

parser.add_argument('--repeat', type=int, default=1, help='Repeat.')
parser.add_argument('--filename', type=str, default='res', help='Filename.')
parser.add_argument('--store_option', type=str, default='append', help='append or cover.')
parser.add_argument('--order_option', type=str, default='order_before_sell', help='order before or after sell.')

# Data related
parser.add_argument('--dist', type=str, default='poisson1', help='Demand distribution.')
parser.add_argument('--mean', type=int, default=80, help='Demand mean.')
parser.add_argument('--n_train', type=int, default=50, help='Number of training trajectories.')
parser.add_argument('--n_horizon', type=int, default=3, help='Number of horizons.')

parser.add_argument('--data_summary', type=str, default='no')
parser.add_argument('--algo_performance', type=str, default='no')
# no, plain, processed
parser.add_argument('--prompt_version', type=str, default='v2', help='Prompt version: v1 (old) or v2 (new)')


# Optimizer
parser.add_argument('--external_opt', type=str, default='no', help='Type of external optimizer.')
parser.add_argument('--iter_opt', type=int, default=30, help='Iterations of external optimizer.')
parser.add_argument('--param_loc', type=str, default='default')
parser.add_argument('--operator', type=str, default='m1', help='Evolution operator: m1, m2, or m1,m2')

# General parameters
parser.add_argument('--ecc_pop_size', type=int, default=4, help='number of samples in each population')
parser.add_argument('--ec_n_pop', type=int, default=5, help='number of populations')
parser.add_argument('--exp_n_proc', type=int, default=4, help='multi-core parallel')
parser.add_argument('--exp_use_continue', type=int, default=1, help='# load existing heuristics.')
parser.add_argument('--exp_continue_path', type=str, default="initial_pool.json", help='path to existing heuristics')
parser.add_argument('--exp_create_initial', type=int, default=0)
parser.add_argument('--exp_output_path', type=str, default='unknown',
                    help='results wil be saved in "{exp_output_path}/pops')

args = parser.parse_args()
options = vars(args)
# print(options)

# Automatically select initial pool file based on version if using default
if args.exp_continue_path == "initial_pool.json" and args.prompt_version == 'v1':
    args.exp_continue_path = "initial_pool_v1.json"
    print(f"Note: Using {args.exp_continue_path} for prompt version v1")

args.exp_output_path = '_'.join([args.llm_model, args.dist, str(args.mean), str(args.n_train), str(args.n_horizon),
                                 args.data_summary, args.algo_performance,
                                 args.external_opt, str(args.iter_opt), args.param_loc, args.operator, 'r' + str(args.repeat)])

# Parameter initilization #
paras = Paras()

# Parse operator argument (support comma-separated values like "m1,m2")
operator_list = [op.strip() for op in args.operator.split(',')]

# Set parameters #
paras.set_paras(method="eoh",
                problem="inventory_ex",
                dist=args.dist,  # normal
                demand=args.mean,
                volatility='low',
                n_train=args.n_train,
                n_horizon=args.n_horizon,
                llm_api_endpoint=args.llm_api_endpoint,  # LLM endpoint
                llm_api_key=args.llm_api_key,  # key
                llm_model=args.llm_model,  # Model
                ecc_pop_size=args.ecc_pop_size,  # number of samples in each population
                ec_n_pop=args.ec_n_pop,  # number of populations
                ec_operators=operator_list,  # Evolution operators
                exp_n_proc=args.exp_n_proc,  # multi-core parallel
                exp_use_continue=args.exp_use_continue,  # load existing heuristics
                exp_continue_path=args.exp_continue_path,  # path to existing heuristics
                exp_create_initial=args.exp_create_initial,
                exp_output_path=args.exp_output_path,
                data_summary=args.data_summary,
                algo_performance=args.algo_performance,
                external_optimizer=args.external_opt,
                iter_opt=args.iter_opt,
                repeat=args.repeat,
                filename=args.filename,
                store_option=args.store_option,
                order_option=args.order_option,
                param_loc=args.param_loc,
                prompt_version=args.prompt_version,
                )
print("Run Inventory Toy Example")
# initilization
evolution = eoh.EVOL(paras)

# run 
evolution.run()
