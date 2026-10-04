# policy_hash: 5e37745847b72fc7956e188b8f2d35f6fffedcf3c79bd639377412ee6f7a8bdb
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L4_c1_5
# matched_train_cells: 7
# source_prompt_files: 1
# best_target_performance: 11381.86
# best_prompt_performance: 11381.86
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L4_c1_5_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_043854.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 381.048656030187  # OPT_PARAM: {"initial": 381.048656030187, "min": 100, "max": 800, "type": "float"}
    demand_estimate = 99.98271260985156  # OPT_PARAM: {"initial": 99.98271260985156, "min": 50, "max": 300, "type": "float"}
    smoothing_factor = 0.2909279850108353  # OPT_PARAM: {"initial": 0.2909279850108353, "min": 0.1, "max": 1.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand during lead time
    expected_lead_time_demand = demand_estimate * len(pipeline_orders)

    # Calculate target inventory position with dynamic adjustment
    # Base target considers expected demand plus buffer
    target_position = base_stock + expected_lead_time_demand * 0.3

    # Calculate order needed to reach target
    order_needed = target_position - inventory_position

    # Apply smoothing to avoid large order swings
    if order_needed > 0:
        # Smooth order adjustment
        order_amount = max(0, smoothing_factor * order_needed)
        # Ensure we order at least expected demand when below target
        if inventory_position < target_position * 0.8:
            order_amount = max(order_amount, demand_estimate)
    else:
        order_amount = 0

    return order_amount
