# policy_hash: 6b7ea0c42caf87af9bb9b119e412d4cfc2f0937276633c4f1644d49598acadf0
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L4_c1_5
# matched_train_cells: 7
# source_prompt_files: 1
# best_target_performance: 2003.96
# best_prompt_performance: 2003.96
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L4_c1_5_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251218_082607.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 491.0000000000088  # OPT_PARAM: {"initial": 491.0000000000088, "min": 400, "max": 650, "type": "float"}
    demand_forecast = 90.0  # OPT_PARAM: {"initial": 90.0, "min": 90, "max": 110, "type": "float"}
    smoothing_factor = 0.2  # OPT_PARAM: {"initial": 0.2, "min": 0.2, "max": 0.5, "type": "float"}
    safety_stock = 80.0  # OPT_PARAM: {"initial": 80.0, "min": 50, "max": 150, "type": "float"}
    lead_time_factor = 1.2  # OPT_PARAM: {"initial": 1.2, "min": 1.0, "max": 1.5, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand during lead time
    lead_time_demand = lead_time_factor * demand_forecast * len(pipeline_orders)

    # Calculate target inventory level
    target_inventory = lead_time_demand + safety_stock

    # Calculate order-up-to level
    order_up_to = max(base_stock, target_inventory)

    # Calculate required order
    required_order = max(0, order_up_to - inventory_position)

    # Smooth adjustment
    smoothed_order = smoothing_factor * required_order + (1 - smoothing_factor) * demand_forecast

    # Ensure non-negative integer order
    order_amount = max(0, round(smoothed_order))

    return order_amount
