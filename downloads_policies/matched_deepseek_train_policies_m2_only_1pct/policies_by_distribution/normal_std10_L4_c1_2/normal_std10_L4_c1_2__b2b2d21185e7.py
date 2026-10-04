# policy_hash: b2b2d21185e71d9395792e262493f2355a3116c722d3293bcbdae948f8e522ef
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std10_L4_c1_2
# matched_train_cells: 34
# source_prompt_files: 1
# best_target_performance: 1053.83
# best_prompt_performance: 1053.83
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_normal_std10_L4_c1_2_50_plain_processed_scipy_15_default_m2_2_r7/prompt_for_code/m2_20260130_043701.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 473.8969607442134  # OPT_PARAM: {"initial": 473.8969607442134, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 42.81847688810107  # OPT_PARAM: {"initial": 42.81847688810107, "min": 0, "max": 200, "type": "float"}
    smoothing_factor = 0.05967671674757981  # OPT_PARAM: {"initial": 0.05967671674757981, "min": 0.0, "max": 1.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Adjust base stock based on pipeline variability
    pipeline_std = 0.0
    if len(pipeline_orders) > 1:
        mean_pipeline = sum(pipeline_orders) / len(pipeline_orders)
        pipeline_std = (sum((q - mean_pipeline) ** 2 for q in pipeline_orders) / len(pipeline_orders)) ** 0.5

    adjusted_base_stock = base_stock + safety_stock * (pipeline_std / 100.0)

    # Calculate order amount with smoothing
    raw_order = max(0, adjusted_base_stock - inventory_position)
    order_amount = smoothing_factor * raw_order + (1 - smoothing_factor) * pipeline_orders[-1] if pipeline_orders else raw_order

    return order_amount
