# policy_hash: 61cd2a7ec148564ec17b1a94d57a0e9b7323b8b17fea261ddc42312e8569bb7a
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L6_c1_2
# matched_train_cells: 5
# source_prompt_files: 1
# best_target_performance: 6236.59
# best_prompt_performance: 6236.59
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_053256.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 379.3981684249439  # OPT_PARAM: {"initial": 379.3981684249439, "min": 200, "max": 600, "type": "float"}
    pipeline_weight = 0.8  # OPT_PARAM: {"initial": 0.8, "min": 0.8, "max": 1.2, "type": "float"}
    smoothing_factor = 0.2747355817094915  # OPT_PARAM: {"initial": 0.2747355817094915, "min": 0.1, "max": 1.0, "type": "float"}
    safety_stock = 49.398168424943776  # OPT_PARAM: {"initial": 49.398168424943776, "min": 20, "max": 150, "type": "float"}

    # Calculate effective pipeline with weight
    effective_pipeline = sum(pipeline_orders) * pipeline_weight

    # Calculate inventory position
    inventory_position = on_hand_inventory + effective_pipeline

    # Calculate target inventory level with safety stock adjustment
    target_level = base_stock + safety_stock

    # Calculate raw order amount
    raw_order = max(0, target_level - inventory_position)

    # Apply smoothing to reduce order volatility
    if raw_order > 0:
        order_amount = smoothing_factor * raw_order
    else:
        order_amount = 0

    # Round to nearest integer
    return order_amount
