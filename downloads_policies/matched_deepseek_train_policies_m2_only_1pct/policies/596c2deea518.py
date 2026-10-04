# policy_hash: 596c2deea5186c50a0bc25b2e549ec3315a5f698f975b790461c8aa609eed4d2
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std50_L6_c1_2
# matched_train_cells: 5
# source_prompt_files: 1
# best_target_performance: 4476.4
# best_prompt_performance: 4476.4
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_normal_std50_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251217_011027.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 477.45231458962144  # OPT_PARAM: {"initial": 477.45231458962144, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 37.77864280897027  # OPT_PARAM: {"initial": 37.77864280897027, "min": 0, "max": 200, "type": "float"}
    demand_forecast = 50.0  # OPT_PARAM: {"initial": 50.0, "min": 50, "max": 200, "type": "float"}
    smoothing_factor = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 0.9, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand during lead time
    expected_lead_time_demand = demand_forecast * len(pipeline_orders)

    # Calculate target inventory level
    target_inventory = expected_lead_time_demand + safety_stock

    # Calculate order-up-to level
    order_up_to = max(base_stock, target_inventory)

    # Calculate order amount
    order_amount = max(0, order_up_to - inventory_position)

    # Apply smoothing to reduce order volatility
    if len(pipeline_orders) > 0:
        last_order = pipeline_orders[-1]
        smoothed_order = smoothing_factor * order_amount + (1 - smoothing_factor) * last_order
        order_amount = max(0, smoothed_order)

    return order_amount
