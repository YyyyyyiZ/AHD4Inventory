# policy_hash: 232fde3a07bd79f63bb5ae8b498e110195b495edf824ec77bc972da1c7ca74db
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L6_c1_2
# matched_train_cells: 6
# source_prompt_files: 2
# best_target_performance: 6574.54
# best_prompt_performance: 6576.08
# best_rel_error_pct: 0.023424
# example_source_txt: examples/inventory/deepseek-chat_exponential_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251222_041224.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 284.76555549482833  # OPT_PARAM: {"initial": 284.76555549482833, "min": 200, "max": 350, "type": "float"}
    safety_stock = 44.81724910048894  # OPT_PARAM: {"initial": 44.81724910048894, "min": 30, "max": 70, "type": "float"}
    pipeline_factor = 0.05  # OPT_PARAM: {"initial": 0.05, "min": 0.05, "max": 0.3, "type": "float"}
    demand_forecast_factor = 0.848323727054424  # OPT_PARAM: {"initial": 0.848323727054424, "min": 0.6, "max": 1.1, "type": "float"}
    max_order_multiplier = 1.7440990151866707  # OPT_PARAM: {"initial": 1.7440990151866707, "min": 1.2, "max": 3.0, "type": "float"}
    recent_weight = 0.700000000000005  # OPT_PARAM: {"initial": 0.700000000000005, "min": 0.5, "max": 0.9, "type": "float"}

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
