# policy_hash: fa068eda4ef91936da919b6b216724ec52c2d57ad8ea6b335db8e9dc1717452f
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std50_L6_c1_5
# matched_train_cells: 63
# source_prompt_files: 1
# best_target_performance: 6858.28
# best_prompt_performance: 6858.28
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_normal_std50_L6_c1_5_50_plain_processed_scipy_15_default_m2_2_r7/prompt_for_code/m2_20260129_090514.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 1194.2923821411007  # OPT_PARAM: {"initial": 1194.2923821411007, "min": 500, "max": 1200, "type": "float"}
    safety_stock = 297.83202494867623  # OPT_PARAM: {"initial": 297.83202494867623, "min": 100, "max": 300, "type": "float"}
    demand_forecast = 104.75023604966228  # OPT_PARAM: {"initial": 104.75023604966228, "min": 100, "max": 200, "type": "float"}
    lead_time_days = 6  # OPT_PARAM: {"initial": 6, "min": 4, "max": 8, "type": "int"}
    smoothing_factor = 0.3  # OPT_PARAM: {"initial": 0.3, "min": 0.3, "max": 0.9, "type": "float"}
    min_order_quantity = 10.1  # OPT_PARAM: {"initial": 10.1, "min": 0, "max": 50, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate target inventory level
    # Base stock + safety stock - expected demand during lead time
    target_inventory = base_stock + safety_stock - (demand_forecast * lead_time_days)

    # Calculate raw order quantity
    raw_order = max(0, target_inventory - inventory_position)

    # Apply smoothing to reduce order volatility
    if raw_order > 0:
        order_amount = max(min_order_quantity, raw_order * smoothing_factor)
    else:
        order_amount = 0

    # Round to nearest integer
    order_amount = int(round(order_amount))

    return order_amount
