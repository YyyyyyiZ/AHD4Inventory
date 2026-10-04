# policy_hash: 63d4091cfdf35d595f0c057878e9b3d8dcbb8a2bab9793715e53e9e4172d15e2
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L4_c1_5
# matched_train_cells: 10
# source_prompt_files: 1
# best_target_performance: 12046.84
# best_prompt_performance: 12045.58
# best_rel_error_pct: 0.010459
# example_source_txt: examples/inventory/deepseek-chat_exponential_L4_c1_5_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251218_084320.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 464.6232480991447  # OPT_PARAM: {"initial": 464.6232480991447, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 165.62331431924946  # OPT_PARAM: {"initial": 165.62331431924946, "min": 0, "max": 500, "type": "float"}
    demand_estimate = 68.37091143672897  # OPT_PARAM: {"initial": 68.37091143672897, "min": 10, "max": 500, "type": "float"}
    demand_std_factor = 1.3086712528137177  # OPT_PARAM: {"initial": 1.3086712528137177, "min": 0.5, "max": 3.0, "type": "float"}
    pipeline_weight = 0.43748452736753324  # OPT_PARAM: {"initial": 0.43748452736753324, "min": 0.0, "max": 1.0, "type": "float"}
    adjustment_smoothing = 0.7644939253470255  # OPT_PARAM: {"initial": 0.7644939253470255, "min": 0.0, "max": 1.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand during lead time with safety buffer
    lead_time = len(pipeline_orders)
    lead_time_demand = demand_estimate * lead_time
    safety_buffer = demand_std_factor * (demand_estimate ** 0.5) * (lead_time ** 0.5)

    # Adjust base stock based on pipeline coverage and variability
    adjusted_base = base_stock + safety_stock - lead_time_demand + safety_buffer

    # Apply pipeline smoothing to reduce order volatility
    pipeline_avg = sum(pipeline_orders) / max(1, len(pipeline_orders))
    pipeline_adjustment = pipeline_weight * (demand_estimate - pipeline_avg)

    # Smooth the adjustment
    smoothed_adjustment = adjustment_smoothing * pipeline_adjustment

    # Final order calculation
    order_amount = max(0, adjusted_base - inventory_position + smoothed_adjustment)

    # Round to nearest integer (as order_amount should be int)
    order_amount = int(round(order_amount))

    return order_amount
