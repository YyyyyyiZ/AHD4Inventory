import subprocess
import sys

print(sys.executable)  # path of python.exe

# === DATASET CONFIGURATION ===
dist_list = [
    'normal_std30_L2_c1_5'
    # normal (std = 10, 20, 30)
    # 'normal_std10_L2_c1_2','normal_std10_L2_c1_5','normal_std10_L4_c1_2','normal_std10_L4_c1_5','normal_std10_L6_c1_2','normal_std10_L6_c1_5',
    # 'normal_std20_L2_c1_2','normal_std20_L2_c1_5','normal_std20_L4_c1_2','normal_std20_L4_c1_5','normal_std20_L6_c1_2','normal_std20_L6_c1_5',
    # 'normal_std30_L2_c1_2', 'normal_std30_L2_c1_5', 'normal_std30_L4_c1_2', 'normal_std30_L4_c1_5',
    # 'normal_std30_L6_c1_2', 'normal_std30_L6_c1_5',

    # # poisson
    # 'poisson_L2_c1_2','poisson_L2_c1_5','poisson_L4_c1_2','poisson_L4_c1_5','poisson_L6_c1_2','poisson_L6_c1_5',

    # # exponential
    # 'exponential_L2_c1_2','exponential_L2_c1_5','exponential_L4_c1_2','exponential_L4_c1_5','exponential_L6_c1_2','exponential_L6_c1_5',
    #
    # # pareto
    # 'pareto_L2_c1_2','pareto_L2_c1_5','pareto_L4_c1_2','pareto_L4_c1_5','pareto_L6_c1_2','pareto_L6_c1_5',
]
problem = "inventory2"     # inventory2 inventory_ex
ec_pop_size = 10
external_opt_list = ['no']       # external_opt_list =['no', 'ng', 'deap', 'scipy']
algo_performance_list = ['processed']     # no: no performance feedback, plain: detailed trajectories, processed: statistical summaries
data_summary_list = ['plain']       # data_summary_list = ['no','plain','processed']
n_train_list = [50]
n_horizon_list = [50]       # n_horizon_list = [3, 5, 10, 20, 50]
iter_opt_list = [15]
param_loc_list = ['default']        # param_loc_list = ['start', 'default']
order_option_list = ['order_before_sell']
operator_list = ['e1', 'e2', 'm2']
repeat_num = 10

for repeat in range(repeat_num):
    repeat += 1
    for dist in dist_list:
        for external_opt in external_opt_list:
            for n_train in n_train_list:
                for n_horizon in n_horizon_list:
                    for order_option in order_option_list:
                        for param_loc in param_loc_list:  # invalid if external_optimizer=='no'
                            for iter_opt in iter_opt_list:  # invalid if external_optimizer=='no'
                                for algo_performance in algo_performance_list:
                                    for data_summary in data_summary_list:
                                        command = (
                                            f"E:\\Anaconda3\\envs\\EoH\\python runEoH.py "  # change this line according to the path of python.exe
                                            f"--llm_api_key sk-8dad0165ee794c5ab892db1612a33cbb "  # sk-b91d11eb3de9494db3a48cae9568ba49; sk-5d290dc8a98e43c99f0e5d09ffb40d72; sk-a27cbbbd15504a278f922fd3204d8ddd; sk-faf6d1042965448d8315ff9122b56990; sk-01975fe796644850a6d96accf30b2480; sk-8dad0165ee794c5ab892db1612a33cbb
                                            f"--problem {problem} "
                                            f"--ec_pop_size {ec_pop_size} "
                                            f"--dist {dist} "
                                            f"--external_opt {external_opt} "
                                            f"--n_train {n_train} "
                                            f"--n_horizon {n_horizon} "
                                            f"--order_option {order_option} "
                                            f"--iter_opt {iter_opt} "
                                            f"--algo_performance {algo_performance} "
                                            f"--data_summary {data_summary} "
                                            f"--operator {' '.join(operator_list)} "
                                            f"--filename template2 "
                                            f"--store_option append "
                                        )
                                        print(f"Running: {command}")
                                        try:
                                            subprocess.run(command, shell=True, check=True)
                                        except subprocess.CalledProcessError as e:
                                            print(f"Command failed: {command}")
                                            print(f"Error: {e}")
