import subprocess
import sys

print(sys.executable)  # path of python.exe

dist_list = ['normal1']
# normal0: initial_inventory=0, normal1: initial_inventory=80, normal2: initial_inventory=60
mean_list = [80]
external_opt_list = ['no']
# external_opt_list =['no', 'ng', 'deap', 'scipy']
algo_performance_list = ['no']
# no: no performance feedback, plain: detailed trajectories, processed: statistical summaries
data_summary_list = ['plain']
# data_summary_list = ['no','plain','processed']
n_train_list = [50]
n_horizon_list = [50]
# n_horizon_list = [3, 5, 10, 20, 50]
iter_opt_list = [30]
param_loc_list = ['default']
# param_loc_list = ['start', 'default']
order_option_list = ['order_before_sell']
repeat_num = 2

for repeat in range(repeat_num):
    repeat += 1
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
                                            command = (
                                                f"python3 runEoH.py "  # change this line according to the path of python.exe
                                                f"--llm_api_key sk-5d290dc8a98e43c99f0e5d09ffb40d72 "
                                                f"--dist {dist} "
                                                f"--mean {mean_demand} "
                                                f"--external_opt {external_opt} "
                                                f"--n_train {n_train} "
                                                f"--n_horizon {n_horizon} "
                                                f"--order_option {order_option} "
                                                f"--iter_opt {iter_opt} "
                                                f"--algo_performance {algo_performance} "
                                                f"--data_summary {data_summary} "
                                                f"--repeat {repeat} "
                                                f"--filename res "
                                                f"--store_option append "
                                            )
                                            print(f"Running: {command}")
                                            try:
                                                subprocess.run(command, shell=True, check=True)
                                            except subprocess.CalledProcessError as e:
                                                print(f"Command failed: {command}")
                                                print(f"Error: {e}")
