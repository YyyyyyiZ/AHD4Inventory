# policy_hash: 6e9fada6c14e705608696a27a0ce5c86fe9382790ec0a7a8fe7f764c3f8ec0d5
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L6_c1_2
# matched_train_cells: 1
# source_prompt_files: 1
# best_target_performance: 6167.66
# best_prompt_performance: 6167.5
# best_rel_error_pct: 0.002594
# example_source_txt: examples/inventory/deepseek-chat_exponential_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251218_092800.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 421.3010860762741  # OPT_PARAM: {"initial": 421.3010860762741, "min": 350, "max": 550, "type": "float"}
    pipeline_weight = 0.7988108787821231  # OPT_PARAM: {"initial": 0.7988108787821231, "min": 0.7, "max": 1.0, "type": "float"}
    smoothing_factor = 0.21587391918810717  # OPT_PARAM: {"initial": 0.21587391918810717, "min": 0.15, "max": 0.4, "type": "float"}
    safety_stock = 61.30108607627435  # OPT_PARAM: {"initial": 61.30108607627435, "min": 40, "max": 100, "type": "float"}
    min_order_threshold = 15.0  # OPT_PARAM: {"initial": 15.0, "min": 5, "max": 30, "type": "float"}

    # Calculate effective inventory position with full pipeline consideration
    effective_pipeline = sum(pipeline_orders) * pipeline_weight
    inventory_position = on_hand_inventory + effective_pipeline

    # Calculate target inventory level
    target_inventory = base_stock + safety_stock

    # Calculate raw order amount
    raw_order = max(0, target_inventory - inventory_position)

    # Apply smoothing with minimum order threshold
    if raw_order > min_order_threshold:
        order_amount = int(raw_order * smoothing_factor + 0.5)
    else:
        order_amount = 0

    return order_amount
