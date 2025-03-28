### Test Only ###
# Set system path
import sys
import os
ABS_PATH = os.path.dirname(os.path.abspath(__file__))
ROOT_PATH = os.path.join(ABS_PATH, "..", "..")
sys.path.append(ROOT_PATH)  # This is for finding all the modules
sys.path.append(ABS_PATH)
print(ABS_PATH)
from eoh import eoh
from eoh.utils.getParas import Paras
# from evol.utils.createReport import ReportCreator
# 

# Parameter initilization #
paras = Paras() 

# Set parameters #
paras.set_paras(method = "eoh",    
                ec_operators  = ['e1','e2','m1','m2','m3'], # operators in EoH
                problem = "inventory", # ['tsp_construct','bp_online','tsp_gls','fssp_gls']
                llm_api_endpoint="api.deepseek.com",  # set your LLM endpoint
                llm_api_key="sk-ee82535575fc4c5183b171fc2ae7b1d0",  # set your key
                llm_model="deepseek-chat",
                ec_pop_size=4,  # number of samples in each population
                ec_n_pop=4,  # number of populations
                exp_n_proc=4,  # multi-core parallel
                exp_debug_mode=False,
                load_pop=True,
                load_pop_path="/results/pops/population_generation_0.json",
                load_pop_id=0
                )

# EoH initilization
evolution = eoh.EVOL(paras)

# run EoH
evolution.run()

# Generate EoH Report
# RC = ReportCreator(paras)
# RC.generate_doc_report()




