# policy_hash: efc7b05306930a1d80982e7db88af8a246a31c705432d2ae3f381f39846fd7d1
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L2_c1_2
# matched_train_cells: 5
# source_prompt_files: 1
# best_target_performance: 5883.08
# best_prompt_performance: 5883.16
# best_rel_error_pct: 0.001360
# example_source_txt: examples/inventory/deepseek-chat_exponential_L2_c1_2_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251218_071009.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 273.22955095895963  # OPT_PARAM: {"initial": 273.22955095895963, "min": 200, "max": 350, "type": "float"}
    safety_stock = 83.22955095895706  # OPT_PARAM: {"initial": 83.22955095895706, "min": 60, "max": 140, "type": "float"}
    pipeline_factor = 0.8  # OPT_PARAM: {"initial": 0.8, "min": 0.8, "max": 1.0, "type": "float"}
    smoothing = 0.4  # OPT_PARAM: {"initial": 0.4, "min": 0.4, "max": 0.9, "type": "float"}
    demand_estimate = 115.0  # OPT_PARAM: {"initial": 115.0, "min": 90, "max": 150, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate pipeline coverage
    pipeline_coverage = sum(pipeline_orders) * pipeline_factor

    # Calculate target inventory level
    target_inventory = base_stock + safety_stock - pipeline_coverage

    # Ensure minimum target based on expected demand
    min_target = demand_estimate * 1.8
    target_inventory = max(target_inventory, min_target)

    # Calculate order needed
    order_needed = target_inventory - inventory_position

    # Apply smoothing with reasonable capping
    if order_needed > 0:
        # Cap order based on expected demand
        max_order = demand_estimate * 2.0
        capped_order = min(order_needed, max_order)
        smoothed_order = capped_order * smoothing
        order_amount = int(round(smoothed_order))
    else:
        order_amount = 0

    return order_amount
