# policy_hash: 17dc6ea13fb7a0ba37dd1852ab8176cb5f1e2f0f599f8273ffbc13d4636f8adb
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L6_c1_5
# matched_train_cells: 8
# source_prompt_files: 1
# best_target_performance: 2887.29
# best_prompt_performance: 2890.15
# best_rel_error_pct: 0.099055
# example_source_txt: examples/inventory/deepseek-chat_poisson_L6_c1_5_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_055436.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 739.0681368425719  # OPT_PARAM: {"initial": 739.0681368425719, "min": 500, "max": 800, "type": "float"}
    safety_stock = 180.0  # OPT_PARAM: {"initial": 180.0, "min": 80, "max": 180, "type": "float"}
    smoothing_factor = 0.3  # OPT_PARAM: {"initial": 0.3, "min": 0.3, "max": 0.7, "type": "float"}
    demand_forecast_factor = 0.5  # OPT_PARAM: {"initial": 0.5, "min": 0.5, "max": 1.0, "type": "float"}
    min_order_threshold = 27.731671164263606  # OPT_PARAM: {"initial": 27.731671164263606, "min": 10, "max": 50, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Better demand forecast using all pipeline orders (weighted average)
    # More weight to recent orders
    if pipeline_orders:
        weights = [0.1, 0.15, 0.2, 0.25, 0.3]  # Fixed weights, not optimized
        weighted_sum = 0
        total_weight = 0
        for i, order in enumerate(pipeline_orders[:5]):  # Use up to 5 most recent
            weight = weights[i] if i < len(weights) else 0.1
            weighted_sum += order * weight
            total_weight += weight
        avg_forecast_demand = weighted_sum / total_weight if total_weight > 0 else 100.0
    else:
        avg_forecast_demand = 100.0

    # Adjust base stock based on demand forecast
    adjusted_base_stock = base_stock + demand_forecast_factor * (avg_forecast_demand - 100.0)

    # Calculate target inventory level
    target_inventory = adjusted_base_stock + safety_stock

    # Smooth ordering
    raw_order = smoothing_factor * (target_inventory - inventory_position)

    # Apply minimum order threshold
    if raw_order > 0 and raw_order < min_order_threshold:
        order_amount = min_order_threshold
    else:
        order_amount = max(0, raw_order)

    # Round to nearest integer
    return order_amount
