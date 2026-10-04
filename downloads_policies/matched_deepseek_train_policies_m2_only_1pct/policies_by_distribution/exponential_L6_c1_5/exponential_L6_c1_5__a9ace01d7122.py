# policy_hash: a9ace01d71220002a1833447adfe35dc1498c788c39455374fd2d45efe64a74e
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L6_c1_5
# matched_train_cells: 6
# source_prompt_files: 1
# best_target_performance: 11815.93
# best_prompt_performance: 11815.32
# best_rel_error_pct: 0.005163
# example_source_txt: examples/inventory/deepseek-chat_exponential_L6_c1_5_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251218_021152.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 397.49773005045864  # OPT_PARAM: {"initial": 397.49773005045864, "min": 300, "max": 450, "type": "float"}
    safety_stock = 132.25280413283008  # OPT_PARAM: {"initial": 132.25280413283008, "min": 80, "max": 160, "type": "float"}
    pipeline_weight = 1.0  # OPT_PARAM: {"initial": 1.0, "min": 0.8, "max": 1.0, "type": "float"}
    inventory_weight = 0.9  # OPT_PARAM: {"initial": 0.9, "min": 0.9, "max": 1.1, "type": "float"}
    demand_estimate = 110.1777299572974  # OPT_PARAM: {"initial": 110.1777299572974, "min": 110, "max": 150, "type": "float"}
    smoothing_factor = 0.9  # OPT_PARAM: {"initial": 0.9, "min": 0.5, "max": 0.9, "type": "float"}
    order_multiplier = 1.2022587800449638  # OPT_PARAM: {"initial": 1.2022587800449638, "min": 1.0, "max": 1.5, "type": "float"}
    min_order = 49.73075686300811  # OPT_PARAM: {"initial": 49.73075686300811, "min": 10, "max": 50, "type": "float"}

    # Calculate weighted pipeline inventory with discounting
    weighted_pipeline = sum(p * (pipeline_weight ** i) for i, p in enumerate(pipeline_orders))

    # Effective inventory position
    inventory_position = on_hand_inventory * inventory_weight + weighted_pipeline

    # Dynamic target based on demand estimate and safety stock
    target_inventory = base_stock + safety_stock * smoothing_factor

    # Order up to target
    order_amount = max(0, target_inventory - inventory_position)

    # Apply order multiplier and ensure minimum order size
    order_amount = order_amount * order_multiplier
    order_amount = max(order_amount, min_order)

    # Reasonable upper bound based on demand estimate
    order_amount = min(order_amount, demand_estimate * 1.5)

    # Ensure integer order quantity
    return order_amount
