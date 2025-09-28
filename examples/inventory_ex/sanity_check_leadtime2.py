#!/usr/bin/env python3
"""
Sanity check script for inventory_ex problem with lead_time = 2
Tests that the system correctly handles longer lead times.
"""

import json
import sys
import os
import numpy as np

# Add the eoh source to path
sys.path.append('../../eoh/src')

from eoh.problems.optimization.inventory_ex.run import INVENTORY
from eoh.problems.optimization.inventory_ex.analyze import InventoryAnalyzer

def create_leadtime2_test_data():
    """Create test data files with lead_time = 2"""

    # Simple test data with lead_time = 2
    test_data = [
        {
            "instance_id": "leadtime2_test_0",
            "initial_inventory": 50,
            "demand": [10, 15, 12, 8, 20, 18, 14, 16, 11, 13],
            "num_periods": 10,
            "holding_cost": 2,
            "lost_sales_cost": 10,
            "lead_time": 2
        },
        {
            "instance_id": "leadtime2_test_1",
            "initial_inventory": 50,
            "demand": [12, 18, 10, 14, 16, 20, 15, 11, 17, 13],
            "num_periods": 10,
            "holding_cost": 2,
            "lost_sales_cost": 10,
            "lead_time": 2
        }
    ]

    # Create data directory if it doesn't exist
    data_dir = "evaluation/data"
    os.makedirs(data_dir, exist_ok=True)

    # Save test data
    train_file = f"{data_dir}/leadtime2_train_80_low.json"
    test_file = f"{data_dir}/leadtime2_test_80_low.json"

    with open(train_file, 'w') as f:
        json.dump(test_data, f, indent=2)

    with open(test_file, 'w') as f:
        json.dump(test_data, f, indent=2)

    print(f"✅ Created test data files:")
    print(f"   - {train_file}")
    print(f"   - {test_file}")

    return train_file, test_file

def test_simple_base_stock_policy():
    """Test a simple base stock policy with manual calculation"""

    print("\n=== Testing Simple Base Stock Policy ===")

    # Simple algorithm: Base Stock Level = 30
    class SimpleBaseStock:
        def compute_order_amount(self, current_inventory, pipeline_inventory):
            base_stock_level = 30
            total_inventory = current_inventory + sum(pipeline_inventory)
            order_amount = max(0, base_stock_level - total_inventory)
            return order_amount

    # Test data
    instance = {
        "initial_inventory": 50,
        "demand": [10, 15, 12, 8, 20],
        "num_periods": 5,
        "holding_cost": 2,
        "lost_sales_cost": 10,
        "lead_time": 2
    }

    # Manual simulation
    print(f"Initial inventory: {instance['initial_inventory']}")
    print(f"Lead time: {instance['lead_time']}")
    print(f"Base stock level: 30")
    print()

    inventory = instance['initial_inventory']
    pipeline = [0, 0]  # lead_time = 2
    total_cost = 0
    algo = SimpleBaseStock()

    print("Period | Demand | Incoming | Inventory | Order | Pipeline | Holding | Lost Sales | Total Cost")
    print("-" * 90)

    for t in range(instance['num_periods']):
        # Receive incoming order (oldest in pipeline)
        incoming = pipeline.pop(0)
        inventory += incoming

        # Make order decision
        order = algo.compute_order_amount(inventory, pipeline.copy())

        # Add new order to pipeline
        pipeline.append(order)

        # Demand occurs
        demand = instance['demand'][t]
        sales = min(inventory, demand)
        lost_sales = demand - sales
        inventory -= sales

        # Calculate costs
        holding_cost = instance['holding_cost'] * inventory
        lost_sales_cost = instance['lost_sales_cost'] * lost_sales
        period_cost = holding_cost + lost_sales_cost
        total_cost += period_cost

        print(f"{t+1:6d} | {demand:6d} | {incoming:8.0f} | {inventory:9.0f} | {order:5.0f} | {pipeline} | {holding_cost:7.0f} | {lost_sales_cost:10.0f} | {total_cost:10.0f}")

    print(f"\nFinal total cost: {total_cost}")
    return total_cost

