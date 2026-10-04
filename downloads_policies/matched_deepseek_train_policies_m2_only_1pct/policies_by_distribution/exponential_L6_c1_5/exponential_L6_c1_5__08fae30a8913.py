# policy_hash: 08fae30a8913389339f5908f78e7404b346b128c3aba8cd6af423a4223179ac9
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L6_c1_5
# matched_train_cells: 9
# source_prompt_files: 1
# best_target_performance: 12234.86
# best_prompt_performance: 12234.86
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L6_c1_5_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251218_020341.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 536.8024431957323  # OPT_PARAM: {"initial": 536.8024431957323, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 36.744618741904  # OPT_PARAM: {"initial": 36.744618741904, "min": 0, "max": 200, "type": "float"}
    demand_forecast_window = 3  # OPT_PARAM: {"initial": 3, "min": 1, "max": 10, "type": "int"}
    pipeline_weight = 0.4811075264790129  # OPT_PARAM: {"initial": 0.4811075264790129, "min": 0.1, "max": 1.5, "type": "float"}
    inventory_weight = 0.5806073355492982  # OPT_PARAM: {"initial": 0.5806073355492982, "min": 0.5, "max": 2.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Adjust base stock based on recent pipeline arrivals (as proxy for demand)
    recent_arrivals = pipeline_orders[0] if pipeline_orders else 0
    adjusted_base = base_stock + safety_stock

    # Calculate order amount with adjusted weights
    order_amount = max(0, adjusted_base * inventory_weight - inventory_position * pipeline_weight)

    # Round to nearest integer (realistic ordering)
    order_amount = int(round(order_amount))

    return order_amount
