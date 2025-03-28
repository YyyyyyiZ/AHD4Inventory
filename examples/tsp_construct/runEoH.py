from eoh import eoh
from eoh.utils.getParas import Paras

# Parameter initilization #
paras = Paras() 

# Set parameters #
paras.set_paras(method = "eoh",    # ['ael','eoh']
                problem = "tsp_construct", #['tsp_construct','bp_online']
                llm_api_endpoint = "api.deepseek.com", # set your LLM endpoint
                llm_api_key = "sk-ee82535575fc4c5183b171fc2ae7b1d0",   # set your key
                llm_model = "deepseek-chat",
                ec_pop_size = 4, # number of samples in each population
                ec_n_pop = 4,  # number of populations
                exp_n_proc = 4,  # multi-core parallel
                exp_debug_mode = False)

# initilization
evolution = eoh.EVOL(paras)

# run 
evolution.run()