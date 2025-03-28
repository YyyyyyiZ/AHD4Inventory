from eoh import eoh
from eoh.utils.getParas import Paras

# Parameter initilization #
paras = Paras() 

# Set parameters #
paras.set_paras(method = "eoh",
                problem = "inventory",
                demand = 60,  # 50, 60, 70, 80
                volatility = 'low',  # low, median, high
                llm_api_endpoint = "api.deepseek.com",  # LLM endpoint
                llm_api_key = "sk-ee82535575fc4c5183b171fc2ae7b1d0",  # key
                llm_model = "deepseek-chat",  # Model
                ecc_pop_size = 4,  # number of samples in each population
                ec_n_pop= 4,  # number of populations
                exp_n_proc = 4,  # multi-core parallel
                exp_debug_mode = False,
                exp_use_continue = True,
                create_initial = False,
                load_pop_path ="results/pops/population_generation_0.json",
                load_pop_id = 0)

# initilization
evolution = eoh.EVOL(paras)

# run 
evolution.run()