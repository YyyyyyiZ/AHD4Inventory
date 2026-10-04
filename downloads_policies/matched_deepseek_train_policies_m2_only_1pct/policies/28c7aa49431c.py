# policy_hash: 28c7aa49431c5e11bacdd23b0b03cb6d42ed8abc80de0bfba31a5733b363a104
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L2_c1_2
# matched_train_cells: 5
# source_prompt_files: 1
# best_target_performance: 5878.32
# best_prompt_performance: 5878.22
# best_rel_error_pct: 0.001701
# example_source_txt: examples/inventory/deepseek-chat_exponential_L2_c1_2_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251217_225956.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 199.18099275622444  # OPT_PARAM: {"initial": 199.18099275622444, "min": 100, "max": 350, "type": "float"}
    safety_multiplier = 1.0624466822186556  # OPT_PARAM: {"initial": 1.0624466822186556, "min": 0.8, "max": 2.0, "type": "float"}
    pipeline_weight = 0.5633206658165418  # OPT_PARAM: {"initial": 0.5633206658165418, "min": 0.3, "max": 1.0, "type": "float"}
    smoothing_factor = 0.2621443269349227  # OPT_PARAM: {"initial": 0.2621443269349227, "min": 0.1, "max": 0.8, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Estimate demand variability from recent pipeline orders
    if len(pipeline_orders) >= 2:
        # Use coefficient of variation as demand variability measure
        mean_pipeline = sum(pipeline_orders) / len(pipeline_orders)
        if mean_pipeline > 0:
            variance = sum((p - mean_pipeline) ** 2 for p in pipeline_orders) / len(pipeline_orders)
            std_dev = variance ** 0.5
            cv = std_dev / mean_pipeline
        else:
            cv = 0.5
    else:
        cv = 0.5

    # Dynamic safety stock based on demand variability
    safety_stock = safety_multiplier * base_stock * cv

    # Adjust target based on pipeline status
    # Weight recent pipeline orders more heavily
    if len(pipeline_orders) > 0:
        recent_pipeline = pipeline_orders[-1] if len(pipeline_orders) > 0 else 0
        pipeline_adjustment = pipeline_weight * (base_stock - recent_pipeline)
    else:
        pipeline_adjustment = 0

    # Calculate target inventory position
    target_inventory = base_stock + safety_stock + pipeline_adjustment

    # Calculate order needed
    order_needed = target_inventory - inventory_position

    # Apply smoothing to avoid extreme fluctuations
    if abs(order_needed) > base_stock * 0.3:
        smoothed_order = order_needed * smoothing_factor
    else:
        smoothed_order = order_needed

    # Ensure non-negative integer order
    order_amount = max(0, int(round(smoothed_order)))

    return order_amount
