#!/usr/bin/env python3
"""
Quick test to verify demand statistics are correctly excluding lead time periods
"""

import sys
sys.path.insert(0, '/home/yfenghua/research/AHD4Inventory/eoh/src')

from eoh.problems.optimization.inventory.run import INVENTORY
from eoh.problems.optimization.inventory.analyzeAgent import InventoryAnalyzer

# Test with one of the existing datasets
dist = 'normal_std30_L6_c1_2'

print("="*70)
print("TESTING DEMAND STATISTICS CALCULATION")
print("="*70)
print(f"\nDataset: {dist}")

# Create problem instance
prob = INVENTORY(
    dist=dist,
    n_horizon=50,
    order_option='order_before_sell'
)

# Load a few training instances to inspect
instances = prob.load_instances(mode='train', n_traj=3)

print(f"\nLoaded {len(instances)} training trajectories")
print("\n" + "="*70)
print("INSPECTING RAW DATA STRUCTURE")
print("="*70)

for idx, inst in enumerate(instances[:3], start=1):
    lead_time = inst.get('lead_time', 0)
    demand = inst.get('demand', [])

    print(f"\nTrajectory {idx}:")
    print(f"  Lead time (L): {lead_time}")
    print(f"  Total demand array length: {len(demand)}")
    print(f"  First {lead_time} values (should be zeros): {demand[:lead_time]}")
    print(f"  Actual demand values (first 10): {demand[lead_time:lead_time+10]}")

    # Manual statistics on actual demand (excluding lead time)
    actual_demand = demand[lead_time:]
    if actual_demand:
        mean = sum(actual_demand) / len(actual_demand)
        print(f"  Manual calc - Actual demand mean (excluding lead time): {mean:.3f}")
        print(f"  Manual calc - Actual demand length: {len(actual_demand)}")

print("\n" + "="*70)
print("TESTING get_demand_stats() METHOD")
print("="*70)

# Create analyzer and get demand stats
analyzer = InventoryAnalyzer(prob=prob, n_train=10)

print("\nRunning analyzer.get_demand_stats() with 10 training trajectories...")
print("(This should now EXCLUDE lead time periods)\n")

stats_output = analyzer.get_demand_stats()

print("\n" + "="*70)
print("VERIFICATION")
print("="*70)

# Manual verification - collect all actual demand values (excluding lead time)
instances_full = prob.load_instances(mode='train', n_traj=10)
all_actual_demand = []
total_with_zeros = 0
total_without_zeros = 0

for inst in instances_full:
    lead_time = inst.get('lead_time', 0)
    demand = inst.get('demand', [])

    # Count observations
    total_with_zeros += len(demand)
    actual_demand = demand[lead_time:]
    total_without_zeros += len(actual_demand)

    # Collect actual demand values
    for v in actual_demand:
        try:
            all_actual_demand.append(float(v))
        except:
            pass

manual_mean = sum(all_actual_demand) / len(all_actual_demand)
manual_var = sum((x - manual_mean)**2 for x in all_actual_demand) / len(all_actual_demand)
manual_std = manual_var ** 0.5

print(f"\nManual verification (10 trajectories):")
print(f"  Total observations WITH lead time zeros: {total_with_zeros}")
print(f"  Total observations WITHOUT lead time zeros: {total_without_zeros}")
print(f"  Observations removed: {total_with_zeros - total_without_zeros}")
print(f"\nManual calculated stats (excluding lead time):")
print(f"  Mean: {manual_mean:.6f}")
print(f"  Std:  {manual_std:.6f}")
print(f"  Min:  {min(all_actual_demand):.6f}")
print(f"  Max:  {max(all_actual_demand):.6f}")

print("\n" + "="*70)
print("TEST COMPLETE")
print("="*70)
print("\nThe stats from get_demand_stats() above should match the manual calculation.")
print("If they differ significantly, there's still an issue with the implementation.")
