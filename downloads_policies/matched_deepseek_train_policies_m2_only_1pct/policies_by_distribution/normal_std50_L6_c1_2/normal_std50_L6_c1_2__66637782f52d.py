# policy_hash: 66637782f52d3dee1ead130c0a121a3b932523754a1383a35392431b34ec42d4
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std50_L6_c1_2
# matched_train_cells: 14
# source_prompt_files: 1
# best_target_performance: 5500.58
# best_prompt_performance: 5500.94
# best_rel_error_pct: 0.006545
# example_source_txt: examples/inventory/deepseek-chat_normal_std50_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251217_002743.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 526.7150563380181  # OPT_PARAM: {"initial": 526.7150563380181, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 42.762886196056456  # OPT_PARAM: {"initial": 42.762886196056456, "min": 0, "max": 200, "type": "float"}
    pipeline_weight = 1.1661459346606162  # OPT_PARAM: {"initial": 1.1661459346606162, "min": 0.1, "max": 1.5, "type": "float"}

    # Calculate effective inventory position
    effective_pipeline = sum(pipeline_orders) * pipeline_weight
    inventory_position = on_hand_inventory + effective_pipeline

    # Adjust base stock based on safety stock
    adjusted_base_stock = base_stock + safety_stock

    # Calculate order amount
    order_amount = max(0, adjusted_base_stock - inventory_position)

    # Apply smoothing to avoid extreme order fluctuations
    smoothing_factor = 0.83578234552405  # OPT_PARAM: {"initial": 0.83578234552405, "min": 0.3, "max": 1.0, "type": "float"}
    if len(pipeline_orders) > 0:
        recent_order = pipeline_orders[-1]
        smoothed_order = smoothing_factor * order_amount + (1 - smoothing_factor) * recent_order
        order_amount = max(0, smoothed_order)

    # Round to nearest integer (as required by output type)
    return order_amount
