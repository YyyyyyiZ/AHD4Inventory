import subprocess
import sys

print(sys.executable)  # path of python.exe

# === DATASET CONFIGURATION ===
# Feng: Modify this part to select the dataset that you want to run
# Feng: What we need is normal_std10, normal_std30, normal_std50, poisson, exponenial
dist_list = [

    # 'normal_std10_L2_c1_2','normal_std10_L2_c1_5','normal_std10_L4_c1_2','normal_std10_L4_c1_5','normal_std10_L6_c1_2','normal_std10_L6_c1_5',

    # 'normal_std30_L2_c1_2',
    # 'normal_std30_L2_c1_5',
    # 'normal_std30_L4_c1_2',
    # 'normal_std30_L4_c1_5',
    # 'normal_std30_L6_c1_2',
    # 'normal_std30_L6_c1_5',

    'normal_std50_L2_c1_2',
    'normal_std50_L2_c1_5',
    'normal_std50_L4_c1_2',
    'normal_std50_L4_c1_5',
    'normal_std50_L6_c1_2',
    'normal_std50_L6_c1_5',

    # 'poisson_L2_c1_2','poisson_L2_c1_5','poisson_L4_c1_2','poisson_L4_c1_5','poisson_L6_c1_2','poisson_L6_c1_5',

    # 'exponential_L2_c1_2','exponential_L2_c1_5','exponential_L4_c1_2','exponential_L4_c1_5','exponential_L6_c1_2','exponential_L6_c1_5',

    # Feng: normal_std20 and lomax are no longer needed in our full model
    ## 'normal_std20_L2_c1_2','normal_std20_L2_c1_5','normal_std20_L4_c1_2','normal_std20_L4_c1_5','normal_std20_L6_c1_2','normal_std20_L6_c1_5',
    ## 'lomax_L2_c1_2','lomax_L2_c1_5','lomax_L4_c1_2','lomax_L4_c1_5','lomax_L6_c1_2','lomax_L6_c1_5',
]
problem = "inventory"  # inventory
ec_pop_size = 1 # Feng: Fixed number of offsprings for each operator
ec_n_pop = 15 # Feng: Fixed Number of generations
ec_m = 1 # Feng: Fixed Number of parents for e1 and e2
external_opt_list = ['scipy']  # external_opt_list =['no', 'ng', 'deap', 'scipy']
algo_performance_list = ['processed']  # no: no performance feedback, plain: detailed trajectories, processed: statistical summaries
data_summary_list = ['plain']  # data_summary_list = ['no','plain','processed']
n_train_list = [50] # Feng: Number of training trajectories
n_horizon_list = [50]  # n_horizon_list = [3, 5, 10, 20, 50]
iter_opt_list = [15]
param_loc_list = ['default']  # param_loc_list = ['start', 'default']
order_option_list = ['order_before_sell']
operator_list = ['e1', 'e2', 'm2']  # 'e1', 'e2', 'm2'
repeat_num = 1 # Feng: Number of repeats, aim for 10 repeats on each dataset

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
                                            f"python3 runEoH.py "  # Feng: change this line according to your path
                                            f"--llm_api_key sk-b91d11eb3de9494db3a48cae9568ba49 " # Feng: When running a script, use a unique API key.
                                            f"--problem {problem} "
                                            f"--ec_pop_size {ec_pop_size} "
                                            f"--ec_n_pop {ec_n_pop} "
                                            f"--ec_m {ec_m} "
                                            f"--dist {dist} "
                                            f"--external_opt {external_opt} "
                                            f"--n_train {n_train} "
                                            f"--n_horizon {n_horizon} "
                                            f"--order_option {order_option} "
                                            f"--iter_opt {iter_opt} "
                                            f"--algo_performance {algo_performance} "
                                            f"--data_summary {data_summary} "
                                            f"--operator {' '.join(operator_list)} "
                                            f"--repeat {repeat} "
                                            f"--filename template_active " # Feng: Output filename
                                        )
                                        print(f"Running: {command}")
                                        try:
                                            subprocess.run(command, shell=True, check=True)
                                        except subprocess.CalledProcessError as e:
                                            print(f"Command failed: {command}")
                                            print(f"Error: {e}")
