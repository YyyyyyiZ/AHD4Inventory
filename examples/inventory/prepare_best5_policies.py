import os
import json
import shutil
from pathlib import Path

def main():
    # Directories
    source_dir = Path('/home/yfenghua/research/AHD4Inventory/examples/inventory/best_policies_by_dataset')
    dest_dir = Path('/home/yfenghua/research/AHD4Inventory/examples/inventory/evaluation/best5/pops_best')

    # Clear existing policy files in dest (but keep extracted folder)
    if dest_dir.exists():
        for f in dest_dir.glob('*.json'):
            f.unlink()
            print(f"Removed old file: {f.name}")

    dest_dir.mkdir(parents=True, exist_ok=True)

    # Get all dataset folders
    dataset_folders = [f for f in os.listdir(source_dir)
                      if os.path.isdir(source_dir / f)]

    print("="*80)
    print("Copying top 3 policies from each dataset to best5/pops_best")
    print("="*80)

    total_copied = 0

    for dataset_name in sorted(dataset_folders):
        dataset_dir = source_dir / dataset_name

        print(f"\nDataset: {dataset_name}")

        # Get all rank_*.json files
        rank_files = sorted(dataset_dir.glob('rank_*.json'))

        if not rank_files:
            print(f"  Warning: No ranked policies found!")
            continue

        # Copy each ranked policy
        for rank_file in rank_files[:3]:  # Only top 3
            # Read the policy
            with open(rank_file, 'r') as f:
                policy_data = json.load(f)

            # Extract rank and objective from filename or data
            if 'rank' in policy_data:
                rank = policy_data['rank']
            else:
                # Parse from filename: rank_1_objective_5993.13.json
                import re
                match = re.search(r'rank_(\d+)', rank_file.name)
                rank = int(match.group(1)) if match else 0

            if 'objective' in policy_data:
                objective = policy_data['objective']
            else:
                match = re.search(r'objective_([\d.]+)', rank_file.name)
                objective = float(match.group(1)) if match else 0.0

            # Get the actual policy
            if 'policy' in policy_data:
                # Wrapped format - extract the inner policy
                actual_policy = policy_data['policy']
            else:
                # Already in policy format
                actual_policy = policy_data

            # Create new filename: {dataset}_{rank}.json
            # Use simplified dataset name (remove _50 suffix if present)
            dataset_short = dataset_name.replace('_50', '')
            new_filename = f"{dataset_short}_rank{rank}.json"
            dest_path = dest_dir / new_filename

            # Save the policy (just the policy, not the wrapper)
            with open(dest_path, 'w') as f:
                json.dump(actual_policy, f, indent=2)

            print(f"  Rank {rank} (obj={objective:.2f}) -> {new_filename}")
            total_copied += 1

    print(f"\n{'='*80}")
    print(f"Total policies copied: {total_copied}")
    print(f"Destination: {dest_dir}")
    print(f"{'='*80}")

    # List all files in destination
    print(f"\nFiles in {dest_dir.name}:")
    for f in sorted(dest_dir.glob('*.json')):
        print(f"  - {f.name}")

if __name__ == '__main__':
    main()
