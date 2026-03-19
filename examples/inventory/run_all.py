import subprocess
import sys
import os

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
    'normal_std30_L6_c1_2',
    # 'normal_std30_L6_c1_5',

    # 'normal_std50_L2_c1_2',
    # 'normal_std50_L2_c1_5',
    # 'normal_std50_L4_c1_2',
    # 'normal_std50_L4_c1_5',
    # 'normal_std50_L6_c1_2',
    # 'normal_std50_L6_c1_5',

    # 'poisson_L2_c1_2','poisson_L2_c1_5','poisson_L4_c1_2','poisson_L4_c1_5',
    'poisson_L6_c1_2',
    # 'poisson_L6_c1_5',

    # 'exponential_L2_c1_2','exponential_L2_c1_5','exponential_L4_c1_2','exponential_L4_c1_5',
    'exponential_L6_c1_2',
    # 'exponential_L6_c1_5',
]
problem = "inventory"  # inventory
ec_pop_size = 10  # Feng: Fixed number of offsprings for each operator
ec_n_pop = 10  # Feng: Fixed Number of generations
ec_m_list = [2, 4, 6, 8]  # Feng: Fixed Number of parents for m2
external_opt_list = ['scipy']  # external_opt_list =['no', 'ng', 'deap', 'scipy']
algo_performance_list = [
    'processed']  # no: no performance feedback, plain: detailed trajectories, processed: statistical summaries
data_summary_list = ['plain']  # data_summary_list = ['no','plain','processed']
n_train_list = [50]  # Feng: Number of training trajectories
n_horizon_list = [50]  # n_horizon_list = [3, 5, 10, 20, 50]
iter_opt_list = [15]
param_loc_list = ['default']  # param_loc_list = ['start', 'default']
param_num_list = [1,2,4]  # param_num_list = [10, 1, 2, 4], 10 is the default restriction
order_option_list = ['order_before_sell']
operator_list = ['m2plural']  # 'e1', 'e2', 'm2','m2plural',
repeat_num = 5  # Feng: Number of repeats, aim for 10 repeats on each dataset
prompt_with_explanations = False  # include DESCRIPTION/INTUITION/REASONING in m2 prompts

for repeat in range(repeat_num):
    repeat += 1
    for dist in dist_list:
        for external_opt in external_opt_list:
            for n_train in n_train_list:
                for n_horizon in n_horizon_list:
                    for order_option in order_option_list:
                        for ec_m in ec_m_list:
                            for param_num in param_num_list:
                                for param_loc in param_loc_list:  # invalid if external_optimizer=='no'
                                    for iter_opt in iter_opt_list:  # invalid if external_optimizer=='no'
                                        for algo_performance in algo_performance_list:
                                            for data_summary in data_summary_list:
                                                command = (
                                                    # f"/zfs/projects/faculty/yh2987-choice-modeling/.venv/bin/python runEoH.py "
                                                    # f"/home/sjtu/.conda/envs/ahd/bin/python runEoH.py "
                                                    f"E:\\Anaconda3\\envs\\EoH\\python runEoH.py "
                                                    # f"python3 runEoH.py "  # change this line according to the path of python.exe
                                                    # f"--llm_api_key {os.getenv('OPENROUTER_API_KEY', '')} "
                                                    f"--llm_api_key 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 "
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
                                                    f"--param_num {param_num} "
                                                    f"--algo_performance {algo_performance} "
                                                    f"--data_summary {data_summary} "
                                                    f"--operator {' '.join(operator_list)} "
                                                    f"--repeat {repeat} "
                                                    f"--filename m2plural "  # Feng: Output filename
                                                    f"{'--prompt_with_explanations ' if prompt_with_explanations else ''}"
                                                )
                                                print(f"Running: {command}")
                                                try:
                                                    subprocess.run(command, shell=True, check=True)
                                                except subprocess.CalledProcessError as e:
                                                    print(f"Command failed: {command}")
                                                    print(f"Error: {e}")
