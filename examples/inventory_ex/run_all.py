import subprocess
import sys

print(sys.executable)  # path of python.exe

# === DATASET CONFIGURATION ===
# Original datasets (holding_cost=2, lost_sales_cost=10):
# Lead time = 1: normal0 (initial_inventory=0), normal1 (initial_inventory=80), normal2 (initial_inventory=60)
# Lead time = 2: leadtime2_0 (initial_inventory=0), leadtime2_1 (initial_inventory=80), leadtime2_2 (initial_inventory=60)
# Lead time = 3: leadtime3_0 (initial_inventory=0), leadtime3_1 (initial_inventory=80), leadtime3_2 (initial_inventory=60)
#
# New datasets (holding_cost=2, lost_sales_cost=4):
# Lead time = 1: cost2_4_lt1_0 (initial_inventory=0)
# Lead time = 2: cost2_4_lt2_0 (initial_inventory=0)
# Lead time = 3: cost2_4_lt3_0 (initial_inventory=0)

# Uncomment one of the following lines to test different configurations:
# dist_list = ['normal1']           # Lead time = 1, initial_inventory = 80
# dist_list = ['normal0', 'leadtime2_0', 'leadtime3_0', 'cost2_4_lt1_0', 'cost2_4_lt2_0',
#              'cost2_4_lt3_0']  # Lead time = 1, initial_inventory = 0
dist_list = [
    # normal (std = 10, 20, 30)
    # 'normal_std10_L2_c1_2','normal_std10_L2_c1_5','normal_std10_L4_c1_2','normal_std10_L4_c1_5','normal_std10_L6_c1_2','normal_std10_L6_c1_5',
    # 'normal_std20_L2_c1_2','normal_std20_L2_c1_5','normal_std20_L4_c1_2','normal_std20_L4_c1_5','normal_std20_L6_c1_2','normal_std20_L6_c1_5',
    'normal_std30_L2_c1_2', 'normal_std30_L2_c1_5', 'normal_std30_L4_c1_2', 'normal_std30_L4_c1_5',
    'normal_std30_L6_c1_2', 'normal_std30_L6_c1_5',

    # # poisson
    # 'poisson_L2_c1_2','poisson_L2_c1_5','poisson_L4_c1_2','poisson_L4_c1_5','poisson_L6_c1_2','poisson_L6_c1_5',
    #
    # # exponential
    # 'exponential_L2_c1_2','exponential_L2_c1_5','exponential_L4_c1_2','exponential_L4_c1_5','exponential_L6_c1_2','exponential_L6_c1_5',
    #
    # # pareto
    # 'pareto_L2_c1_2','pareto_L2_c1_5','pareto_L4_c1_2','pareto_L4_c1_5','pareto_L6_c1_2','pareto_L6_c1_5',
]

# dist_list = ['normal0']           # Lead time = 1, initial_inventory = 0
# dist_list = ['leadtime2_1']       # Lead time = 2, initial_inventory = 80
# dist_list = ['leadtime2_0']       # Lead time = 2, initial_inventory = 0
# dist_list = ['leadtime2_2']       # Lead time = 2, initial_inventory = 60
# dist_list = ['leadtime3_1']       # Lead time = 3, initial_inventory = 80
# dist_list = ['leadtime3_0']       # Lead time = 3, initial_inventory = 0
# dist_list = ['leadtime3_2']       # Lead time = 3, initial_inventory = 60
# dist_list = ['cost2_4_lt1_0', 'cost2_4_lt2_0']     # Lead time = 1, initial_inventory = 0, holding_cost=2, lost_sales_cost=4
# dist_list = ['cost2_4_lt2_0']     # Lead time = 2, initial_inventory = 0, holding_cost=2, lost_sales_cost=4
# dist_list = ['cost2_4_lt3_0']     # Lead time = 3, initial_inventory = 0, holding_cost=2, lost_sales_cost=4

# Compare multiple configurations:
# dist_list = ['normal1', 'leadtime2_1']  # Compare lead time 1 vs 2 (same initial inventory)
# dist_list = ['normal1', 'leadtime2_1', 'leadtime3_1']  # Compare all lead times (same initial inventory)
# dist_list = ['cost2_4_lt1_0', 'cost2_4_lt2_0', 'cost2_4_lt3_0']  # Compare all lead times with cost2_4
mean_list = [80]
external_opt_list = ['no']
# external_opt_list =['no', 'ng', 'deap', 'scipy']
algo_performance_list = ['no', 'processed']
# no: no performance feedback, plain: detailed trajectories, processed: statistical summaries
data_summary_list = ['plain']
# data_summary_list = ['no','plain','processed']
n_train_list = [50]
n_horizon_list = [50]
# n_horizon_list = [3, 5, 10, 20, 50]
iter_opt_list = [15]
param_loc_list = ['default']
# param_loc_list = ['start', 'default']
order_option_list = ['order_before_sell']
operator_list = ['m2']  # Choose from: 'm1', 'm2', 'm3', or combinations
# Operator options:
# 'm1': Only parameter adjustment (restrictive)
# 'm2': Parameter adjustment OR structure change (flexible, but LLMs tend to be lazy)
# 'm3': MUST change structure (forces innovation)
# ['m1', 'm3']: Test parameter-only vs structure-only separately
# ['m1,m3']: Use both operators in same run (50% each)
# ['m1', 'm2', 'm3']: Test all three approaches separately
repeat_num = 3

for repeat in range(repeat_num):
    repeat += 4
    for dist in dist_list:
        for mean_demand in mean_list:
            for external_opt in external_opt_list:
                for n_train in n_train_list:
                    for n_horizon in n_horizon_list:
                        for order_option in order_option_list:
                            for param_loc in param_loc_list:  # invalid if external_optimizer=='no'
                                for iter_opt in iter_opt_list:  # invalid if external_optimizer=='no'
                                    for algo_performance in algo_performance_list:
                                        for data_summary in data_summary_list:
                                            for operator in operator_list:
                                                command = (
                                                    f"E:\\Anaconda3\\envs\\EoH\\python runEoH.py "  # change this line according to the path of python.exe
                                                    f"--llm_api_key sk-8dad0165ee794c5ab892db1612a33cbb "  # sk-b91d11eb3de9494db3a48cae9568ba49; sk-5d290dc8a98e43c99f0e5d09ffb40d72; sk-a27cbbbd15504a278f922fd3204d8ddd; sk-faf6d1042965448d8315ff9122b56990; sk-01975fe796644850a6d96accf30b2480; sk-8dad0165ee794c5ab892db1612a33cbb
                                                    f"--dist {dist} "
                                                    f"--mean {mean_demand} "
                                                    f"--external_opt {external_opt} "
                                                    f"--n_train {n_train} "
                                                    f"--n_horizon {n_horizon} "
                                                    f"--order_option {order_option} "
                                                    f"--iter_opt {iter_opt} "
                                                    f"--algo_performance {algo_performance} "
                                                    f"--data_summary {data_summary} "
                                                    f"--operator {operator} "
                                                    f"--repeat {repeat} "
                                                    f"--filename template "
                                                    f"--store_option append "
                                                )
                                                print(f"Running: {command}")
                                                try:
                                                    subprocess.run(command, shell=True, check=True)
                                                except subprocess.CalledProcessError as e:
                                                    print(f"Command failed: {command}")
                                                    print(f"Error: {e}")
