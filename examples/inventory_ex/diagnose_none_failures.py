#!/usr/bin/env python3
"""
Diagnostic script to analyze None values in optimization results
"""
import json
import pandas as pd
from pathlib import Path
from collections import defaultdict

def analyze_population_files(base_dir):
    """Analyze all population JSON files to find patterns in None values"""

    base_path = Path(base_dir)
    results = {
        'total_populations': 0,
        'populations_with_none': 0,
        'total_individuals': 0,
        'none_individuals': 0,
        'none_by_generation': defaultdict(int),
        'none_examples': []
    }

    # Find all population JSON files
    pop_files = list(base_path.glob("**/pops/population_generation_*.json"))

    print(f"Found {len(pop_files)} population files")
    print("=" * 80)

    for pop_file in sorted(pop_files):
        try:
            with open(pop_file, 'r') as f:
                population = json.load(f)

            # Extract generation number from filename
            gen_num = pop_file.stem.split('_')[-1]

            results['total_populations'] += 1
            has_none = False

            # Check if population is a list or single dict
            if isinstance(population, list):
                results['total_individuals'] += len(population)

                for i, individual in enumerate(population):
                    if individual.get('objective') is None:
                        has_none = True
                        results['none_individuals'] += 1
                        results['none_by_generation'][gen_num] += 1

                        # Store example for detailed inspection
                        if len(results['none_examples']) < 5:
                            results['none_examples'].append({
                                'file': str(pop_file),
                                'generation': gen_num,
                                'individual_index': i,
                                'has_code': individual.get('code') is not None,
                                'has_algorithm': individual.get('algorithm') is not None,
                                'opt_params': individual.get('opt_params', {})
                            })
            else:
                # Single individual file
                results['total_individuals'] += 1
                if population.get('objective') is None:
                    has_none = True
                    results['none_individuals'] += 1
                    results['none_by_generation'][gen_num] += 1

            if has_none:
                results['populations_with_none'] += 1

        except Exception as e:
            print(f"Error reading {pop_file}: {e}")

    return results

def analyze_csv_results(csv_path):
    """Analyze the results CSV to find None patterns"""

    try:
        df = pd.read_csv(csv_path)

        print("\n" + "=" * 80)
        print(f"Analyzing CSV: {csv_path}")
        print("=" * 80)

        # Find columns with repeat data
        repeat_cols = [col for col in df.columns if col.startswith('repeat_')]

        if not repeat_cols:
            print("No repeat columns found")
            return

        # Count None values
        for col in repeat_cols:
            none_count = df[col].isna().sum()
            total_count = len(df)
            none_pct = (none_count / total_count * 100) if total_count > 0 else 0

            print(f"{col}: {none_count}/{total_count} None values ({none_pct:.1f}%)")

        # Look for patterns in None values
        print("\n" + "-" * 80)
        print("Configurations with most None values:")
        print("-" * 80)

        # Group by configuration parameters
        config_cols = ['LLM', 'external_opt', 'iter_opt', 'n_pop', 'mode']
        available_config_cols = [col for col in config_cols if col in df.columns]

        if available_config_cols:
            for col in repeat_cols:
                none_mask = df[col].isna()
                if none_mask.any():
                    print(f"\n{col} - Configurations with None:")
                    print(df[none_mask][available_config_cols])

    except Exception as e:
        print(f"Error analyzing CSV: {e}")

def main():
    base_dir = Path(__file__).parent

    print("=" * 80)
    print("DIAGNOSTIC ANALYSIS: None Values in Optimization Results")
    print("=" * 80)

    # Analyze population JSON files
    print("\n1. Analyzing population JSON files...")
    results = analyze_population_files(base_dir)

    print("\n" + "=" * 80)
    print("SUMMARY OF POPULATION FILES")
    print("=" * 80)
    print(f"Total populations analyzed: {results['total_populations']}")
    print(f"Populations with None values: {results['populations_with_none']}")
    print(f"Total individuals: {results['total_individuals']}")
    print(f"Individuals with None objective: {results['none_individuals']}")

    if results['none_individuals'] > 0:
        none_pct = (results['none_individuals'] / results['total_individuals'] * 100)
        print(f"None percentage: {none_pct:.1f}%")

    if results['none_by_generation']:
        print("\nNone values by generation:")
        for gen in sorted(results['none_by_generation'].keys(), key=lambda x: int(x) if x.isdigit() else 0):
            print(f"  Generation {gen}: {results['none_by_generation'][gen]} None values")

    if results['none_examples']:
        print("\nExample failures:")
        for i, example in enumerate(results['none_examples'], 1):
            print(f"\nExample {i}:")
            print(f"  File: {example['file']}")
            print(f"  Generation: {example['generation']}")
            print(f"  Has code: {example['has_code']}")
            print(f"  Has algorithm: {example['has_algorithm']}")
            print(f"  Opt params: {example['opt_params']}")

    # Analyze CSV files
    print("\n2. Analyzing CSV results...")
    csv_files = list(base_dir.glob("res*.csv"))
    for csv_file in csv_files:
        if not csv_file.name.endswith('_reasoning.csv'):
            analyze_csv_results(csv_file)

    print("\n" + "=" * 80)
    print("RECOMMENDATIONS:")
    print("=" * 80)
    if results['none_individuals'] > 0:
        print("- Run your code again with the enhanced error logging")
        print("- Check the console output for detailed error messages")
        print("- Look for patterns in which generations fail")
        print("- Check if timeout is too short (current default: 2 minutes)")
    else:
        print("- No None values found in population files!")
        print("- Check if the issue is only in CSV results")

if __name__ == "__main__":
    main()
