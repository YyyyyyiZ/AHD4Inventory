import subprocess
import sys

print(sys.executable)  # path of python.exe

# 需要运行的配置
config = {
    'cfg_1': {
        'dist': 'normal',
        'mean': 70,
        'prompt_type': 'original',
        'background_info': 'no',
        'external_opt': 'no',
        'K1': 0,
        'K2': 0,
    },
    'cfg_2': {
        'dist': 'normal',
        'mean': 70,
        'prompt_type': 'original',
        'background_info': 'all',
        'external_opt': 'scipy',
        'K1': 0,
        'K2': 1,
    },
    'cfg_3': {
        'dist': 'normal',
        'mean': 70,
        'prompt_type': 'original',
        'background_info': 'avg',
        'external_opt': 'scipy',
        'K1': 1,
        'K2': 0,
    },
    'cfg_4': {
        'dist': 'normal',
        'mean': 70,
        'prompt_type': 'original',
        'background_info': 'avg',
        'external_opt': 'scipy',
        'K1': 0,
        'K2': 1,
    },
'cfg_5': {
        'dist': 'normal',
        'mean': 70,
        'prompt_type': 'original',
        'background_info': 'quantile',
        'external_opt': 'scipy',
        'K1': 1,
        'K2': 0,
    },
    'cfg_6': {
        'dist': 'normal',
        'mean': 70,
        'prompt_type': 'original',
        'background_info': 'quantile',
        'external_opt': 'scipy',
        'K1': 2,
        'K2': 0,
    },
    'cfg_7': {
        'dist': 'normal',
        'mean': 70,
        'prompt_type': 'original',
        'background_info': 'quantile',
        'external_opt': 'scipy',
        'K1': 0,
        'K2': 0,
    },
'cfg_8': {
        'dist': 'poisson',
        'mean': 80,
        'prompt_type': 'original',
        'background_info': 'no',
        'external_opt': 'no',
        'K1': 0,
        'K2': 0,
    },
'cfg_9': {
        'dist': 'poisson',
        'mean': 80,
        'prompt_type': 'original',
        'background_info': 'quantile',
        'external_opt': 'scipy',
        'K1': 1,
        'K2': 0,
    },
    'cfg_10': {
        'dist': 'poisson',
        'mean': 80,
        'prompt_type': 'original',
        'background_info': 'quantile',
        'external_opt': 'scipy',
        'K1': 2,
        'K2': 0,
    },
    'cfg_11': {
        'dist': 'poisson',
        'mean': 80,
        'prompt_type': 'original',
        'background_info': 'quantile',
        'external_opt': 'scipy',
        'K1': 0,
        'K2': 0,
    },
'cfg_12': {
        'dist': 'poisson',
        'mean': 80,
        'prompt_type': 'original',
        'background_info': 'avg',
        'external_opt': 'scipy',
        'K1': 1,
        'K2': 0,
    },
    'cfg_13': {
        'dist': 'poisson',
        'mean': 80,
        'prompt_type': 'original',
        'background_info': 'avg',
        'external_opt': 'scipy',
        'K1': 0,
        'K2': 1,
    },
}


for cfg_name, cfg in config.items():
    command = (
        f"{sys.executable} runEoH.py "  # 使用当前Python解释器
        f"--dist {cfg['dist']} "
        f"--mean {cfg['mean']} "
        f"--prompt_type {cfg['prompt_type']} "
        f"--background_info {cfg['background_info']} "
        f"--external_opt {cfg['external_opt']} "
        f"--K1 {cfg['K1']} "
        f"--K2 {cfg['K2']} "
    )
    print(f"\nRunning config {cfg_name}: {command}")
    try:
        subprocess.run(command, shell=True, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Command failed: {command}")
        print(f"Error: {e}")