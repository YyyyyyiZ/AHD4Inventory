# policy_hash: d938180728ce433f70cf1287b21e383d8183510b20dcbad343fccd4cbac7b448
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std10_L6_c1_5
# matched_train_cells: 15
# source_prompt_files: 1
# best_target_performance: 3395.56
# best_prompt_performance: 3394.82
# best_rel_error_pct: 0.021793
# example_source_txt: examples/inventory/deepseek-chat_normal_std10_L6_c1_5_50_plain_processed_scipy_15_default_m2_2_r8/prompt_for_code/m2_20260128_083054.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 633.8768382249165  # OPT_PARAM: {"initial": 633.8768382249165, "min": 550, "max": 700, "type": "float"}
    safety_stock = 46.76038655175572  # OPT_PARAM: {"initial": 46.76038655175572, "min": 30, "max": 60, "type": "float"}
    pipeline_weight = 1.0  # OPT_PARAM: {"initial": 1.0, "min": 0.8, "max": 1.0, "type": "float"}
    demand_buffer = 16.167348912327103  # OPT_PARAM: {"initial": 16.167348912327103, "min": 5, "max": 25, "type": "float"}
    pipeline_threshold = 97.5322207970119  # OPT_PARAM: {"initial": 97.5322207970119, "min": 80, "max": 120, "type": "float"}
    adjustment_strength = 0.9543026532984894  # OPT_PARAM: {"initial": 0.9543026532984894, "min": 0.5, "max": 1.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate average pipeline order
    if pipeline_orders:
        avg_pipeline = sum(pipeline_orders) / len(pipeline_orders)
    else:
        avg_pipeline = 0

    # Adjust base stock based on pipeline level
    if avg_pipeline > pipeline_threshold:
        adjustment = pipeline_weight * adjustment_strength
    else:
        adjustment = 1.0

    # Target inventory position
    target_position = base_stock + safety_stock + demand_buffer

    # Calculate order amount with adjustment
    order_amount = max(0, (target_position - inventory_position) * adjustment)

    # Round to nearest integer
    return order_amount
