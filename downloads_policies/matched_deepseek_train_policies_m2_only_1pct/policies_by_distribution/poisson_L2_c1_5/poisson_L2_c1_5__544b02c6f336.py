# policy_hash: 544b02c6f3363e2961cb18a5b46e3bf40257dec211b60ab6198fc39a369dc425
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L2_c1_5
# matched_train_cells: 7
# source_prompt_files: 1
# best_target_performance: 1368.14
# best_prompt_performance: 1367.86
# best_rel_error_pct: 0.020466
# example_source_txt: examples/inventory/deepseek-chat_poisson_L2_c1_5_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_025700.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 247.96450659942676  # OPT_PARAM: {"initial": 247.96450659942676, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 9.113377384274056  # OPT_PARAM: {"initial": 9.113377384274056, "min": 0, "max": 200, "type": "float"}
    demand_adjustment = 0.5  # OPT_PARAM: {"initial": 0.5, "min": 0.5, "max": 1.5, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Estimate upcoming demand based on pipeline orders (since L=2)
    # Use the most recent order as a proxy for demand expectation
    recent_order = pipeline_orders[-1] if pipeline_orders else 0
    expected_demand = recent_order * demand_adjustment

    # Adjust base stock based on expected demand
    adjusted_base_stock = base_stock + safety_stock + expected_demand

    # Calculate order amount
    order_amount = max(0, adjusted_base_stock - inventory_position)

    # Apply smoothing to avoid extreme order fluctuations
    smoothing_factor = 0.30967211946108714  # OPT_PARAM: {"initial": 0.30967211946108714, "min": 0.1, "max": 1.0, "type": "float"}
    if pipeline_orders and len(pipeline_orders) > 0:
        previous_order = pipeline_orders[-1]
        smoothed_order = smoothing_factor * order_amount + (1 - smoothing_factor) * previous_order
        order_amount = max(0, smoothed_order)

    # Round to nearest integer since order amount should be integer
    order_amount = int(round(order_amount))

    return order_amount
