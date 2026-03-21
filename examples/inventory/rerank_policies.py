import os
import json
import shutil
from pathlib import Path

def extract_objective_from_file(file_path):
    """Extract objective value from a policy JSON file."""
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)

        # Check if it's a wrapped policy (with metadata) or direct policy
        if 'policy' in data and 'objective' in data:
            # Wrapped format from our previous extraction
            return data['objective']
        elif 'objective' in data:
            # Direct policy format
            return data['objective']
        else:
            print(f"Warning: No objective found in {file_path}")
            return None
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return None

def main():
    # Base directory
    base_dir = Path('/home/yfenghua/research/AHD4Inventory/examples/inventory/best_policies_by_dataset')

    if not base_dir.exists():
        print(f"Error: Directory {base_dir} does not exist!")
        return

    # Get all dataset folders
    dataset_folders = [f for f in os.listdir(base_dir)
                      if os.path.isdir(base_dir / f)]

    print(f"Found {len(dataset_folders)} dataset folders to process...")
    print("="*80)

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
            objective = extract_objective_from_file(file_path)

            if objective is not None:
                policies.append({
                    'filename': json_file,
                    'filepath': file_path,
                    'objective': objective
                })

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

        # Rename top 3 to standardized format
        top_3_info = []
        for i, policy in enumerate(top_3, 1):
            old_path = policy['filepath']
            new_filename = f"rank_{i}_objective_{policy['objective']:.2f}.json"
            new_path = dataset_dir / new_filename

            # Only rename if the name is different
            if old_path.name != new_filename:
                # If target already exists and is different, remove it first
                if new_path.exists() and new_path != old_path:
                    os.remove(new_path)
                os.rename(old_path, new_path)
                print(f"  Rank {i}: {policy['objective']:.2f} (renamed to {new_filename})")
            else:
                print(f"  Rank {i}: {policy['objective']:.2f} (kept as {new_filename})")

            # Read the full policy data for summary
            with open(new_path, 'r') as f:
                policy_data = json.load(f)

            # Extract source information if available
            source_folder = policy_data.get('source_folder', 'unknown')

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
    print(f"Re-ranking complete!")
    print(f"Updated summary saved to: {summary_file}")
    print(f"Total datasets processed: {len(new_summary)}")
    print(f"{'='*80}")

if __name__ == '__main__':
    main()
