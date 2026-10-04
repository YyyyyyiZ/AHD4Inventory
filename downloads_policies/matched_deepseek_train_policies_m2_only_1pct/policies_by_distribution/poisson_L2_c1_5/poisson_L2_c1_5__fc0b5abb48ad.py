# policy_hash: fc0b5abb48ad19fe78014ccce62d1ebf5d716b4a6f85c76cfbcb1a44be74b3a2
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L2_c1_5
# matched_train_cells: 2
# source_prompt_files: 1
# best_target_performance: 3768.46
# best_prompt_performance: 3768.46
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L2_c1_5_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251218_065522.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 308.9814814814807  # OPT_PARAM: {"initial": 308.9814814814807, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 50.0  # OPT_PARAM: {"initial": 50.0, "min": 0, "max": 200, "type": "float"}
    demand_adjustment = 0.8  # OPT_PARAM: {"initial": 0.8, "min": 0.5, "max": 1.5, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Estimate upcoming demand based on pipeline orders (as proxy for recent demand)
    # Use average of recent orders as demand estimate
    if len(pipeline_orders) >= 2:
        recent_orders = pipeline_orders[-2:]  # Last two orders placed
        demand_estimate = sum(recent_orders) / len(recent_orders) * demand_adjustment
    else:
        demand_estimate = 100.0  # Default estimate

    # Dynamic base stock adjustment
    dynamic_base = base_stock + safety_stock - demand_estimate

    # Calculate order amount
    order_amount = max(0, dynamic_base - inventory_position)

    # Round to nearest integer (since order amounts should be integers)
    order_amount = int(round(order_amount))

    return order_amount
