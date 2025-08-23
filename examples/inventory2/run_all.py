import subprocess
import sys

print(sys.executable)      # path of python.exe


# dist_list = ['poisson1','normal1']
dist_list = ['poisson1']
mean_list = [80]
prompt_type_list = ['old20']
external_opt_list =['scipy']
# external_opt_list =['no', 'ng', 'deap', 'scipy']
algo_performance_list=['reflected']
# algo_performance_list=['no','plain','processed','reflected']
data_summary_list = ['no']
# data_summary_list = ['no','yes']
n_train_list = [10]
iter_opt_list = [2]
param_loc_list = ['default']
# param_loc_list = ['start', 'default']
repeat_num=1

for repeat in range(repeat_num):
    repeat += 1
    for dist in dist_list:
        for mean_demand in mean_list:
            for external_opt in external_opt_list:
                for n_train in n_train_list:
                    for param_loc in param_loc_list:    # invalid if external_optimizer=='no'
                        for iter_opt in iter_opt_list:    # invalid if external_optimizer=='no'
                            for algo_performance in algo_performance_list:
                                for data_summary in data_summary_list:
                                    command = (
                                        f"E:\\Anaconda3\\envs\\EoH\\python runEoH.py "  # change this line according to the path of python.exe
                                        f"--llm_api_key sk-2f6742f460b24ab68c9580a3fd367493 "
                                        f"--dist {dist} "
                                        f"--mean {mean_demand} "
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
