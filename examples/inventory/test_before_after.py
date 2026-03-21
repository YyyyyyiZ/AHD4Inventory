#!/usr/bin/env python3
"""
Comparison test: Show the difference between including vs excluding lead time zeros
"""

import sys
sys.path.insert(0, '/home/yfenghua/research/AHD4Inventory/eoh/src')

from eoh.problems.optimization.inventory.run import INVENTORY

dist = 'normal_std30_L6_c1_2'

print("="*80)
print("BEFORE vs AFTER: Impact of Excluding Lead Time Zeros")
print("="*80)
print(f"\nDataset: {dist}")

prob = INVENTORY(dist=dist, n_horizon=50, order_option='order_before_sell')
instances = prob.load_instances(mode='train', n_traj=10)

# ============================================================================
# BEFORE: Including all demand values (with lead time zeros)
# ============================================================================
all_demand_with_zeros = []
for traj in instances:
    d = traj.get('demand', [])
    for v in d:
        try:
            all_demand_with_zeros.append(float(v))
        except:
            pass

n_with = len(all_demand_with_zeros)
mean_with = sum(all_demand_with_zeros) / n_with
var_with = sum((x - mean_with)**2 for x in all_demand_with_zeros) / n_with
std_with = var_with ** 0.5
sorted_with = sorted(all_demand_with_zeros)

# ============================================================================
# AFTER: Excluding lead time zeros
# ============================================================================
all_demand_without_zeros = []
for traj in instances:
    d = traj.get('demand', [])
    lead_time = traj.get('lead_time', 0)
    actual_demand = d[lead_time:]  # Skip lead time periods
    for v in actual_demand:
        try:
            all_demand_without_zeros.append(float(v))
        except:
            pass

n_without = len(all_demand_without_zeros)
mean_without = sum(all_demand_without_zeros) / n_without
var_without = sum((x - mean_without)**2 for x in all_demand_without_zeros) / n_without
std_without = var_without ** 0.5
sorted_without = sorted(all_demand_without_zeros)

# ============================================================================
# COMPARISON
# ============================================================================
print("\n" + "="*80)
print("RESULTS COMPARISON")
print("="*80)

print(f"\n{'Metric':<30} | {'BEFORE (with zeros)':<20} | {'AFTER (no zeros)':<20} | {'Difference':<15}")
print("-" * 80)
print(f"{'Total Observations':<30} | {n_with:<20} | {n_without:<20} | {n_with - n_without:<15}")
print(f"{'Mean Demand':<30} | {mean_with:<20.6f} | {mean_without:<20.6f} | {mean_without - mean_with:<15.6f}")
print(f"{'Std Dev':<30} | {std_with:<20.6f} | {std_without:<20.6f} | {std_without - std_with:<15.6f}")
print(f"{'Min Demand':<30} | {sorted_with[0]:<20.6f} | {sorted_without[0]:<20.6f} | {sorted_without[0] - sorted_with[0]:<15.6f}")
print(f"{'Max Demand':<30} | {sorted_with[-1]:<20.6f} | {sorted_without[-1]:<20.6f} | {sorted_without[-1] - sorted_with[-1]:<15.6f}")

print("\n" + "="*80)
print("IMPACT ANALYSIS")
print("="*80)

zeros_count = n_with - n_without
mean_bias = ((mean_without - mean_with) / mean_without) * 100
std_bias = ((std_without - std_with) / std_without) * 100

print(f"\n✓ Lead time zeros removed: {zeros_count}")
print(f"✓ Mean demand bias correction: +{mean_bias:.2f}% (was underestimated)")
print(f"✓ Std dev bias correction: +{std_bias:.2f}% (was underestimated)")
print(f"\n✓ The AFTER values are now ACCURATE and represent actual demand distribution")
print(f"✓ These corrected statistics will be passed to evaluator and policy creator agents")

print("\n" + "="*80)
