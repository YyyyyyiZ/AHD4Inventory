# policy_hash: f8e5a1026402e2112342ef849df1550ba1ecd5ae9918d399ad37de445c877923
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L6_c1_2
# matched_train_cells: 9
# source_prompt_files: 1
# best_target_performance: 6120.39
# best_prompt_performance: 6120.39
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_053206.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 437.8823192852477  # OPT_PARAM: {"initial": 437.8823192852477, "min": 100, "max": 800, "type": "float"}
    safety_stock = 67.88231928524431  # OPT_PARAM: {"initial": 67.88231928524431, "min": 20, "max": 200, "type": "float"}
    pipeline_weight = 0.708040278951441  # OPT_PARAM: {"initial": 0.708040278951441, "min": 0.5, "max": 1.0, "type": "float"}
    smoothing_factor = 0.2  # OPT_PARAM: {"initial": 0.2, "min": 0.1, "max": 1.0, "type": "float"}
    min_order_threshold = 20  # OPT_PARAM: {"initial": 20, "min": 0, "max": 50, "type": "int"}

    # Calculate inventory position with weighted pipeline
    effective_pipeline = sum(pipeline_orders) * pipeline_weight
    inventory_position = on_hand_inventory + effective_pipeline

    # Simple base-stock policy with safety stock
    target_inventory = base_stock + safety_stock
    gap = target_inventory - inventory_position

    # Apply smoothing to order amount
    if gap > 0:
        order_amount = max(0, smoothing_factor * gap)
    else:
        order_amount = 0

    # Apply minimum order threshold
    if order_amount < min_order_threshold:
        order_amount = 0

    return order_amount
