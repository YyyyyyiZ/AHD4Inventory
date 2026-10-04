# policy_hash: dc8ac5afdedf7179ff6f06b1ab59dabcda2a35c2a1d8ec030a19a2b2a3af05e0
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L4_c1_5
# matched_train_cells: 8
# source_prompt_files: 2
# best_target_performance: 2018.8
# best_prompt_performance: 2019.57
# best_rel_error_pct: 0.038141
# example_source_txt: examples/inventory/deepseek-chat_poisson_L4_c1_5_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_045145.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 501.1468241981803  # OPT_PARAM: {"initial": 501.1468241981803, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 48.24801388584313  # OPT_PARAM: {"initial": 48.24801388584313, "min": 0, "max": 200, "type": "float"}
    demand_forecast_factor = 0.9  # OPT_PARAM: {"initial": 0.9, "min": 0.5, "max": 1.5, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate target inventory level
    target_inventory = base_stock + safety_stock

    # Calculate order quantity
    order_amount = max(0, target_inventory - inventory_position)

    # Apply smoothing to avoid large order fluctuations
    smoothing_factor = 0.6594757944396332  # OPT_PARAM: {"initial": 0.6594757944396332, "min": 0.1, "max": 1.0, "type": "float"}
    if order_amount > 0:
        order_amount = smoothing_factor * order_amount

    # Round to nearest integer (since order amounts should be integers)
    order_amount = int(round(order_amount))

    return order_amount
