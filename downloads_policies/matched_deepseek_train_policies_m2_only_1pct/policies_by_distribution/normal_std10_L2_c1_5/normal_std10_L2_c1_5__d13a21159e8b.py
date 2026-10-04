# policy_hash: d13a21159e8b176b4a32f5970802e8a8ca6551c1120cc1c4e41d557b426d5e0a
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std10_L2_c1_5
# matched_train_cells: 26
# source_prompt_files: 1
# best_target_performance: 1269.91
# best_prompt_performance: 1269.91
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_normal_std10_L2_c1_5_50_plain_processed_scipy_15_default_m2_2_r7/prompt_for_code/m2_20260129_061110.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 319.01298629142167  # OPT_PARAM: {"initial": 319.01298629142167, "min": 100, "max": 400, "type": "float"}
    adjustment_factor = 0.5  # OPT_PARAM: {"initial": 0.5, "min": 0.5, "max": 1.5, "type": "float"}
    safety_stock = 42.27643303655938  # OPT_PARAM: {"initial": 42.27643303655938, "min": 0, "max": 50, "type": "float"}
    pipeline_weight = 0.0  # OPT_PARAM: {"initial": 0.0, "min": 0.0, "max": 0.5, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected short-term demand based on pipeline variability
    # Use average of pipeline orders as indicator of recent demand pattern
    if len(pipeline_orders) > 0:
        avg_pipeline = sum(pipeline_orders) / len(pipeline_orders)
        pipeline_effect = max(0, avg_pipeline - on_hand_inventory) * pipeline_weight
    else:
        pipeline_effect = 0

    # Calculate target order
    target_order = max(0, base_stock - inventory_position)

    # Apply adjustment factor
    adjusted_order = target_order * adjustment_factor

    # Add safety stock and pipeline effect
    order_amount = max(0, adjusted_order + safety_stock + pipeline_effect)

    # Round to nearest integer (since demand is integer)
    return order_amount
