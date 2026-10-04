# policy_hash: 186d28b1570b379bb1d6c51b5028827f088e522ff09329e4e6727f952fc81e34
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L4_c1_5
# matched_train_cells: 2
# source_prompt_files: 1
# best_target_performance: 1213.28
# best_prompt_performance: 1212.54
# best_rel_error_pct: 0.060992
# example_source_txt: examples/inventory/deepseek-chat_poisson_L4_c1_5_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251218_083521.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 400.0  # OPT_PARAM: {"initial": 400.0, "min": 400, "max": 650, "type": "float"}
    demand_forecast = 94.98519327316241  # OPT_PARAM: {"initial": 94.98519327316241, "min": 90, "max": 110, "type": "float"}
    smoothing_factor = 0.01  # OPT_PARAM: {"initial": 0.01, "min": 0.01, "max": 0.5, "type": "float"}
    safety_stock_multiplier = 1.8086698423613181  # OPT_PARAM: {"initial": 1.8086698423613181, "min": 0.5, "max": 2.0, "type": "float"}
    lead_time = 4  # Fixed parameter

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate safety stock
    safety_stock = safety_stock_multiplier * demand_forecast * (lead_time ** 0.5)

    # Calculate target inventory position
    target_inventory = base_stock + safety_stock

    # Calculate order-up-to level
    order_up_to = max(0, target_inventory - inventory_position)

    # Apply smoothing
    smoothed_order = smoothing_factor * order_up_to + (1 - smoothing_factor) * demand_forecast

    # Ensure non-negative integer order
    order_amount = max(0, round(smoothed_order))

    return order_amount
