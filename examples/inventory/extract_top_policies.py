import os
import json
import re
from pathlib import Path
from collections import defaultdict
import shutil

def extract_dataset_name(folder_name):
    """
    Extract dataset name from folder pattern.
    Pattern: deepseek-chat_{DATASET}_{method}_{run}
    Example: deepseek-chat_exponential_L2_c1_2_50_plain_processed_scipy_15_default_e1-e2-m2_2_r2
    Dataset: exponential_L2_c1_2_50
    """
    # Remove 'deepseek-chat_' prefix
    if not folder_name.startswith('deepseek-chat_'):
        return None

    rest = folder_name[len('deepseek-chat_'):]

    # Common patterns: ends with _plain_processed... or similar
    # Extract everything before _plain_processed or _no_ or other method identifiers
    patterns = [
        r'^(.+?)_plain_processed',
        r'^(.+?)_no_',
    ]

    for pattern in patterns:
        match = re.match(pattern, rest)
        if match:
            return match.group(1)

    # If no pattern matches, try to extract based on common suffixes
    # Look for pattern: {distribution}_{params}_r\d+
    match = re.match(r'^(.+?)_r\d+$', rest)
    if match:
        candidate = match.group(1)
        # Remove method suffix if present
        # Common method patterns: _scipy_15_default_*, _default_*, etc.
        method_match = re.match(r'^(.+?)_(?:scipy|no)_\d+_default', candidate)
        if method_match:
            return method_match.group(1)

    return None

def find_last_generation_file(pops_best_dir):
    """Find the last generation file in pops_best directory."""
    if not os.path.exists(pops_best_dir):
        return None

    generation_files = []
    for filename in os.listdir(pops_best_dir):
        if filename.startswith('population_generation_') and filename.endswith('.json'):
            # Extract generation number
            match = re.match(r'population_generation_(\d+)\.json', filename)
            if match:
                gen_num = int(match.group(1))
                generation_files.append((gen_num, filename))

    if not generation_files:
        return None

    # Return the file with the highest generation number
    generation_files.sort(reverse=True)
    return generation_files[0][1]

def extract_best_policy(json_file_path):
    """Extract the best policy from a JSON file."""
    try:
        with open(json_file_path, 'r') as f:
            data = json.load(f)

        # Check if data is a list or a single policy
        if isinstance(data, list):
            # Multiple policies - find the one with lowest objective
            best_policy = min(data, key=lambda x: x.get('objective', float('inf')))
            return best_policy
        elif isinstance(data, dict):
            # Single policy
            return data
        else:
            print(f"Warning: Unexpected data format in {json_file_path}")
            return None
    except Exception as e:
        print(f"Error reading {json_file_path}: {e}")
        return None

def main():
    # Base directory
    base_dir = Path('/home/yfenghua/research/AHD4Inventory/examples/inventory')

    # Dictionary to store policies grouped by dataset
    # Structure: {dataset_name: [(objective, policy_data, source_folder), ...]}
    dataset_policies = defaultdict(list)

    # Scan all folders starting with 'deepseek-chat'
    folders = [f for f in os.listdir(base_dir) if f.startswith('deepseek-chat_') and os.path.isdir(base_dir / f)]

    print(f"Found {len(folders)} folders to process...")

    processed_count = 0
    skipped_count = 0

    for folder in folders:
        folder_path = base_dir / folder

        # Extract dataset name
        dataset_name = extract_dataset_name(folder)
        if not dataset_name:
            print(f"Warning: Could not extract dataset name from {folder}")
            skipped_count += 1
            continue

        # Find pops_best directory
        pops_best_dir = folder_path / 'pops_best'
        if not os.path.exists(pops_best_dir):
            print(f"Warning: No pops_best directory in {folder}")
            skipped_count += 1
            continue

        # Find last generation file
        last_gen_file = find_last_generation_file(pops_best_dir)
        if not last_gen_file:
            print(f"Warning: No generation file found in {folder}/pops_best")
            skipped_count += 1
            continue

        # Read and extract best policy
        json_file_path = pops_best_dir / last_gen_file
        policy = extract_best_policy(json_file_path)

        if policy is None:
            print(f"Warning: Could not extract policy from {folder}/{last_gen_file}")
            skipped_count += 1
            continue

        # Get objective value
        objective = policy.get('objective')
        if objective is None:
            print(f"Warning: No objective value in {folder}/{last_gen_file}")
            skipped_count += 1
            continue

        # Store policy data
        dataset_policies[dataset_name].append({
            'objective': objective,
            'policy': policy,
            'source_folder': folder,
            'source_file': str(json_file_path.relative_to(base_dir))
        })

        processed_count += 1
        if processed_count % 10 == 0:
            print(f"Processed {processed_count} folders...")

    print(f"\nProcessing complete!")
    print(f"Successfully processed: {processed_count}")
    print(f"Skipped: {skipped_count}")
    print(f"Unique datasets found: {len(dataset_policies)}")

    # Select top 3 policies for each dataset
    output_dir = base_dir / 'best_policies_by_dataset'
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir()

    summary = {}

    for dataset_name, policies in dataset_policies.items():
        print(f"\nDataset: {dataset_name}")
        print(f"  Total policies: {len(policies)}")

        # Sort by objective (lower is better)
        policies.sort(key=lambda x: x['objective'])

        # Take top 3
        top_3 = policies[:3]

        # Create dataset folder
        dataset_dir = output_dir / dataset_name
        dataset_dir.mkdir()

        # Save top 3 policies
        summary[dataset_name] = {
            'total_policies': len(policies),
            'top_3': []
        }

        for i, policy_data in enumerate(top_3, 1):
            # Save policy JSON
            output_file = dataset_dir / f'rank_{i}_objective_{policy_data["objective"]:.2f}.json'

            # Add metadata to policy
            policy_with_metadata = {
                'rank': i,
                'objective': policy_data['objective'],
                'source_folder': policy_data['source_folder'],
                'source_file': policy_data['source_file'],
                'policy': policy_data['policy']
            }

            with open(output_file, 'w') as f:
                json.dump(policy_with_metadata, f, indent=2)

            summary[dataset_name]['top_3'].append({
                'rank': i,
                'objective': policy_data['objective'],
                'source_folder': policy_data['source_folder'],
                'saved_as': str(output_file.relative_to(output_dir))
            })

            print(f"  Rank {i}: Objective={policy_data['objective']:.2f} from {policy_data['source_folder']}")

    # Save summary
    summary_file = output_dir / 'summary.json'
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2)

    print(f"\n{'='*80}")
    print(f"Results saved to: {output_dir}")
    print(f"Summary file: {summary_file}")
    print(f"Total datasets processed: {len(summary)}")
    print(f"{'='*80}")

if __name__ == '__main__':
    main()
