# policy_hash: 5bfbca43dda13e4753a2bcb0792db7a939dda586fca9b27a83cbe48a36260733
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L2_c1_5
# matched_train_cells: 29
# source_prompt_files: 1
# best_target_performance: 1218.84
# best_prompt_performance: 1218.84
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L2_c1_5_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_032834.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 289.63235841693995  # OPT_PARAM: {"initial": 289.63235841693995, "min": 250, "max": 330, "type": "float"}
    safety_stock = 17.332358416939716  # OPT_PARAM: {"initial": 17.332358416939716, "min": 10, "max": 30, "type": "float"}
    demand_estimate = 97.33215122007937  # OPT_PARAM: {"initial": 97.33215122007937, "min": 95, "max": 105, "type": "float"}
    pipeline_weight = 0.12091617060693201  # OPT_PARAM: {"initial": 0.12091617060693201, "min": 0.1, "max": 0.4, "type": "float"}
    smoothing_factor = 0.10463372939335842  # OPT_PARAM: {"initial": 0.10463372939335842, "min": 0.05, "max": 0.25, "type": "float"}
    threshold_factor = 0.7785174885043613  # OPT_PARAM: {"initial": 0.7785174885043613, "min": 0.7, "max": 1.1, "type": "float"}
    pipeline_lookback = 2  # OPT_PARAM: {"initial": 2, "min": 1, "max": 2, "type": "int"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate target inventory level
    target_level = base_stock + safety_stock

    # Base order amount from base-stock policy
    base_order = max(0, target_level - inventory_position)

    # Pipeline adjustment - consider recent pipeline orders
    if len(pipeline_orders) > 0 and pipeline_lookback > 0:
        recent_pipeline = sum(pipeline_orders[-pipeline_lookback:]) if pipeline_lookback <= len(pipeline_orders) else sum(pipeline_orders)
        expected_recent = demand_estimate * min(pipeline_lookback, len(pipeline_orders))

        # Adjust if recent pipeline deviates from expected
        if recent_pipeline < threshold_factor * expected_recent:
            pipeline_deficit = max(0, expected_recent - recent_pipeline)
            base_order += pipeline_weight * pipeline_deficit
        elif recent_pipeline > (2 - threshold_factor) * expected_recent:
            pipeline_excess = max(0, recent_pipeline - expected_recent)
            base_order = max(0, base_order - pipeline_weight * pipeline_excess)

    # Apply smoothing
    order_amount = smoothing_factor * base_order + (1 - smoothing_factor) * demand_estimate

    # Ensure non-negative integer order
    order_amount = max(0, int(round(order_amount)))

    return order_amount
