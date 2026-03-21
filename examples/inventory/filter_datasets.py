import os
import json
import shutil
from pathlib import Path

def main():
    # Base directory
    base_dir = Path('/home/yfenghua/research/AHD4Inventory/examples/inventory/best_policies_by_dataset')

    if not base_dir.exists():
        print(f"Error: Directory {base_dir} does not exist!")
        return

    # Filter criteria: L6 and c1_2
    required_patterns = ['L6', 'c1_2']

    # Get all dataset folders
    all_folders = [f for f in os.listdir(base_dir) if os.path.isdir(base_dir / f)]

    # Filter datasets
    kept_datasets = []
    removed_datasets = []

    for folder in all_folders:
        # Check if folder matches the criteria
        if all(pattern in folder for pattern in required_patterns):
            kept_datasets.append(folder)
            print(f"Keeping: {folder}")
        else:
            # Remove the folder
            folder_path = base_dir / folder
            if folder_path.is_dir():
                shutil.rmtree(folder_path)
                removed_datasets.append(folder)
                print(f"Removed: {folder}")

    # Update summary.json to only include kept datasets
    summary_file = base_dir / 'summary.json'
    if summary_file.exists():
        with open(summary_file, 'r') as f:
            full_summary = json.load(f)

        # Filter summary to only include kept datasets
        filtered_summary = {k: v for k, v in full_summary.items() if k in kept_datasets}

        # Save filtered summary
        with open(summary_file, 'w') as f:
            json.dump(filtered_summary, f, indent=2)

        print(f"\nSummary updated with {len(filtered_summary)} datasets")

    print(f"\n{'='*80}")
    print(f"Filtering complete!")
    print(f"Kept datasets: {len(kept_datasets)}")
    print(f"Removed datasets: {len(removed_datasets)}")
    print(f"\nDatasets matching L6 and c1_2:")
    for dataset in sorted(kept_datasets):
        print(f"  - {dataset}")
    print(f"{'='*80}")

if __name__ == '__main__':
    main()
