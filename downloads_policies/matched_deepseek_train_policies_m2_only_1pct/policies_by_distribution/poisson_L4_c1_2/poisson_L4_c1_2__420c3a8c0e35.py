# policy_hash: 420c3a8c0e3535c3937cc627a59d5688de62e33538d2c5e42d40d9a455c66fde
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L4_c1_2
# matched_train_cells: 2
# source_prompt_files: 1
# best_target_performance: 1648.94
# best_prompt_performance: 1648.8
# best_rel_error_pct: 0.008490
# example_source_txt: examples/inventory/deepseek-chat_poisson_L4_c1_2_50_plain_processed_scipy_15_default_m2_2_r7/prompt_for_code/m2_20260130_072358.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 501.8179896158785  # OPT_PARAM: {"initial": 501.8179896158785, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 50.0  # OPT_PARAM: {"initial": 50.0, "min": 0, "max": 200, "type": "float"}
    demand_forecast = 100.0  # OPT_PARAM: {"initial": 100.0, "min": 50, "max": 150, "type": "float"}
    smoothing_factor = 0.8079923965399923  # OPT_PARAM: {"initial": 0.8079923965399923, "min": 0.1, "max": 0.9, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand during lead time
    expected_lead_time_demand = 4 * demand_forecast  # L=4

    # Calculate target inventory level
    target_inventory = expected_lead_time_demand + safety_stock

    # Calculate order-up-to level
    order_up_to = max(base_stock, target_inventory)

    # Calculate order amount
    order_amount = max(0, order_up_to - inventory_position)

    # Apply smoothing to reduce order volatility
    if order_amount > 0:
        order_amount = int(order_amount * smoothing_factor + 0.5)

    return order_amount
