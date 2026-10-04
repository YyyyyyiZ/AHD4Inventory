# policy_hash: a9206a93990769763fab2180fcd2acdcf5fc3ed7e74a4978b587c25b60634741
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L2_c1_5
# matched_train_cells: 22
# source_prompt_files: 1
# best_target_performance: 1219.76
# best_prompt_performance: 1219.76
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L2_c1_5_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_031828.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 251.495422602024  # OPT_PARAM: {"initial": 251.495422602024, "min": 100, "max": 400, "type": "float"}
    safety_stock = 30.69495840085473  # OPT_PARAM: {"initial": 30.69495840085473, "min": 0, "max": 100, "type": "float"}
    demand_estimate = 100.18940155601692  # OPT_PARAM: {"initial": 100.18940155601692, "min": 80, "max": 120, "type": "float"}
    pipeline_threshold = 0.7999999999999999  # OPT_PARAM: {"initial": 0.7999999999999999, "min": 0.7, "max": 1.0, "type": "float"}
    pipeline_adjustment = 0.05  # OPT_PARAM: {"initial": 0.05, "min": 0.05, "max": 0.4, "type": "float"}
    order_smoothing = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 0.9, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate target inventory level
    target_level = base_stock + safety_stock

    # Base order amount
    base_order = max(0, target_level - inventory_position)

    # Add demand anticipation for pipeline smoothing
    if len(pipeline_orders) > 0:
        expected_pipeline = demand_estimate * len(pipeline_orders)
        current_pipeline = sum(pipeline_orders)
        if current_pipeline < expected_pipeline * pipeline_threshold:
            base_order += pipeline_adjustment * (expected_pipeline - current_pipeline)

    # Apply smoothing to avoid large order fluctuations
    order_amount = order_smoothing * base_order + (1 - order_smoothing) * demand_estimate

    # Ensure non-negative integer order
    order_amount = max(0, int(round(order_amount)))

    return order_amount
