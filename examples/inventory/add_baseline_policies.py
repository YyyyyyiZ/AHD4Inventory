"""
Add baseline policies from initial_pool.json to the evaluation
"""
import json
from pathlib import Path

def main():
    # Read the initial_pool.json
    initial_pool_path = Path('/home/yfenghua/research/AHD4Inventory/examples/inventory/initial_pool.json')

    with open(initial_pool_path, 'r') as f:
        policies = json.load(f)

    # Destination folder
    dest_dir = Path('/home/yfenghua/research/AHD4Inventory/examples/inventory/evaluation/best5/pops_best')

    # Policy names
    policy_names = [
        'baseline_base_stock',
        'baseline_constant_order',
        'baseline_capped_base_stock'
    ]

    print("="*80)
    print("Adding baseline policies to evaluation")
    print("="*80)

    for i, (policy_data, policy_name) in enumerate(zip(policies, policy_names)):
        # Create individual JSON file
        output_path = dest_dir / f"{policy_name}.json"

        with open(output_path, 'w') as f:
            json.dump(policy_data, f, indent=2)

        print(f"Created: {policy_name}.json")

    print(f"\n{'='*80}")
    print(f"Successfully added {len(policy_names)} baseline policies")
    print(f"Next step: Run extract_code.py and then evaluate_focused.py")
    print(f"{'='*80}")

if __name__ == '__main__':
    main()
