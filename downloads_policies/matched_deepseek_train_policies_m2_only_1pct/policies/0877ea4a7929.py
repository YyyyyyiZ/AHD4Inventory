# policy_hash: 0877ea4a792902a3c5fb0b40c137f2413a7dfa2e1109a8e2d4c1db926599656e
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L6_c1_2
# matched_train_cells: 25
# source_prompt_files: 1
# best_target_performance: 6392.54
# best_prompt_performance: 6392.54
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251218_092505.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 358.44360246713956  # OPT_PARAM: {"initial": 358.44360246713956, "min": 100, "max": 800, "type": "float"}
    pipeline_weight = 0.7  # OPT_PARAM: {"initial": 0.7, "min": 0.7, "max": 1.0, "type": "float"}
    smoothing_factor = 0.4  # OPT_PARAM: {"initial": 0.4, "min": 0.4, "max": 1.0, "type": "float"}

    # Calculate inventory position with weighted pipeline
    effective_pipeline = sum(pipeline_orders) * pipeline_weight
    inventory_position = on_hand_inventory + effective_pipeline

    # Calculate raw order amount
    raw_order = max(0, base_stock - inventory_position)

    # Apply smoothing to avoid extreme fluctuations
    if raw_order > 0:
        order_amount = int(raw_order * smoothing_factor + 0.5)
    else:
        order_amount = 0

    return order_amount
