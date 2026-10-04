# policy_hash: b9052bb310b38b49bbddd6b65fa25de92094f7f49f13c832e6ce9e094f876e82
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std10_L2_c1_5
# matched_train_cells: 23
# source_prompt_files: 1
# best_target_performance: 1356.86
# best_prompt_performance: 1356.86
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_normal_std10_L2_c1_5_50_plain_processed_scipy_15_default_m2_2_r7/prompt_for_code/m2_20260129_055016.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 307.87458775882396  # OPT_PARAM: {"initial": 307.87458775882396, "min": 10, "max": 1000, "type": "float"}
    adjustment_factor = 0.819260608612017  # OPT_PARAM: {"initial": 0.819260608612017, "min": 0.1, "max": 2.0, "type": "float"}
    safety_stock = 14.913863119645121  # OPT_PARAM: {"initial": 14.913863119645121, "min": 0, "max": 100, "type": "float"}

    # Calculate current inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate target order amount with adjustment
    target_order = max(0, base_stock - inventory_position)

    # Apply adjustment factor to smooth ordering
    adjusted_order = target_order * adjustment_factor

    # Add safety stock component based on pipeline variability
    pipeline_variability = max(pipeline_orders) - min(pipeline_orders) if len(pipeline_orders) > 1 else 0
    safety_component = safety_stock * (1 + pipeline_variability / 100)

    # Final order amount
    order_amount = max(0, adjusted_order + safety_component)

    return order_amount
