# policy_hash: a1d82a0c1f985513ff4fccf6865b2fad08437f43719ae0708f5c770b203d261e
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std30_L4_c1_5
# matched_train_cells: 29
# source_prompt_files: 1
# best_target_performance: 3588.46
# best_prompt_performance: 3590.06
# best_rel_error_pct: 0.044587
# example_source_txt: examples/inventory/deepseek-chat_normal_std30_L4_c1_5_50_plain_processed_scipy_15_default_m2_2_r6/prompt_for_code/m2_20260129_230445.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 501.9060686741186  # OPT_PARAM: {"initial": 501.9060686741186, "min": 300, "max": 800, "type": "float"}
    safety_stock = 75.1  # OPT_PARAM: {"initial": 75.1, "min": 20, "max": 150, "type": "float"}
    demand_forecast = 94.1385951014109  # OPT_PARAM: {"initial": 94.1385951014109, "min": 80, "max": 130, "type": "float"}
    smoothing_factor = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 0.5, "type": "float"}
    lead_time = 4

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand during lead time
    expected_lead_time_demand = demand_forecast * lead_time

    # Calculate target inventory level
    target_inventory = expected_lead_time_demand + safety_stock

    # Use the maximum of base_stock and target_inventory as order-up-to level
    order_up_to = max(base_stock, target_inventory)

    # Calculate raw order amount
    raw_order = max(0, order_up_to - inventory_position)

    # Apply smoothing only if raw order is positive
    if raw_order > 0:
        order_amount = smoothing_factor * raw_order + (1 - smoothing_factor) * demand_forecast
    else:
        order_amount = 0

    # Round to nearest integer
    order_amount = int(round(order_amount))

    return order_amount
