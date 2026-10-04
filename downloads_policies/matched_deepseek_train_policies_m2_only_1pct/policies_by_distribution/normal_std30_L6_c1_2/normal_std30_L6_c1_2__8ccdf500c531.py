# policy_hash: 8ccdf500c5319bad6a885bc72b0bde8c87951dc6ac76f6027bb1b5cf2161293e
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std30_L6_c1_2
# matched_train_cells: 27
# source_prompt_files: 1
# best_target_performance: 2514.62
# best_prompt_performance: 2514.62
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_normal_std30_L6_c1_2_50_plain_processed_scipy_15_default_m2_2_r7/prompt_for_code/m2_20260128_053057.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 577.0375642795393  # OPT_PARAM: {"initial": 577.0375642795393, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 50.1  # OPT_PARAM: {"initial": 50.1, "min": 0, "max": 200, "type": "float"}
    demand_forecast = 84.59151351372714  # OPT_PARAM: {"initial": 84.59151351372714, "min": 50, "max": 200, "type": "float"}
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
    if order_amount > 0:
        order_amount = smoothing_factor * order_amount + (1 - smoothing_factor) * demand_forecast

    # Round to nearest integer
    order_amount = int(round(order_amount))

    return order_amount
