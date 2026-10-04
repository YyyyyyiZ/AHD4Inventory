# policy_hash: 57ac6c53c9bc857e8c9a84ae0ad8e0188e388099dd05d529e14d8535b618716b
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std10_L2_c1_5
# matched_train_cells: 9
# source_prompt_files: 1
# best_target_performance: 1347.86
# best_prompt_performance: 1347.86
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_normal_std10_L2_c1_5_50_plain_processed_scipy_15_default_m2_2_r6/prompt_for_code/m2_20260128_234744.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 276.1721366701965  # OPT_PARAM: {"initial": 276.1721366701965, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 28.837923260872827  # OPT_PARAM: {"initial": 28.837923260872827, "min": 0, "max": 200, "type": "float"}
    pipeline_weight = 1.0  # OPT_PARAM: {"initial": 1.0, "min": 0.0, "max": 1.0, "type": "float"}

    # Calculate effective inventory position with weighted pipeline
    weighted_pipeline = pipeline_weight * sum(pipeline_orders)
    effective_inventory = on_hand_inventory + weighted_pipeline

    # Calculate order amount with safety stock adjustment
    order_amount = max(0, base_stock - effective_inventory + safety_stock)

    # Apply smoothing to avoid extreme order fluctuations
    smoothing_factor = 0.5  # OPT_PARAM: {"initial": 0.5, "min": 0.5, "max": 1.0, "type": "float"}
    if pipeline_orders and len(pipeline_orders) > 0:
        recent_order = pipeline_orders[-1]
        smoothed_order = smoothing_factor * order_amount + (1 - smoothing_factor) * recent_order
        order_amount = max(0, smoothed_order)

    # Round to nearest integer (orders must be integer quantities)
    order_amount = int(round(order_amount))

    return order_amount
