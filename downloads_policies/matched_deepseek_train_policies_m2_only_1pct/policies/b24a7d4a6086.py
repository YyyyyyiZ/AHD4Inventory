# policy_hash: b24a7d4a6086cda1cc6b0f471f74346c08dd8611f69e2e7c204ad5024e65fdb9
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std10_L6_c1_5
# matched_train_cells: 15
# source_prompt_files: 1
# best_target_performance: 1304.66
# best_prompt_performance: 1306.75
# best_rel_error_pct: 0.160195
# example_source_txt: examples/inventory/deepseek-chat_normal_std10_L6_c1_5_50_plain_processed_scipy_15_default_m2_2_r6/prompt_for_code/m2_20260130_184253.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 705.9901690597175  # OPT_PARAM: {"initial": 705.9901690597175, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 50.0  # OPT_PARAM: {"initial": 50.0, "min": 0, "max": 200, "type": "float"}
    demand_forecast = 50.0  # OPT_PARAM: {"initial": 50.0, "min": 50, "max": 150, "type": "float"}
    smoothing_factor = 0.01  # OPT_PARAM: {"initial": 0.01, "min": 0.01, "max": 1.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand during lead time
    expected_lead_time_demand = demand_forecast * len(pipeline_orders)

    # Calculate target inventory position
    target_position = expected_lead_time_demand + safety_stock

    # Calculate order-up-to level
    order_up_to = max(base_stock, target_position)

    # Calculate order amount
    order_amount = max(0, order_up_to - inventory_position)

    # Apply smoothing to avoid large order fluctuations
    if order_amount > demand_forecast * 2:
        order_amount = demand_forecast * 2 + smoothing_factor * (order_amount - demand_forecast * 2)

    return order_amount
