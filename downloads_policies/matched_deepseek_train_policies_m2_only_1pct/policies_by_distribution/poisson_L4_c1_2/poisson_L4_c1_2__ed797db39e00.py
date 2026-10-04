# policy_hash: ed797db39e005d104eaeb3882332a489dfbc8c294b64061b5f69e71573cea22f
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L4_c1_2
# matched_train_cells: 29
# source_prompt_files: 2
# best_target_performance: 1727.93
# best_prompt_performance: 1727.93
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L4_c1_2_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251218_074029.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 388.29386214364666  # OPT_PARAM: {"initial": 388.29386214364666, "min": 300, "max": 500, "type": "float"}
    safety_stock = 33.29386214364845  # OPT_PARAM: {"initial": 33.29386214364845, "min": 10, "max": 50, "type": "float"}
    demand_forecast = 110.5015222306816  # OPT_PARAM: {"initial": 110.5015222306816, "min": 85, "max": 115, "type": "float"}
    pipeline_weight = 0.7860680637985573  # OPT_PARAM: {"initial": 0.7860680637985573, "min": 0.7, "max": 1.0, "type": "float"}
    forecast_adjustment = 0.8628900456961381  # OPT_PARAM: {"initial": 0.8628900456961381, "min": 0.7, "max": 1.1, "type": "float"}
    smoothing_factor = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 0.5, "type": "float"}

    # Calculate inventory position with discounted pipeline
    inventory_position = on_hand_inventory + sum(pipeline_orders) * pipeline_weight

    # Adjusted base stock based on forecast
    adjusted_base = base_stock * (demand_forecast / 100.0) * forecast_adjustment

    # Order-up-to level with safety stock
    order_up_to = adjusted_base + safety_stock

    # Calculate raw order amount
    raw_order = max(0, order_up_to - inventory_position)

    # Apply smoothing to reduce order volatility
    smoothed_order = smoothing_factor * raw_order + (1 - smoothing_factor) * pipeline_orders[-1] if pipeline_orders else raw_order

    # Round to nearest integer
    order_amount = int(round(smoothed_order))

    return order_amount
