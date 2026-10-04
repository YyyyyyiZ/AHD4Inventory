# policy_hash: 573e97d41ead5000df4a746fa8e8cdeb82d089d20119cab17ddeee41813be85c
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std10_L2_c1_5
# matched_train_cells: 20
# source_prompt_files: 1
# best_target_performance: 1382.08
# best_prompt_performance: 1382.8
# best_rel_error_pct: 0.052095
# example_source_txt: examples/inventory/deepseek-chat_normal_std10_L2_c1_5_50_plain_processed_scipy_15_default_m2_2_r6/prompt_for_code/m2_20260129_231118.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 307.9999935374786  # OPT_PARAM: {"initial": 307.9999935374786, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 50.0  # OPT_PARAM: {"initial": 50.0, "min": 0, "max": 200, "type": "float"}
    adjustment_factor = 0.9757640127366946  # OPT_PARAM: {"initial": 0.9757640127366946, "min": 0.1, "max": 1.5, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Adjust base stock based on pipeline variability
    pipeline_sum = sum(pipeline_orders)
    if len(pipeline_orders) > 0:
        avg_pipeline = pipeline_sum / len(pipeline_orders)
        pipeline_variability = sum(abs(p - avg_pipeline) for p in pipeline_orders) / len(pipeline_orders)
        adjusted_base = base_stock + safety_stock * (pipeline_variability / 100.0)
    else:
        adjusted_base = base_stock

    # Calculate order amount with adjustment factor
    raw_order = max(0, adjusted_base - inventory_position)
    order_amount = int(round(raw_order * adjustment_factor))

    return order_amount
