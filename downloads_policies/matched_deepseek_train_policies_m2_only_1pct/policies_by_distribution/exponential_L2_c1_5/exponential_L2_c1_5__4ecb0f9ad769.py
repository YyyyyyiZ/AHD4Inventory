# policy_hash: 4ecb0f9ad76906fa84a02a5a86fa8016ffcb36702411697b622edf3b34f219f1
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L2_c1_5
# matched_train_cells: 3
# source_prompt_files: 1
# best_target_performance: 11369.9
# best_prompt_performance: 11369.9
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L2_c1_5_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_031230.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 324.93124999998804  # OPT_PARAM: {"initial": 324.93124999998804, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 50.0  # OPT_PARAM: {"initial": 50.0, "min": 0, "max": 200, "type": "float"}
    demand_forecast_factor = 0.8  # OPT_PARAM: {"initial": 0.8, "min": 0.1, "max": 2.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Adjust base stock based on pipeline composition
    # Give more weight to near-term arrivals
    weighted_pipeline = 0
    for i, qty in enumerate(pipeline_orders):
        weight = 1.0 / (i + 1)  # More weight to earlier arrivals
        weighted_pipeline += qty * weight

    # Adjust target based on pipeline distribution
    pipeline_adjustment = weighted_pipeline / max(1, sum(pipeline_orders)) if sum(pipeline_orders) > 0 else 1.0
    adjusted_base_stock = base_stock * (0.9 + 0.2 * pipeline_adjustment)  # OPT_PARAM: {"initial": 0.9, "min": 0.5, "max": 1.5, "type": "float"}

    # Calculate order amount with safety stock consideration
    target_inventory = adjusted_base_stock + safety_stock
    order_amount = max(0, target_inventory - inventory_position)

    # Apply smoothing to avoid extreme order fluctuations
    smoothing_factor = 0.7  # OPT_PARAM: {"initial": 0.7, "min": 0.1, "max": 1.0, "type": "float"}
    if pipeline_orders and len(pipeline_orders) > 0:
        # Consider recent order patterns
        recent_order_avg = sum(pipeline_orders[-2:]) / min(2, len(pipeline_orders))
        smoothed_order = smoothing_factor * order_amount + (1 - smoothing_factor) * recent_order_avg
        order_amount = max(0, smoothed_order)

    # Round to integer (as required by output type)
    return order_amount
