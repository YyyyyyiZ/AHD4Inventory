import subprocess
import sys

print(sys.executable)  # path of python.exe

# option_list = ['stochastic','deterministic']
option_list = ['stochastic']
node_list = [50]
external_opt_list = ['scipy']
# external_opt_list =['no', 'ng', 'deap', 'scipy']
algo_performance_list = ['no', 'plain']
# algo_performance_list=['no','plain','processed']
data_summary_list = ['yes','no']
# data_summary_list = ['no','yes']
n_train_list = [50]
iter_opt_list = [30]
param_loc_list = ['default']
# param_loc_list = ['start', 'default']
repeat_num = 1

for repeat in range(repeat_num):
    repeat += 1
    for option in option_list:
        for n_node in node_list:
            for external_opt in external_opt_list:
                for n_train in n_train_list:
                    for param_loc in param_loc_list:  # invalid if external_optimizer=='no'
                        for iter_opt in iter_opt_list:  # invalid if external_optimizer=='no'
                            for algo_performance in algo_performance_list:
                                for data_summary in data_summary_list:
                                    command = (
                                        f"E:\\Anaconda3\\envs\\EoH\\python runEoH.py "  # change this line according to the path of python.exe
                                        f"--llm_api_key sk-20502d3c42ad4f3fb0df0d65f55ecc98 "
                                        f"--option {option} "
                                        f"--n_node {n_node} "
                                        f"--external_opt {external_opt} "
                                        f"--n_train {n_train} "
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
