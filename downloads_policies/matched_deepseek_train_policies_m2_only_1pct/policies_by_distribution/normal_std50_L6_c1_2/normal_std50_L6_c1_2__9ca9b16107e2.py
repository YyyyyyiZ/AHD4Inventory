# policy_hash: 9ca9b16107e22066359d7479fdcde6763ee864fd66646a5f3bc27dc63e15b168
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std50_L6_c1_2
# matched_train_cells: 10
# source_prompt_files: 1
# best_target_performance: 3828.3
# best_prompt_performance: 3828.3
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_normal_std50_L6_c1_2_50_plain_processed_scipy_15_default_m2_2_r6/prompt_for_code/m2_20260129_022116.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 700.0  # OPT_PARAM: {"initial": 700.0, "min": 300, "max": 700, "type": "float"}
    safety_stock = 150.0  # OPT_PARAM: {"initial": 150.0, "min": 20, "max": 150, "type": "float"}
    smoothing_factor = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 0.5, "type": "float"}
    demand_forecast_factor = 0.3  # OPT_PARAM: {"initial": 0.3, "min": 0.05, "max": 0.3, "type": "float"}
    lead_time_factor = 1.5  # OPT_PARAM: {"initial": 1.5, "min": 0.8, "max": 1.5, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Estimate upcoming demand based on pipeline orders (as proxy for recent orders)
    # When pipeline is full, recent orders reflect recent demand patterns
    avg_pipeline_order = sum(pipeline_orders) / len(pipeline_orders) if pipeline_orders else 0
    demand_adjustment = demand_forecast_factor * avg_pipeline_order

    # Adjust base stock for lead time
    adjusted_base = base_stock * lead_time_factor

    # Calculate target inventory with dynamic adjustment
    target_inventory = adjusted_base + safety_stock + demand_adjustment

    # Apply smoothing to avoid overreacting
    smoothed_target = smoothing_factor * target_inventory + (1 - smoothing_factor) * inventory_position

    # Calculate order amount
    order_amount = max(0, smoothed_target - inventory_position)

    # Round to nearest integer
    return order_amount
