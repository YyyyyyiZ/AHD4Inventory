import subprocess
import sys

print(sys.executable)      # path of python.exe

# exclude_config = {
#     'cfg_1': {
#         'dist': 'poisson',
#         'mean': 80,
#         'volatility':'low',
#         'prompt_type': 'original',
#         'background_info':'no',
#         'external_opt': 'no'
#     },
#     'cfg_2': {
#             'dist': 'poisson',
#             'mean': 80,
#             'volatility':'low',
#             'prompt_type': 'original',
#             'background_info':'no',
#             'external_opt': 'scipy'
#         },
# }


dist_list = ['poisson1','poisson2','normal1','normal2']
mean_list = [80]
prompt_type_list = ['flowinf']
background_info_list = ['exactdata']
# background_info_list = ['exactdata', 'refonly', 'exactdataref']
background_type_list = ['nofix']
data_sep_list = ['sepp']
cal_cost_list = ['no']
external_opt_list =['scipy']
k1k2_list=[(1,0),(2,0), (3,0),(4,0),
           (1,1),(2,2), (3,3),(4,4),]
repeat_num=1


for repeat in range(repeat_num):
    repeat += 1
    for dist in dist_list:
        for mean_demand in mean_list:
            for prompt_type in prompt_type_list:
                for background_info in background_info_list:
                    for background_type in background_type_list:
                        for data_sep in data_sep_list:
                            for cal_cost in cal_cost_list:
                                for external_opt in external_opt_list:
                                    for k1k2 in k1k2_list:
                                        K1, K2 = k1k2
                                        command = (
                                            f"E:\\Anaconda3\\envs\\EoH\\python runEoH3.py "  # change this line according to the path of python.exe
                                            f"--dist {dist} "
                                            f"--mean {mean_demand} "
                                            f"--prompt_type {prompt_type} "
                                            f"--background_info {background_info} "
                                            f"--background_type {background_type} "
                                            f"--data_sep {data_sep} "
                                            f"--cal_cost {cal_cost} "
                                            f"--external_opt {external_opt} "
                                            f"--K1 {K1} "
                                            f"--K2 {K2} "
                                            f"--repeat {repeat} "
                                            f"--filename res_exactdata "
                                        )
                                        print(f"Running: {command}")
                                        try:
                                            subprocess.run(command, shell=True, check=True)
                                        except subprocess.CalledProcessError as e:
                                            print(f"Command failed: {command}")
                                            print(f"Error: {e}")
