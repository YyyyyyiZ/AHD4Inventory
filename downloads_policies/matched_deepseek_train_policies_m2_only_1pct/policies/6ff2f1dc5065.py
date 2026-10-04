# policy_hash: 6ff2f1dc5065eef324da2c997eafd81ef25e5a8dfb17aa02ff11993a57169bed
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L2_c1_2
# matched_train_cells: 4
# source_prompt_files: 1
# best_target_performance: 5886.5
# best_prompt_performance: 5886.5
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L2_c1_2_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_025935.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 180.0  # OPT_PARAM: {"initial": 180.0, "min": 100, "max": 300, "type": "float"}
    safety_stock = 25.0  # OPT_PARAM: {"initial": 25.0, "min": 10, "max": 80, "type": "float"}
    demand_estimate = 77.53633758040289  # OPT_PARAM: {"initial": 77.53633758040289, "min": 60, "max": 150, "type": "float"}
    smoothing = 0.3487836596158211  # OPT_PARAM: {"initial": 0.3487836596158211, "min": 0.1, "max": 0.8, "type": "float"}
    lead_time = len(pipeline_orders)

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand during lead time plus one period
    lead_time_demand = demand_estimate * (lead_time + 1)

    # Dynamic order-up-to level based on pipeline status
    pipeline_ratio = sum(pipeline_orders) / (demand_estimate * lead_time + 1e-6)
    pipeline_adjustment = 0.2  # OPT_PARAM: {"initial": 0.2, "min": 0.1, "max": 0.5, "type": "float"}

    order_up_to = 1.1  # Optimized
    order_up_to = max(order_up_to, lead_time_demand * 1.1)  # OPT_PARAM: {"initial": 1.1, "min": 1.0, "max": 1.5, "type": "float"}

    # Calculate raw order quantity
    raw_order = max(0, order_up_to - inventory_position)

    # Apply stronger smoothing for stability
    smoothed_order = smoothing * raw_order + (1 - smoothing) * demand_estimate

    # Ensure minimum order size for efficiency
    if smoothed_order < demand_estimate * 0.3:  # OPT_PARAM: {"initial": 0.3, "min": 0.1, "max": 0.5, "type": "float"}
        smoothed_order = 0

    # Round to nearest integer
    order_amount = int(round(smoothed_order))

    return order_amount
