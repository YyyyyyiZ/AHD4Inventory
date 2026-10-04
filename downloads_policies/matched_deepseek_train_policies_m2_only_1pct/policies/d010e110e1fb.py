# policy_hash: d010e110e1fbbba477a224abb5f023c0ed70b9a5bd629d675b656a15153fe913
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L4_c1_5
# matched_train_cells: 21
# source_prompt_files: 1
# best_target_performance: 1319.93
# best_prompt_performance: 1319.12
# best_rel_error_pct: 0.061367
# example_source_txt: examples/inventory/deepseek-chat_poisson_L4_c1_5_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251218_083423.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 350.53560100726884  # OPT_PARAM: {"initial": 350.53560100726884, "min": 350, "max": 550, "type": "float"}
    demand_forecast = 95.08665825802363  # OPT_PARAM: {"initial": 95.08665825802363, "min": 95, "max": 105, "type": "float"}
    smoothing_factor = 0.05  # OPT_PARAM: {"initial": 0.05, "min": 0.05, "max": 0.3, "type": "float"}
    safety_stock_multiplier = 0.9035268538101293  # OPT_PARAM: {"initial": 0.9035268538101293, "min": 0.8, "max": 1.8, "type": "float"}
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
