# policy_hash: ac6beae9280cad0ea3a57f20b9706f48c53362662c78281dbae6e37125e4fba5
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L4_c1_2
# matched_train_cells: 23
# source_prompt_files: 1
# best_target_performance: 6140.78
# best_prompt_performance: 6140.36
# best_rel_error_pct: 0.006840
# example_source_txt: examples/inventory/deepseek-chat_exponential_L4_c1_2_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251218_080037.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 450.0000232025056  # OPT_PARAM: {"initial": 450.0000232025056, "min": 100, "max": 800, "type": "float"}
    safety_stock = 50.000023202505595  # OPT_PARAM: {"initial": 50.000023202505595, "min": 0, "max": 200, "type": "float"}
    smoothing_factor = 0.17662446096233717  # OPT_PARAM: {"initial": 0.17662446096233717, "min": 0.1, "max": 1.0, "type": "float"}
    min_order_threshold = 5.0  # OPT_PARAM: {"initial": 5.0, "min": 0, "max": 20, "type": "float"}

    # Calculate net inventory position
    net_inventory = on_hand_inventory + sum(pipeline_orders)

    # Target inventory position
    target_position = base_stock + safety_stock

    # Calculate order amount
    raw_order = max(0, target_position - net_inventory)

    # Apply smoothing
    smoothed_order = smoothing_factor * raw_order

    # Round and apply minimum order threshold
    if smoothed_order < min_order_threshold:
        order_amount = 0
    else:
        order_amount = int(round(smoothed_order))

    return order_amount
