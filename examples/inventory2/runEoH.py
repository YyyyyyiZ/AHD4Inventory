from eoh import eoh
from eoh.utils.getParas import Paras
import sys
import argparse


parser = argparse.ArgumentParser('Run Inventory2')


# LLM Config
parser.add_argument('--llm_api_endpoint', type=str, default="api.deepseek.com")
parser.add_argument('--llm_api_key', type=str, default="sk-30f87012f8d040c18901307dc7b8bc12")
parser.add_argument('--llm_model', type=str, default="deepseek-chat")

parser.add_argument('--repeat', type=int, default=1, help='Repeat.')
parser.add_argument('--filename', type=str, default='res', help='Filename.')
parser.add_argument('--store_option', type=str, default='append', help='append or cover.')

# Data related
parser.add_argument('--dist', type=str, default='poisson1', help='Demand distribution.')
parser.add_argument('--mean', type=int, default=80, help='Demand mean.')
parser.add_argument('--n_train', type=int, default=50, help='Number of training trajectories.')

# Reflection
parser.add_argument('--prompt_type', type=str, default='old20')
# flow prompt pattern only when background_info=datasepp
parser.add_argument('--K1', type=int, default=0, help='Number of good performers.')
parser.add_argument('--K2', type=int, default=0, help='Number of bad performers.')

# Background Information
parser.add_argument('--background_info', type=str, default='no')
# sepp: no, exactdata, refonly, exactdataref
parser.add_argument('--background_type', type=str, default='nofix') # fix, nofix
# 'fix' valid only when background_info == sep
parser.add_argument('--data_sep', type=str, default='sepp')
# sep: independent data_reflector, second reflector `info` will be None
# sepp: independent data_reflector with performance on specified code and all trajectories, second reflector info will be data reflector result
parser.add_argument('--cal_cost', type=str, default='no')

# Optimizer
parser.add_argument('--external_opt', type=str, default='no', help='Type of external optimizer.')
parser.add_argument('--iter_opt', type=int, default=30, help='Iterations of external optimizer.')
parser.add_argument('--param_loc', type=str, default='default')


# General parameters
parser.add_argument('--ecc_pop_size', type=int, default=30, help='number of samples in each population')
parser.add_argument('--ec_n_pop', type=int, default=10, help='number of populations')
parser.add_argument('--exp_n_proc', type=int, default=4, help='multi-core parallel')
parser.add_argument('--exp_use_continue', type=int, default=1, help='# load existing heuristics.')
parser.add_argument('--exp_continue_path', type=str, default="results/pops/initial_pool.json", help='path to existing heuristics')
parser.add_argument('--exp_create_initial', type=int, default=0)
parser.add_argument('--exp_output_path', type=str, default='unknown', help='results wil be saved in "{exp_output_path}/pops')


args = parser.parse_args()
options = vars(args)
print(options)


args.exp_output_path = '_'.join([args.dist, str(args.mean), str(args.n_train),
                                 args.prompt_type, str(args.K1), str(args.K2),
                                 args.background_info, args.background_type, args.data_sep, args.cal_cost,
                                 args.external_opt, str(args.iter_opt), args.param_loc, 'r'+str(args.repeat)])


# Parameter initilization #
paras = Paras() 

# Set parameters #
paras.set_paras(method = "eoh",
                problem = "inventory2",
                dist = args.dist,   # normal
                demand = args.mean,
                volatility = 'low',
                n_train = args.n_train,
                llm_api_endpoint = args.llm_api_endpoint,  # LLM endpoint
                llm_api_key = args.llm_api_key,  # key
                llm_model = args.llm_model,  # Model
                ecc_pop_size = args.ecc_pop_size,  # number of samples in each population
                ec_n_pop= args.ec_n_pop,  # number of populations
                exp_n_proc = args.exp_n_proc,  # multi-core parallel
                exp_use_continue = args.exp_use_continue,    # load existing heuristics
                exp_continue_path =args.exp_continue_path,   # path to existing heuristics
                exp_create_initial = args.exp_create_initial,
                exp_output_path = args.exp_output_path,
                K1=args.K1,
                K2=args.K2,   # 'mimic_best_sample', 'correct_worst_sample', 'hybrid', 'multi_comparative_reflection'
                external_optimizer=args.external_opt,
                iter_opt = args.iter_opt,
                background_info=args.background_info,
                background_type=args.background_type,
                data_sep=args.data_sep,
                cal_cost=args.cal_cost,
                prompt_type=args.prompt_type,  # llm, tool
                repeat=args.repeat,
                filename=args.filename,
                store_option=args.store_option,
                param_loc = args.param_loc,
                )
print("Run Inventory2")
# initilization
evolution = eoh.EVOL(paras)

# run 
evolution.run()