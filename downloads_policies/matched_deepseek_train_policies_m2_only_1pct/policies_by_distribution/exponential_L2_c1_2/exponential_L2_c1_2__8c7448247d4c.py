# policy_hash: 8c7448247d4cd25e229506a2718ce51ff53c53aa3668fc1838f2350234880b16
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L2_c1_2
# matched_train_cells: 1
# source_prompt_files: 1
# best_target_performance: 7594.7
# best_prompt_performance: 7594.7
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L2_c1_2_50_plain_processed_scipy_15_default_m2_4_r4/prompt_for_code/m2_20251218_103935.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 250.0  # OPT_PARAM: {"initial": 250.0, "min": 100, "max": 500, "type": "float"}
    safety_stock = 80.0  # OPT_PARAM: {"initial": 80.0, "min": 20, "max": 200, "type": "float"}
    demand_adj_factor = 0.7  # OPT_PARAM: {"initial": 0.7, "min": 0.3, "max": 1.5, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Estimate upcoming demand based on pipeline arrivals
    # Use weighted average of recent pipeline orders as demand proxy
    if len(pipeline_orders) >= 2:
        recent_orders = pipeline_orders[-2:]  # Last two orders placed
        demand_estimate = sum(recent_orders) / len(recent_orders) * demand_adj_factor
    else:
        demand_estimate = 0

    # Dynamic base stock adjustment
    dynamic_base = base_stock + max(0, safety_stock - demand_estimate)

    # Calculate order amount with smoothing
    raw_order = max(0, dynamic_base - inventory_position)

    # Round to nearest integer for practical ordering
    order_amount = int(round(raw_order))

    return order_amount
