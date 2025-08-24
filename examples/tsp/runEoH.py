from eoh import eoh
from eoh.utils.getParas import Paras
import sys
import argparse


parser = argparse.ArgumentParser('Run TSP')


# LLM Config
parser.add_argument('--llm_api_endpoint', type=str, default="api.deepseek.com")
parser.add_argument('--llm_api_key', type=str, default="")
parser.add_argument('--llm_model', type=str, default="deepseek-chat")

parser.add_argument('--repeat', type=int, default=1, help='Repeat.')
parser.add_argument('--filename', type=str, default='res', help='Filename.')
parser.add_argument('--store_option', type=str, default='append', help='append or cover.')

# Data related
parser.add_argument('--option', type=str, default='stochastic', help='stochastic or deterministic')
parser.add_argument('--n_node', type=int, default=50, help='Number of nodes.')
parser.add_argument('--n_train', type=int, default=50, help='Number of training scenarios.')

parser.add_argument('--data_summary', type=str, default='no')
parser.add_argument('--algo_performance', type=str, default='reflected')
# plain, processed, reflected

# Optimizer
parser.add_argument('--external_opt', type=str, default='no', help='Type of external optimizer.')
parser.add_argument('--iter_opt', type=int, default=30, help='Iterations of external optimizer.')
parser.add_argument('--param_loc', type=str, default='default')


# General parameters
parser.add_argument('--ecc_pop_size', type=int, default=30, help='number of samples in each population')
parser.add_argument('--ec_n_pop', type=int, default=5, help='number of populations')
parser.add_argument('--exp_n_proc', type=int, default=4, help='multi-core parallel')
parser.add_argument('--exp_use_continue', type=int, default=1, help='# load existing heuristics.')
parser.add_argument('--exp_continue_path', type=str, default="initial_pool.json", help='path to existing heuristics')
parser.add_argument('--exp_create_initial', type=int, default=0)
parser.add_argument('--exp_output_path', type=str, default='unknown', help='results wil be saved in "{exp_output_path}/pops')


args = parser.parse_args()
options = vars(args)


args.exp_output_path = '_'.join([args.llm_model, args.option, str(args.n_node), str(args.n_train),
                                 args.data_summary, args.algo_performance,
                                 args.external_opt, str(args.iter_opt), args.param_loc, 'r'+str(args.repeat)])


# Parameter initilization #
paras = Paras() 

# Set parameters #
paras.set_paras(method = "eoh",
                problem = "tsp",
                option = args.option,   # stochastic/deterministic
                n_node = args.n_node,
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
                data_summary=args.data_summary,
                algo_performance = args.algo_performance,
                external_optimizer=args.external_opt,
                iter_opt = args.iter_opt,
                repeat=args.repeat,
                filename=args.filename,
                store_option=args.store_option,
                param_loc = args.param_loc,
                )
print(F"Run TSP {args.option}")
# initilization
evolution = eoh.EVOL(paras)
# run 
evolution.run()