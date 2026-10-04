# policy_hash: 8056a2ebab29d8aba1b11a436e12870f1a49042a381f158ca5fb869a5068e161
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std50_L6_c1_2
# matched_train_cells: 10
# source_prompt_files: 1
# best_target_performance: 3831.77
# best_prompt_performance: 3830.14
# best_rel_error_pct: 0.042539
# example_source_txt: examples/inventory/deepseek-chat_normal_std50_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251216_235541.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 383.4406788222814  # OPT_PARAM: {"initial": 383.4406788222814, "min": 200, "max": 600, "type": "float"}
    safety_stock = 123.44067882228252  # OPT_PARAM: {"initial": 123.44067882228252, "min": 50, "max": 250, "type": "float"}
    smoothing_factor = 0.1706514268557243  # OPT_PARAM: {"initial": 0.1706514268557243, "min": 0.1, "max": 0.8, "type": "float"}
    demand_forecast_factor = 0.25977424685419587  # OPT_PARAM: {"initial": 0.25977424685419587, "min": 0.05, "max": 0.3, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Simple demand forecast using recent pipeline arrivals (last 3 periods)
    if len(pipeline_orders) >= 3:
        recent_arrivals = pipeline_orders[:3]  # Oldest 3 are arriving soonest
        expected_demand = sum(recent_arrivals) / 3.0
    else:
        expected_demand = 0

    # Adjusted base stock with safety stock
    adjusted_base_stock = base_stock + safety_stock

    # Add demand forecast component
    target_position = adjusted_base_stock + expected_demand * demand_forecast_factor

    # Calculate raw order
    raw_order = max(0, target_position - inventory_position)

    # Apply smoothing to avoid extreme order fluctuations
    smoothed_order = raw_order * smoothing_factor + expected_demand * (1 - smoothing_factor)

    # Round to nearest integer
    order_amount = max(0, int(round(smoothed_order)))

    return order_amount
