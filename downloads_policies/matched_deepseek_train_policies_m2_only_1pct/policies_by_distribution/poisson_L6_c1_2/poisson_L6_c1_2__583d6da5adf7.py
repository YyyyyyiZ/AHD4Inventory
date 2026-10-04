# policy_hash: 583d6da5adf747f1ab03aed7bca2f1cfe786a3818774f919b512310323b40ecc
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L6_c1_2
# matched_train_cells: 13
# source_prompt_files: 1
# best_target_performance: 2505.44
# best_prompt_performance: 2503.81
# best_rel_error_pct: 0.065058
# example_source_txt: examples/inventory/deepseek-chat_poisson_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251222_015921.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 688.241185680014  # OPT_PARAM: {"initial": 688.241185680014, "min": 400, "max": 700, "type": "float"}
    safety_stock = 50.0  # OPT_PARAM: {"initial": 50.0, "min": 0, "max": 50, "type": "float"}
    pipeline_adjustment = 1.0  # OPT_PARAM: {"initial": 1.0, "min": 0.9, "max": 1.2, "type": "float"}
    smoothing_factor = 0.5  # OPT_PARAM: {"initial": 0.5, "min": 0.5, "max": 1.0, "type": "float"}

    # Calculate effective pipeline with adjustment
    effective_pipeline = sum(pipeline_orders) * pipeline_adjustment

    # Calculate target inventory position
    target_inventory = base_stock + safety_stock

    # Calculate inventory position
    inventory_position = on_hand_inventory + effective_pipeline

    # Calculate raw order amount
    raw_order = max(0, target_inventory - inventory_position)

    # Apply smoothing to reduce order volatility
    order_amount = smoothing_factor * raw_order

    # Round to nearest integer
    return order_amount
