# policy_hash: 909a4531e7d7de52dbdf2f55f50480891a916b644caa3c29245e3fe0adcb65a2
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L4_c1_5
# matched_train_cells: 7
# source_prompt_files: 1
# best_target_performance: 10977.21
# best_prompt_performance: 10977.21
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L4_c1_5_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_045916.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 377.9899050201224  # OPT_PARAM: {"initial": 377.9899050201224, "min": 200, "max": 600, "type": "float"}
    demand_estimate = 120.76417052848544  # OPT_PARAM: {"initial": 120.76417052848544, "min": 80, "max": 200, "type": "float"}
    safety_stock_multiplier = 1.8895984698921824  # OPT_PARAM: {"initial": 1.8895984698921824, "min": 0.5, "max": 2.5, "type": "float"}
    order_smoothing = 0.173620410193325  # OPT_PARAM: {"initial": 0.173620410193325, "min": 0.1, "max": 1.0, "type": "float"}
    min_order_fraction = 0.37810445569764345  # OPT_PARAM: {"initial": 0.37810445569764345, "min": 0.3, "max": 1.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate safety stock based on lead time demand variability
    lead_time = len(pipeline_orders)
    safety_stock = safety_stock_multiplier * demand_estimate * (lead_time ** 0.5)

    # Calculate target inventory position
    target_position = base_stock + safety_stock

    # Calculate order needed to reach target
    order_needed = target_position - inventory_position

    # Apply order smoothing and ensure non-negative order
    if order_needed > 0:
        # Smooth order adjustment
        order_amount = max(0, order_smoothing * order_needed)
        # Ensure minimum order when significantly below target
        if inventory_position < target_position * min_order_fraction:
            order_amount = max(order_amount, demand_estimate)
    else:
        order_amount = 0

    return order_amount
