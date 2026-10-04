# policy_hash: d1e1ede1c6834e6952d73e49fb2005c45b27e7a12381f89a81ab6f82ece4394e
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L6_c1_2
# matched_train_cells: 4
# source_prompt_files: 1
# best_target_performance: 6728.43
# best_prompt_performance: 6728.94
# best_rel_error_pct: 0.007580
# example_source_txt: examples/inventory/deepseek-chat_exponential_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251218_012255.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 281.38732406136756  # OPT_PARAM: {"initial": 281.38732406136756, "min": 100, "max": 500, "type": "float"}
    safety_stock = 41.387324061367856  # OPT_PARAM: {"initial": 41.387324061367856, "min": 10, "max": 100, "type": "float"}
    smoothing_factor = 0.4192201666748559  # OPT_PARAM: {"initial": 0.4192201666748559, "min": 0.1, "max": 0.8, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate target inventory position
    target_inventory = base_stock + safety_stock

    # Calculate order needed to reach target
    needed = target_inventory - inventory_position

    # Apply smoothing to reduce order volatility
    if needed > 0:
        order_amount = int(round(smoothing_factor * needed))
    else:
        order_amount = 0

    return order_amount
