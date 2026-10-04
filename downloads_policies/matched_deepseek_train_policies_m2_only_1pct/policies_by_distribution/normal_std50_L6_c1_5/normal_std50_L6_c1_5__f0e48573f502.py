# policy_hash: f0e48573f502f07247b02485b47e47886c0102a86ff2eb81b7b88d64816c9394
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std50_L6_c1_5
# matched_train_cells: 27
# source_prompt_files: 1
# best_target_performance: 6574.56
# best_prompt_performance: 6574.56
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_normal_std50_L6_c1_5_50_plain_processed_scipy_15_default_m2_2_r8/prompt_for_code/m2_20260128_221634.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 722.9162270001405  # OPT_PARAM: {"initial": 722.9162270001405, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 50.0  # OPT_PARAM: {"initial": 50.0, "min": 0, "max": 200, "type": "float"}
    demand_forecast = 50.0  # OPT_PARAM: {"initial": 50.0, "min": 50, "max": 250, "type": "float"}
    smoothing_factor = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 0.9, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand during lead time
    lead_time_demand = demand_forecast * len(pipeline_orders)

    # Calculate target inventory level
    target_inventory = lead_time_demand + safety_stock

    # Calculate order-up-to level
    order_up_to = max(base_stock, target_inventory)

    # Calculate order amount
    order_amount = max(0, order_up_to - inventory_position)

    # Apply smoothing to avoid large order fluctuations
    if order_amount > demand_forecast * 2:
        order_amount = demand_forecast * 2 + smoothing_factor * (order_amount - demand_forecast * 2)

    return order_amount
