import os
import json
import shutil
from pathlib import Path

def main():
    # Base directory
    base_dir = Path('/home/yfenghua/research/AHD4Inventory/examples/inventory/best_policies_by_dataset')

    # Map of new policy files to their dataset folders
    policy_files = {
        'exponential_L6_c1_2.json': 'exponential_L6_c1_2_50',
        'normal_std10_L6_c1_2.json': 'normal_std10_L6_c1_2_50',
        'normal_std30_L6_c1_2.json': 'normal_std30_L6_c1_2_50',
        'normal_std50_L6_c1_2.json': 'normal_std50_L6_c1_2_50',
        'poisson_L6_c1_2.json': 'poisson_L6_c1_2_50'
    }

    print("="*80)
    print("Step 1: Moving new policies to dataset folders")
    print("="*80)

    # Move each policy file to its corresponding dataset folder
    for policy_file, dataset_folder in policy_files.items():
        source_path = base_dir / policy_file
        dest_folder = base_dir / dataset_folder

        if not source_path.exists():
            print(f"Warning: {policy_file} not found!")
            continue

        if not dest_folder.exists():
            print(f"Warning: Dataset folder {dataset_folder} not found!")
            continue

        # Read the policy to get its objective
        with open(source_path, 'r') as f:
            policy_data = json.load(f)

        objective = policy_data.get('objective', 'unknown')

        # Create a temporary filename in the dataset folder
        temp_filename = f"new_policy_{objective}.json"
        dest_path = dest_folder / temp_filename

        # Move the file
        shutil.move(str(source_path), str(dest_path))
        print(f"Moved {policy_file} (obj={objective}) -> {dataset_folder}/{temp_filename}")

    print("\n" + "="*80)
    print("Step 2: Re-ranking policies in each dataset folder")
    print("="*80)

    # Get all dataset folders
    dataset_folders = [f for f in os.listdir(base_dir)
                      if os.path.isdir(base_dir / f)]

    new_summary = {}

    for dataset_name in sorted(dataset_folders):
        dataset_dir = base_dir / dataset_name

        print(f"\nProcessing: {dataset_name}")

        # Get all JSON files (except summary.json)
        json_files = [f for f in os.listdir(dataset_dir)
                     if f.endswith('.json') and f != 'summary.json']

        print(f"  Found {len(json_files)} policy files")

        # Extract objectives for all policies
        policies = []
        for json_file in json_files:
            file_path = dataset_dir / json_file

            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)

                # Check if it's a wrapped policy or direct policy
                if 'policy' in data and 'objective' in data:
                    objective = data['objective']
                elif 'objective' in data:
                    objective = data['objective']
                else:
                    print(f"  Warning: No objective in {json_file}")
                    continue

                policies.append({
                    'filename': json_file,
                    'filepath': file_path,
                    'objective': objective,
                    'data': data
                })

            except Exception as e:
                print(f"  Error reading {json_file}: {e}")
                continue

        if not policies:
            print(f"  Warning: No valid policies found!")
            continue

        # Sort by objective (lower is better)
        policies.sort(key=lambda x: x['objective'])

        print(f"  Objectives range: {policies[0]['objective']:.2f} to {policies[-1]['objective']:.2f}")

        # Keep top 3, remove the rest
        top_3 = policies[:3]
        to_remove = policies[3:]

        # Remove files that are not in top 3
        for policy in to_remove:
            os.remove(policy['filepath'])
            print(f"  Removed: {policy['filename']} (objective={policy['objective']:.2f})")

        # Rename/save top 3 to standardized format
        top_3_info = []
        for i, policy in enumerate(top_3, 1):
            new_filename = f"rank_{i}_objective_{policy['objective']:.2f}.json"
            new_path = dataset_dir / new_filename

            # Remove old file if it exists with different content
            if new_path.exists():
                os.remove(new_path)

            # Save with proper metadata
            policy_to_save = policy['data']

            # Add metadata if not already wrapped
            if 'rank' not in policy_to_save:
                wrapped_policy = {
                    'rank': i,
                    'objective': policy['objective'],
                    'source_folder': policy_to_save.get('source_folder', 'external'),
                    'policy': policy_to_save
                }
                with open(new_path, 'w') as f:
                    json.dump(wrapped_policy, f, indent=2)
            else:
                # Already has metadata, just update rank
                policy_to_save['rank'] = i
                with open(new_path, 'w') as f:
                    json.dump(policy_to_save, f, indent=2)

            # Remove old file if different
            if policy['filepath'] != new_path:
                if policy['filepath'].exists():
                    os.remove(policy['filepath'])

            print(f"  Rank {i}: {policy['objective']:.2f} -> {new_filename}")

            # Extract source information
            source_folder = policy['data'].get('source_folder', 'external')

            top_3_info.append({
                'rank': i,
                'objective': policy['objective'],
                'source_folder': source_folder,
                'saved_as': f"{dataset_name}/{new_filename}"
            })

        # Update summary for this dataset
        new_summary[dataset_name] = {
            'total_policies': len(policies),
            'top_3': top_3_info
        }

    # Save updated summary
    summary_file = base_dir / 'summary.json'
    with open(summary_file, 'w') as f:
        json.dump(new_summary, f, indent=2)

    print(f"\n{'='*80}")
    print(f"Integration complete!")
    print(f"Updated summary saved to: {summary_file}")
    print(f"Total datasets processed: {len(new_summary)}")
    print(f"{'='*80}")

if __name__ == '__main__':
    main()
