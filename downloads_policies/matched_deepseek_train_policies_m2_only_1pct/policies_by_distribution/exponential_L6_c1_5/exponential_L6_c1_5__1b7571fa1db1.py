# policy_hash: 1b7571fa1db1045d05d84d009be70e0cd64d5c71f5090b57404b6233d9cb248f
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L6_c1_5
# matched_train_cells: 4
# source_prompt_files: 1
# best_target_performance: 11796.44
# best_prompt_performance: 11796.43
# best_rel_error_pct: 0.000085
# example_source_txt: examples/inventory/deepseek-chat_exponential_L6_c1_5_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251218_020557.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 424.4762109473174  # OPT_PARAM: {"initial": 424.4762109473174, "min": 200, "max": 500, "type": "float"}
    safety_stock = 147.82701539791339  # OPT_PARAM: {"initial": 147.82701539791339, "min": 80, "max": 200, "type": "float"}
    pipeline_weight = 1.0  # OPT_PARAM: {"initial": 1.0, "min": 0.9, "max": 1.0, "type": "float"}
    inventory_weight = 0.8  # OPT_PARAM: {"initial": 0.8, "min": 0.8, "max": 1.2, "type": "float"}
    demand_estimate = 100.0  # OPT_PARAM: {"initial": 100.0, "min": 100, "max": 200, "type": "float"}
    smoothing_factor = 0.9  # OPT_PARAM: {"initial": 0.9, "min": 0.5, "max": 0.9, "type": "float"}

    # Calculate weighted pipeline inventory
    weighted_pipeline = sum(p * (pipeline_weight ** i) for i, p in enumerate(pipeline_orders))

    # Effective inventory position
    inventory_position = on_hand_inventory * inventory_weight + weighted_pipeline

    # Dynamic target based on demand estimate and safety stock
    target_inventory = base_stock + safety_stock * smoothing_factor

    # Order up to target
    order_amount = max(0, target_inventory - inventory_position)

    # Reasonable upper bound based on demand estimate
    order_amount = min(order_amount, demand_estimate * 1.5)

    # Ensure integer order quantity
    return order_amount
