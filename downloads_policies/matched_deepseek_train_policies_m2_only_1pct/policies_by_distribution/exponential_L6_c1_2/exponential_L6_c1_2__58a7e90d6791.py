# policy_hash: 58a7e90d6791cc82677c8568ea7df3cd62a52b0b5ccaf854e74f8f0cfc8278d9
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L6_c1_2
# matched_train_cells: 6
# source_prompt_files: 1
# best_target_performance: 6232.34
# best_prompt_performance: 6232.34
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251218_014107.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 454.2116080470191  # OPT_PARAM: {"initial": 454.2116080470191, "min": 100, "max": 800, "type": "float"}
    pipeline_weight = 0.7675875177158725  # OPT_PARAM: {"initial": 0.7675875177158725, "min": 0.5, "max": 1.2, "type": "float"}
    smoothing_factor = 0.3  # OPT_PARAM: {"initial": 0.3, "min": 0.3, "max": 1.0, "type": "float"}

    # Calculate weighted pipeline inventory
    weighted_pipeline = sum(pipeline_orders) * pipeline_weight

    # Calculate inventory position
    inventory_position = on_hand_inventory + weighted_pipeline

    # Calculate desired order
    desired_order = max(0, base_stock - inventory_position)

    # Apply smoothing to reduce order volatility
    if desired_order > 0:
        order_amount = int(desired_order * smoothing_factor)
    else:
        order_amount = 0

    return order_amount
