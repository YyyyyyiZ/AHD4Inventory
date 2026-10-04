# policy_hash: 45eafa373b749d81e6c724166ef095a43caf3ff1c7feddc84c7e8795f6442c5b
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std50_L6_c1_2
# matched_train_cells: 42
# source_prompt_files: 1
# best_target_performance: 3806.13
# best_prompt_performance: 3806.13
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_normal_std50_L6_c1_2_50_plain_processed_scipy_15_default_m2_2_r6/prompt_for_code/m2_20260129_024057.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 698.5702410070919  # OPT_PARAM: {"initial": 698.5702410070919, "min": 300, "max": 700, "type": "float"}
    safety_stock = 198.80822543054816  # OPT_PARAM: {"initial": 198.80822543054816, "min": 20, "max": 200, "type": "float"}
    smoothing_factor = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 0.5, "type": "float"}
    demand_forecast_factor = 0.3  # OPT_PARAM: {"initial": 0.3, "min": 0.05, "max": 0.3, "type": "float"}
    lead_time_factor = 1.5  # OPT_PARAM: {"initial": 1.5, "min": 0.8, "max": 1.5, "type": "float"}
    pipeline_weight = 1.0  # OPT_PARAM: {"initial": 1.0, "min": 0.3, "max": 1.0, "type": "float"}
    min_order_threshold = 10.0  # OPT_PARAM: {"initial": 10.0, "min": 0, "max": 50, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Weighted pipeline average (emphasize recent orders more)
    L = len(pipeline_orders)
    if L > 0:
        weights = [pipeline_weight ** (L - i - 1) for i in range(L)]
        weighted_sum = sum(w * q for w, q in zip(weights, pipeline_orders))
        weight_total = sum(weights)
        avg_pipeline_order = weighted_sum / weight_total
    else:
        avg_pipeline_order = 0

    # Demand adjustment based on weighted pipeline average
    demand_adjustment = demand_forecast_factor * avg_pipeline_order

    # Adjusted base stock for lead time
    adjusted_base = base_stock * lead_time_factor

    # Target inventory calculation
    target_inventory = adjusted_base + safety_stock + demand_adjustment

    # Smoothing adjustment
    smoothed_target = smoothing_factor * target_inventory + (1 - smoothing_factor) * inventory_position

    # Calculate order amount
    order_amount = max(0, smoothed_target - inventory_position)

    # Apply minimum order threshold to reduce small orders
    if order_amount < min_order_threshold:
        order_amount = 0

    return order_amount
