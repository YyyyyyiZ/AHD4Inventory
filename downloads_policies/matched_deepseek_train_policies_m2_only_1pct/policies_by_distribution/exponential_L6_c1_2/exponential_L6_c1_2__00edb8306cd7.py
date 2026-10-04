# policy_hash: 00edb8306cd7e8a80376aef23e6ce6f604e0e42c2952a321d8ca5a0017c2b378
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L6_c1_2
# matched_train_cells: 12
# source_prompt_files: 1
# best_target_performance: 6094.18
# best_prompt_performance: 6094.84
# best_rel_error_pct: 0.010830
# example_source_txt: examples/inventory/deepseek-chat_exponential_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251222_043344.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 315.29647460133816  # OPT_PARAM: {"initial": 315.29647460133816, "min": 200, "max": 350, "type": "float"}
    safety_stock = 36.447011056750256  # OPT_PARAM: {"initial": 36.447011056750256, "min": 30, "max": 70, "type": "float"}
    pipeline_factor = 0.25  # OPT_PARAM: {"initial": 0.25, "min": 0.05, "max": 0.25, "type": "float"}
    demand_forecast_factor = 1.1  # OPT_PARAM: {"initial": 1.1, "min": 0.6, "max": 1.1, "type": "float"}
    max_order_multiplier = 1.2  # OPT_PARAM: {"initial": 1.2, "min": 1.2, "max": 3.0, "type": "float"}
    recent_weight_factor = 0.5  # OPT_PARAM: {"initial": 0.5, "min": 0.5, "max": 0.9, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Improved demand forecast using weighted average with emphasis on recent orders
    if len(pipeline_orders) >= 3:
        # Exponential weighting: most recent gets highest weight
        weights = [recent_weight_factor ** i for i in range(3)]
        weights = [w / sum(weights) for w in weights]  # Normalize
        recent_arrivals = pipeline_orders[:3]
        forecast_demand = sum(w * d for w, d in zip(weights, recent_arrivals)) * demand_forecast_factor
    else:
        forecast_demand = 0

    # Adjust base stock based on pipeline variability
    pipeline_sum = sum(pipeline_orders)
    if pipeline_sum > 0:
        pipeline_avg = pipeline_sum / len(pipeline_orders)
        pipeline_variability = sum(abs(p - pipeline_avg) for p in pipeline_orders) / pipeline_sum
        # More responsive adjustment for variability
        adjusted_base = base_stock * (1 + pipeline_variability * pipeline_factor)
    else:
        adjusted_base = base_stock

    # Target inventory with safety stock and forecast
    target_inventory = adjusted_base + safety_stock + forecast_demand

    # Calculate order amount
    order_amount = max(0, target_inventory - inventory_position)

    # Smarter order capping based on demand patterns
    if len(pipeline_orders) > 0:
        # Use weighted average of recent orders for capping
        if len(pipeline_orders) >= 3:
            recent_avg = sum(p * w for p, w in zip(pipeline_orders[:3], [0.5, 0.3, 0.2])) / 1.0
        else:
            recent_avg = sum(pipeline_orders) / len(pipeline_orders)

        max_order = max(recent_avg * max_order_multiplier, safety_stock * 1.5)
        order_amount = min(order_amount, max_order)

    # Round to nearest integer
    return order_amount
