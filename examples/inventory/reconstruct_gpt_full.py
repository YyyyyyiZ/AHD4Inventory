import json
import os
import glob
import csv
import re

# Get all gpt-5 directories excluding std10 only
base_path = '/home/yfenghua/research/AHD4Inventory/examples/inventory'
dirs = glob.glob(os.path.join(base_path, 'gpt-5-*'))
dirs = [d for d in dirs if 'std10' not in d and os.path.isdir(d)]

print(f"Found {len(dirs)} directories to process")

# Prepare data rows
rows = []

for dir_path in sorted(dirs):
    dir_name = os.path.basename(dir_path)

    # Parse directory name
    match = re.match(r'gpt-5-(nano|mini)_(.+?)_L\d+_c1_\d+_50_plain_processed_(no|scipy)_15_default_m2(plural)?_\d+_r(\d+)', dir_name)

    if not match:
        print(f"Warning: Could not parse directory name: {dir_name}")
        continue

    model = match.group(1)
    dist = match.group(2)
    optimizer = match.group(3)
    repeat = int(match.group(5))

    llm = f"gpt-5-{model}"
    dist_full = f"{dist}_L6_c1_2"

    # Read population files for generations 1-10
    for gen in range(1, 11):
        pop_file = os.path.join(dir_path, 'pops', f'population_generation_{gen}.json')

        if not os.path.exists(pop_file):
            print(f"Warning: Missing {pop_file}")
            continue

        with open(pop_file, 'r') as f:
            population = json.load(f)

        # Find the policy with minimum train objective (best)
        if not population:
            continue

        best_policy = min(population, key=lambda p: p.get('objective', float('inf')))
        train_obj = best_policy.get('objective')
        test_obj = best_policy.get('test_objective')

        if train_obj is None or test_obj is None:
            continue

        # Create train row for this generation
        train_row = {
            'LLM': llm,
            'problem': 'inventory',
            'n_train': 50,
            'p': 4,
            'initialexternal_opt': '',
            'repeat': repeat,
            'n_pop': gen,
            'mode': 'train',
            'algo_performance': 'processed',
            'dist': dist_full,
        }
        # Add generation columns (only column 1 has the value, rest empty)
        for i in range(1, 31):
            if i == 1:
                train_row[str(i)] = f"{train_obj:.2f}" if isinstance(train_obj, (int, float)) else str(train_obj)
            else:
                train_row[str(i)] = ''
        train_row['initial'] = '1.00'
        train_row['external_opt'] = optimizer

        # Create test row for this generation
        test_row = train_row.copy()
        test_row['mode'] = 'test'
        test_row['1'] = f"{test_obj:.2f}" if isinstance(test_obj, (int, float)) else str(test_obj)

        rows.append(train_row)
        rows.append(test_row)

    print(f"Processed: {llm} {dist_full} {optimizer} r{repeat}")

# Sort rows to match original format
rows.sort(key=lambda x: (x['LLM'], x['dist'], x['external_opt'], x['repeat'], x['n_pop'], 0 if x['mode'] == 'train' else 1))

# Write CSV
output_file = os.path.join(base_path, 'gpt.csv')
fieldnames = ['LLM', 'problem', 'n_train', 'p', 'initialexternal_opt', 'repeat', 'n_pop', 'mode', 'algo_performance', 'dist'] + \
             [str(i) for i in range(1, 31)] + ['initial', 'external_opt']

with open(output_file, 'w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)

print(f"\nWrote {len(rows)} rows to {output_file}")
print(f"Total generation-rows: {len(rows)} (each run has 20 rows: 10 generations × 2 modes)")
