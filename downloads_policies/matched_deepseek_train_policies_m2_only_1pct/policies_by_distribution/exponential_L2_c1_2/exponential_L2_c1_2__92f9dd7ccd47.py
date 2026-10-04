# policy_hash: 92f9dd7ccd47431d6d25be9325162f749b2732fa5d0663db1aaf0727c10257f4
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L2_c1_2
# matched_train_cells: 8
# source_prompt_files: 1
# best_target_performance: 5896.16
# best_prompt_performance: 5896.16
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L2_c1_2_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251217_223742.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 177.10791252426304  # OPT_PARAM: {"initial": 177.10791252426304, "min": 50, "max": 400, "type": "float"}
    safety_factor = 1.5991841023659612  # OPT_PARAM: {"initial": 1.5991841023659612, "min": 0.5, "max": 3.0, "type": "float"}
    demand_smoothing = 0.39648304537032253  # OPT_PARAM: {"initial": 0.39648304537032253, "min": 0.1, "max": 0.9, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Estimate demand variability from pipeline orders
    if len(pipeline_orders) >= 2:
        # Use standard deviation of pipeline orders as demand variability proxy
        mean_pipeline = sum(pipeline_orders) / len(pipeline_orders)
        variance = sum((p - mean_pipeline) ** 2 for p in pipeline_orders) / len(pipeline_orders)
        std_dev = variance ** 0.5
    else:
        std_dev = base_stock * 0.3

    # Dynamic safety stock based on demand variability
    dynamic_safety = safety_factor * std_dev

    # Adjust target based on current pipeline status
    # If pipeline is low, be more aggressive; if high, be conservative
    pipeline_ratio = sum(pipeline_orders) / (base_stock * len(pipeline_orders)) if base_stock > 0 else 1.0
    pipeline_adjustment = (1.0 - pipeline_ratio) * base_stock * 0.2

    # Calculate target inventory position
    target_inventory = base_stock + dynamic_safety + pipeline_adjustment

    # Smooth ordering to avoid extreme fluctuations
    order_needed = target_inventory - inventory_position
    if abs(order_needed) > base_stock * 0.5:
        # Large adjustments: smooth them
        smoothed_order = order_needed * demand_smoothing
    else:
        smoothed_order = order_needed

    # Ensure non-negative integer order
    order_amount = max(0, int(round(smoothed_order)))

    return order_amount
