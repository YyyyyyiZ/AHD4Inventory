# policy_hash: c033345000cf69c902884706c303af9237c42098a07e9e7d8b09226929d9d953
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std10_L2_c1_2
# matched_train_cells: 3
# source_prompt_files: 1
# best_target_performance: 1008.14
# best_prompt_performance: 1016.46
# best_rel_error_pct: 0.825282
# example_source_txt: examples/inventory/deepseek-chat_normal_std10_L2_c1_2_50_plain_processed_scipy_15_default_m2_2_r7/prompt_for_code/m2_20260129_200848.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 296.00009215267625  # OPT_PARAM: {"initial": 296.00009215267625, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 50.1  # OPT_PARAM: {"initial": 50.1, "min": 0, "max": 200, "type": "float"}
    adjustment_factor = 0.9563022472164189  # OPT_PARAM: {"initial": 0.9563022472164189, "min": 0.1, "max": 1.5, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Adjust base stock based on pipeline variability
    pipeline_sum = sum(pipeline_orders)
    if len(pipeline_orders) > 0:
        avg_pipeline = pipeline_sum / len(pipeline_orders)
        pipeline_variability = max(0, pipeline_sum - avg_pipeline * len(pipeline_orders))
        adjusted_base = base_stock + safety_stock * (pipeline_variability / (avg_pipeline + 1))
    else:
        adjusted_base = base_stock + safety_stock

    # Calculate order amount with adjustment
    raw_order = max(0, adjusted_base - inventory_position)
    order_amount = int(round(raw_order * adjustment_factor))

    return order_amount
