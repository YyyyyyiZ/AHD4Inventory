# policy_hash: 501cecba68300a9981276c0a22aa241b6b4bb2fa4840625d25f450388cd22498
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std50_L6_c1_2
# matched_train_cells: 2
# source_prompt_files: 1
# best_target_performance: 4364.46
# best_prompt_performance: 4362.56
# best_rel_error_pct: 0.043533
# example_source_txt: examples/inventory/deepseek-chat_normal_std50_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251216_231331.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 511.6533760992128  # OPT_PARAM: {"initial": 511.6533760992128, "min": 400, "max": 700, "type": "float"}
    safety_stock = 56.427137610235654  # OPT_PARAM: {"initial": 56.427137610235654, "min": 20, "max": 150, "type": "float"}
    adjustment_factor = 0.3  # OPT_PARAM: {"initial": 0.3, "min": 0.3, "max": 1.0, "type": "float"}
    pipeline_weight = 0.01  # OPT_PARAM: {"initial": 0.01, "min": 0.01, "max": 0.3, "type": "float"}
    demand_buffer = 1.3960231807428434  # OPT_PARAM: {"initial": 1.3960231807428434, "min": 1.0, "max": 1.5, "type": "float"}
    min_order_size = 15.0  # OPT_PARAM: {"initial": 15.0, "min": 10, "max": 50, "type": "float"}
    safety_multiplier = 0.01  # OPT_PARAM: {"initial": 0.01, "min": 0.01, "max": 1.0, "type": "float"}
    lost_sales_weight = 0.9792161305986202  # OPT_PARAM: {"initial": 0.9792161305986202, "min": 0.1, "max": 2.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate base order using base-stock policy with lost-sales weighting
    base_order = max(0, base_stock * demand_buffer * lost_sales_weight - inventory_position)

    # Calculate pipeline adjustment - focus on smoothing
    if len(pipeline_orders) >= 2:
        # Use weighted average of recent pipeline (more weight on recent)
        recent_weights = [0.3, 0.7] if len(pipeline_orders) >= 2 else [1.0]
        recent_orders = pipeline_orders[-len(recent_weights):]
        weighted_avg = sum(w * o for w, o in zip(recent_weights, recent_orders)) / sum(recent_weights)

        if weighted_avg > 0:
            # Smoother adjustment based on trend
            trend = pipeline_orders[-1] / weighted_avg
            pipeline_adjustment = 1.0 + (trend - 1.0) * pipeline_weight
            pipeline_adjustment = max(0.9, min(1.1, pipeline_adjustment))
        else:
            pipeline_adjustment = 1.0
    else:
        pipeline_adjustment = 1.0

    # Calculate safety stock adjustment - more conservative
    safety_adjustment = 0
    if on_hand_inventory < safety_stock:
        deficit = safety_stock - on_hand_inventory
        safety_adjustment = deficit * safety_multiplier

    # Combine adjustments with higher adjustment factor
    adjusted_order = base_order * pipeline_adjustment * adjustment_factor + safety_adjustment

    # Ensure minimum order size when inventory is low
    if on_hand_inventory < safety_stock and adjusted_order < min_order_size:
        adjusted_order = min_order_size

    # Round to nearest integer
    order_amount = int(round(adjusted_order))

    return order_amount
