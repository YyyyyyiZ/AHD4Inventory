# policy_hash: 3c1965257436a02b3cddde34f3249c2718d7d1b97134c5d7ea6112f924acc837
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L2_c1_5
# matched_train_cells: 6
# source_prompt_files: 1
# best_target_performance: 1222.8
# best_prompt_performance: 1222.8
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L2_c1_5_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_032431.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 270.2748562431627  # OPT_PARAM: {"initial": 270.2748562431627, "min": 200, "max": 350, "type": "float"}
    safety_stock = 22.644349793096993  # OPT_PARAM: {"initial": 22.644349793096993, "min": 5, "max": 40, "type": "float"}
    demand_estimate = 99.31426612818656  # OPT_PARAM: {"initial": 99.31426612818656, "min": 90, "max": 110, "type": "float"}
    pipeline_weight = 0.0  # OPT_PARAM: {"initial": 0.0, "min": 0.0, "max": 0.5, "type": "float"}
    smoothing_factor = 0.11  # OPT_PARAM: {"initial": 0.11, "min": 0.01, "max": 0.3, "type": "float"}
    threshold_factor = 0.8  # OPT_PARAM: {"initial": 0.8, "min": 0.5, "max": 1.2, "type": "float"}
    pipeline_lookback = 1  # OPT_PARAM: {"initial": 1, "min": 0, "max": 2, "type": "int"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate target inventory level
    target_level = base_stock + safety_stock

    # Base order amount from base-stock policy
    base_order = max(0, target_level - inventory_position)

    # Pipeline adjustment with threshold - only consider recent pipeline orders
    if len(pipeline_orders) > 0 and pipeline_lookback > 0:
        recent_pipeline = sum(pipeline_orders[-pipeline_lookback:]) if pipeline_lookback <= len(pipeline_orders) else sum(pipeline_orders)
        expected_recent = demand_estimate * min(pipeline_lookback, len(pipeline_orders))

        # Only adjust if recent pipeline is below expected
        if recent_pipeline < threshold_factor * expected_recent:
            pipeline_deficit = max(0, expected_recent - recent_pipeline)
            base_order += pipeline_weight * pipeline_deficit

    # Apply smoothing
    order_amount = smoothing_factor * base_order + (1 - smoothing_factor) * demand_estimate

    # Ensure non-negative integer order
    order_amount = max(0, int(round(order_amount)))

    return order_amount
