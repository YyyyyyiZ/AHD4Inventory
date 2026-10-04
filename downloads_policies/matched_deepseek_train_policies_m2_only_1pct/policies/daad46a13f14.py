# policy_hash: daad46a13f148df3fd21975c3ae4c8948568b56f58829d41702bf667dc159943
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L2_c1_2
# matched_train_cells: 2
# source_prompt_files: 1
# best_target_performance: 944.36
# best_prompt_performance: 944.36
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L2_c1_2_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_023236.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 308.89012569562163  # OPT_PARAM: {"initial": 308.89012569562163, "min": 200, "max": 400, "type": "float"}
    safety_stock = 44.76292052098738  # OPT_PARAM: {"initial": 44.76292052098738, "min": 0, "max": 100, "type": "float"}
    demand_forecast = 101.27357483204204  # OPT_PARAM: {"initial": 101.27357483204204, "min": 80, "max": 120, "type": "float"}
    pipeline_weight = 0.8616798021847736  # OPT_PARAM: {"initial": 0.8616798021847736, "min": 0.5, "max": 1.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected pipeline coverage
    expected_pipeline_coverage = demand_forecast * len(pipeline_orders)
    actual_pipeline_coverage = sum(pipeline_orders)

    # Adjust base stock based on pipeline status
    if expected_pipeline_coverage > 0:
        pipeline_adjustment = (actual_pipeline_coverage / expected_pipeline_coverage) * pipeline_weight
    else:
        pipeline_adjustment = 1.0

    # Calculate dynamic order-up-to level
    order_up_to = base_stock + safety_stock * pipeline_adjustment

    # Calculate order amount
    order_amount = max(0, order_up_to - inventory_position)

    # Apply demand-based smoothing
    smoothing_threshold = 1.386126109273568  # OPT_PARAM: {"initial": 1.386126109273568, "min": 1.0, "max": 2.5, "type": "float"}
    smoothing_factor = 0.636263270766323  # OPT_PARAM: {"initial": 0.636263270766323, "min": 0.5, "max": 0.9, "type": "float"}

    if order_amount > smoothing_threshold:
        order_amount = smoothing_factor * order_amount + (1 - smoothing_factor) * smoothing_threshold

    # Round to nearest integer
    order_amount = int(round(order_amount))

    return order_amount
