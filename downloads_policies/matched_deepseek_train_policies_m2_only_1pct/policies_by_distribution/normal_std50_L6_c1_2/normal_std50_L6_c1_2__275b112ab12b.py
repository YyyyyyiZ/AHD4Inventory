# policy_hash: 275b112ab12b899a6e8fecc3f050d23c6139e69b37ca4de8e0243215bdfeb087
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std50_L6_c1_2
# matched_train_cells: 35
# source_prompt_files: 2
# best_target_performance: 3809.29
# best_prompt_performance: 3808.9
# best_rel_error_pct: 0.010238
# example_source_txt: examples/inventory/deepseek-chat_normal_std50_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251217_001017.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 427.7685265016654  # OPT_PARAM: {"initial": 427.7685265016654, "min": 300, "max": 550, "type": "float"}
    safety_stock = 67.76852650166707  # OPT_PARAM: {"initial": 67.76852650166707, "min": 20, "max": 120, "type": "float"}
    smoothing_factor = 0.16324762567317977  # OPT_PARAM: {"initial": 0.16324762567317977, "min": 0.1, "max": 0.5, "type": "float"}
    demand_forecast_factor = 1.226929263447095  # OPT_PARAM: {"initial": 1.226929263447095, "min": 0.8, "max": 1.5, "type": "float"}
    pipeline_weight = 0.7  # OPT_PARAM: {"initial": 0.7, "min": 0.3, "max": 0.9, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Simple demand forecast: average of recent pipeline arrivals (last 3 periods)
    if len(pipeline_orders) >= 3:
        recent_arrivals = pipeline_orders[:3]  # Oldest first, so these are recent arrivals
        expected_demand = sum(recent_arrivals) / 3.0
    else:
        expected_demand = 0

    # Adjust base stock with forecast
    adjusted_base_stock = base_stock + safety_stock + (expected_demand * demand_forecast_factor)

    # Calculate order-up-to level
    order_up_to = max(0, adjusted_base_stock - inventory_position)

    # Apply smoothing
    smoothed_order = smoothing_factor * order_up_to + (1 - smoothing_factor) * expected_demand

    # Round to nearest integer
    order_amount = int(round(smoothed_order))

    return order_amount
