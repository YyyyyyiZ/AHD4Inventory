# policy_hash: 85241e3919b2cddcf0ac59c6a4f815167691cc9b3734b2628ff25667d5b799fd
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L2_c1_5
# matched_train_cells: 24
# source_prompt_files: 1
# best_target_performance: 10427.65
# best_prompt_performance: 10427.65
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L2_c1_5_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_032228.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 260.9420981303434  # OPT_PARAM: {"initial": 260.9420981303434, "min": 100, "max": 500, "type": "float"}
    safety_stock = 55.94209813033789  # OPT_PARAM: {"initial": 55.94209813033789, "min": 20, "max": 150, "type": "float"}
    pipeline_weight_factor = 0.3  # OPT_PARAM: {"initial": 0.3, "min": 0.1, "max": 0.8, "type": "float"}
    smoothing_factor = 0.5  # OPT_PARAM: {"initial": 0.5, "min": 0.5, "max": 1.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Simple weighted pipeline adjustment
    weighted_pipeline = 0
    for i, qty in enumerate(pipeline_orders):
        weight = 1.0 / (i + 1)  # More weight to earlier arrivals
        weighted_pipeline += qty * weight

    # Normalize the weighted pipeline effect
    if sum(pipeline_orders) > 0:
        pipeline_ratio = weighted_pipeline / sum(pipeline_orders)
    else:
        pipeline_ratio = 1.0

    # Adjust target based on pipeline distribution
    pipeline_adjustment = 1.0 - pipeline_weight_factor * (1.0 - pipeline_ratio)
    adjusted_base_stock = base_stock * pipeline_adjustment

    # Calculate order amount with safety stock
    target_inventory = adjusted_base_stock + safety_stock
    order_amount = max(0, target_inventory - inventory_position)

    # Apply smoothing using recent pipeline orders
    if pipeline_orders:
        recent_orders = pipeline_orders[-2:] if len(pipeline_orders) >= 2 else pipeline_orders
        recent_avg = sum(recent_orders) / len(recent_orders)
        smoothed_order = smoothing_factor * order_amount + (1 - smoothing_factor) * recent_avg
        order_amount = max(0, smoothed_order)

    # Round to integer
    return order_amount
