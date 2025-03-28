from eoh import eoh
from eoh.utils.getParas import Paras
from prob import Evaluation

# Parameter initilization #
paras = Paras() 

# Set your local problem
problem_local = Evaluation()

# Set parameters #
paras.set_paras(method = "eoh",    # ['ael','eoh']
                problem = problem_local, # Set local problem, else use default problems
                llm_api_endpoint="api.deepseek.com",  # set your LLM endpoint
                llm_api_key="sk-ee82535575fc4c5183b171fc2ae7b1d0",  # set your key
                llm_model="deepseek-chat",
                ec_pop_size = 4, # number of samples in each population
                ec_n_pop = 4,  # number of populations
                exp_n_proc = 1,  # multi-core parallel
                exp_debug_mode = False,
                eva_numba_decorator = False)

# initilization
evolution = eoh.EVOL(paras)

# run 
evolution.run()