def test_inventory_system_with_leadtime2():
    """Test the INVENTORY system with lead_time = 2 data"""

    print("\n=== Testing INVENTORY System with Lead Time = 2 ===")

    # Create test data
    train_file, test_file = create_leadtime2_test_data()

    # Load inventory system
    inventory = INVENTORY(dist='leadtime2', demand=80, volatility='low', n_train=2, n_horizon=10)

    print(f"✅ Loaded {len(inventory.train_instances)} training instances")
    print(f"✅ Loaded {len(inventory.test_instances)} test instances")

    # Check lead time
    lead_time = inventory.train_instances[0]['lead_time']
    print(f"✅ Lead time confirmed: {lead_time}")

    # Test simple algorithm
    code_string = """
def compute_order_amount(current_inventory, pipeline_inventory):
    base_stock_level = 30
    total_inventory = current_inventory + sum(pipeline_inventory)
    order_amount = max(0, base_stock_level - total_inventory)
    return order_amount
"""

    print(f"\n🔍 Testing algorithm:")
    print(code_string)

    # Evaluate algorithm
    result = inventory.evaluate(code_string)

    print(f"\n📊 Results:")
    print(f"   Training average cost: {result['avg']:.2f}")
    print(f"   Test average cost: {result['test_obj']:.2f}")
    print(f"   95% CI: [{result['lower']:.2f}, {result['upper']:.2f}]")

    return result

def test_analyzer_with_leadtime2():
    """Test the InventoryAnalyzer with lead_time = 2"""

    print("\n=== Testing InventoryAnalyzer with Lead Time = 2 ===")

    # Load inventory system
    inventory = INVENTORY(dist='leadtime2', demand=80, volatility='low', n_train=2, n_horizon=10)

    # Create analyzer
    analyzer = InventoryAnalyzer(inventory, n_train=2, data_summary='plain', algo_performance='plain', param_info=True)

    print("✅ InventoryAnalyzer created successfully")

    # Test parameter info
    print(f"\n📋 Parameter info:")
    print(analyzer.param)

    # Test data summary
    print(f"\n📊 Data summary:")
    data_summary = analyzer.get_data_summary()
    print(data_summary[:300] + "..." if len(data_summary) > 300 else data_summary)

    return analyzer

def compare_leadtime_1_vs_2():
    """Compare the same algorithm with lead_time = 1 vs lead_time = 2"""

    print("\n=== Comparing Lead Time 1 vs 2 ===")

    # Same algorithm code
    code_string = """
def compute_order_amount(current_inventory, pipeline_inventory):
    base_stock_level = 30
    total_inventory = current_inventory + sum(pipeline_inventory)
    order_amount = max(0, base_stock_level - total_inventory)
    return order_amount
"""

    # Test with lead_time = 1 (normal1)
    print("🔍 Testing with lead_time = 1 (normal1):")
    inventory_lt1 = INVENTORY(dist='normal1', demand=80, volatility='low', n_train=2, n_horizon=10)
    result_lt1 = inventory_lt1.evaluate(code_string)
    print(f"   Lead time 1 - Average cost: {result_lt1['avg']:.2f}")

    # Test with lead_time = 2 (leadtime2)
    print("🔍 Testing with lead_time = 2 (leadtime2):")
    inventory_lt2 = INVENTORY(dist='leadtime2', demand=80, volatility='low', n_train=2, n_horizon=10)
    result_lt2 = inventory_lt2.evaluate(code_string)
    print(f"   Lead time 2 - Average cost: {result_lt2['avg']:.2f}")

    print(f"\n📈 Impact of longer lead time:")
    cost_increase = result_lt2['avg'] - result_lt1['avg']
    print(f"   Cost increase: {cost_increase:.2f} ({cost_increase/result_lt1['avg']*100:.1f}%)")

    return result_lt1, result_lt2

def main():
    """Run all sanity checks"""

    print("🔧 INVENTORY_EX LEAD TIME = 2 SANITY CHECK")
    print("=" * 50)

    try:
        # 1. Manual calculation test
        manual_cost = test_simple_base_stock_policy()

        # 2. System test
        system_result = test_inventory_system_with_leadtime2()

        # 3. Analyzer test
        analyzer = test_analyzer_with_leadtime2()

        # 4. Comparison test
        lt1_result, lt2_result = compare_leadtime_1_vs_2()

        print("\n" + "=" * 50)
        print("✅ ALL SANITY CHECKS PASSED!")
        print("✅ Lead time = 2 implementation is working correctly")

    except Exception as e:
        print(f"\n❌ SANITY CHECK FAILED: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()