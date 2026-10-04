# policy_hash: 1ddd19ee2f5379bffecb436251bb4d0d0cfad0f8b48df6d0aff3b16d816a35a9
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L4_c1_5
# matched_train_cells: 5
# source_prompt_files: 1
# best_target_performance: 2192.62
# best_prompt_performance: 2192.62
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L4_c1_5_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251218_002622.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 476.72922623304464  # OPT_PARAM: {"initial": 476.72922623304464, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 24.632621400214614  # OPT_PARAM: {"initial": 24.632621400214614, "min": 0, "max": 200, "type": "float"}
    pipeline_weight = 1.0040016800712157  # OPT_PARAM: {"initial": 1.0040016800712157, "min": 0.1, "max": 1.5, "type": "float"}

    # Calculate effective pipeline with weighted future arrivals
    weighted_pipeline = sum(p * (pipeline_weight ** i) for i, p in enumerate(pipeline_orders))

    # Calculate inventory position with weighted adjustment
    inventory_position = on_hand_inventory + weighted_pipeline

    # Base order-up-to level with safety stock adjustment
    target_level = base_stock + safety_stock

    # Calculate order amount with smoothing
    order_amount = max(0, target_level - inventory_position)

    # Apply rounding to integer (maintains stationarity)
    return order_amount
