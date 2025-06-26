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


dist_list = ['poisson']
mean_list = [8000]
prompt_type_list = ['old20']
background_info_list = ['data_sep']
external_opt_list =['scipy']
# k1k2_list=[(0,0),(0,1),(0,2), (0,3),(0,4),
#            (1,0),(2,0), (3,0),(4,0),
#            (1,1),(2,2), (3,3),(4,4),]
k1k2_list=[(0,1)]
repeat_num=1

# dist_list = ['poisson']
# mean_list = [8000]
# prompt_type_list = ['original']
# background_info_list = ['no']
# external_opt_list =['no','scipy']
# # k1k2_list=[(0,0),(0,1),(0,2), (0,3),(0,4)]
# k1k2_list=[(0,0),(0,1),(0,2), (0,3),(0,4),
#            (1,0),(2,0), (3,0),(4,0),
#            (1,1),(2,2), (3,3),(4,4),]
# repeat_num=2

for repeat in range(repeat_num):
    repeat += 5
    for dist in dist_list:
        for mean_demand in mean_list:
                for prompt_type in prompt_type_list:
                    for background_info in background_info_list:
                        for external_opt in external_opt_list:
                            for k1k2 in k1k2_list:
                                K1, K2 = k1k2
                                command = (
                                    f"E:\\Anaconda3\\envs\\EoH\\python runEoH.py "  # change this line according to the path of python.exe
                                    f"--dist {dist} "
                                    f"--mean {mean_demand} "
                                    f"--prompt_type {prompt_type} "
                                    f"--background_info {background_info} "
                                    f"--external_opt {external_opt} "
                                    f"--K1 {K1} "
                                    f"--K2 {K2} "
                                    f"--repeat {repeat} "
                                    f"--filename res_data_prompt "
                                )
                                print(f"Running: {command}")
                                try:
                                    subprocess.run(command, shell=True, check=True)
                                except subprocess.CalledProcessError as e:
                                    print(f"Command failed: {command}")
                                    print(f"Error: {e}")
