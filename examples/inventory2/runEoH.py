from eoh import eoh
from eoh.utils.getParas import Paras

# Parameter initilization #
paras = Paras() 

# Set parameters #
paras.set_paras(method = "eoh",
                problem = "inventory2",
                demand = 80,  # 50, 60, 70, 80
                volatility = 'low',  # low, median, high
                llm_api_endpoint = "api.deepseek.com",  # LLM endpoint
                llm_api_key = "sk-ee82535575fc4c5183b171fc2ae7b1d0",  # key
                llm_model = "deepseek-chat",  # Model
                ecc_pop_size = 10,  # number of samples in each population
                ec_n_pop= 2,  # number of populations
                exp_n_proc = 4,  # multi-core parallel
                exp_use_continue = True,    # load existing heuristics
                exp_continue_path ="results/pops/initial_pool.json",   # path to existing heuristics
                exp_create_initial = False,
                exp_output_path = "./results0",  # results wil be saved in "{exp_output_path}/pops"
                reflect = 'multi_comparative_reflection',  # 'mimic_best_sample', 'correct_worst_sample', 'hybrid', 'multi_comparative_reflection'
                external_optimizer=False)

# initilization
evolution = eoh.EVOL(paras)

# run 
evolution.run()