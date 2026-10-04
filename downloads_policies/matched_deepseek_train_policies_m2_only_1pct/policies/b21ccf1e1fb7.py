# policy_hash: b21ccf1e1fb70b17398758b2a8d170c5c745e0c7970623be7aab316a7d3bfdc9
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L6_c1_2
# matched_train_cells: 1
# source_prompt_files: 1
# best_target_performance: 6561.65
# best_prompt_performance: 6559.73
# best_rel_error_pct: 0.029261
# example_source_txt: examples/inventory/deepseek-chat_exponential_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251222_043331.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 250.04041526740224  # OPT_PARAM: {"initial": 250.04041526740224, "min": 180, "max": 320, "type": "float"}
    safety_stock = 55.043835172317465  # OPT_PARAM: {"initial": 55.043835172317465, "min": 40, "max": 80, "type": "float"}
    pipeline_factor = 0.05174299634046744  # OPT_PARAM: {"initial": 0.05174299634046744, "min": 0.05, "max": 0.3, "type": "float"}
    demand_forecast_factor = 0.9379491708598552  # OPT_PARAM: {"initial": 0.9379491708598552, "min": 0.8, "max": 1.1, "type": "float"}
    max_order_multiplier = 1.6536721049192689  # OPT_PARAM: {"initial": 1.6536721049192689, "min": 1.2, "max": 2.5, "type": "float"}
    recent_weight = 0.65  # OPT_PARAM: {"initial": 0.65, "min": 0.5, "max": 0.9, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Improved demand forecast using exponential weighting of pipeline orders
    if len(pipeline_orders) >= 3:
        # Exponential weights: most recent gets highest weight
        weights = [recent_weight, recent_weight*0.5, recent_weight*0.25]
        # Normalize weights
        weight_sum = sum(weights)
        normalized_weights = [w/weight_sum for w in weights]
        recent_arrivals = pipeline_orders[:3]
        forecast_demand = sum(w * d for w, d in zip(normalized_weights, recent_arrivals)) * demand_forecast_factor
    else:
        forecast_demand = 0

    # Adjust base stock based on pipeline variability
    pipeline_sum = sum(pipeline_orders)
    if pipeline_sum > 0:
        pipeline_avg = pipeline_sum / len(pipeline_orders)
        pipeline_variability = sum(abs(p - pipeline_avg) for p in pipeline_orders) / pipeline_sum
        # Stronger adjustment for variability to better handle demand spikes
        adjusted_base = base_stock * (1 + pipeline_variability * pipeline_factor)
    else:
        adjusted_base = base_stock

    # Target inventory with safety stock and forecast
    target_inventory = adjusted_base + safety_stock + forecast_demand

    # Calculate order amount
    order_amount = max(0, target_inventory - inventory_position)

    # More conservative order capping
    if len(pipeline_orders) > 0:
        # Use weighted average of recent orders for capping
        if len(pipeline_orders) >= 3:
            avg_recent = sum(p * w for p, w in zip(pipeline_orders[:3], [0.5, 0.3, 0.2])) / 1.0
        else:
            avg_recent = sum(pipeline_orders) / len(pipeline_orders)

        max_order = avg_recent * max_order_multiplier if avg_recent > 0 else target_inventory * 0.5
        order_amount = min(order_amount, max_order)

    # Round to nearest integer
    return order_amount
