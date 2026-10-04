# policy_hash: dfb85e4bf43a74123a3b48aae940e0cb6bb537b27aa8116dba37d13a0f81c015
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std50_L6_c1_2
# matched_train_cells: 1
# source_prompt_files: 1
# best_target_performance: 4732.26
# best_prompt_performance: 4726.08
# best_rel_error_pct: 0.130593
# example_source_txt: examples/inventory/deepseek-chat_normal_std50_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251217_010922.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 524.7747443231798  # OPT_PARAM: {"initial": 524.7747443231798, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 41.02261505213607  # OPT_PARAM: {"initial": 41.02261505213607, "min": 0, "max": 200, "type": "float"}
    lead_time = 6
    forecast_horizon = 3  # OPT_PARAM: {"initial": 3, "min": 1, "max": 10, "type": "int"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand during lead time
    # Use average of recent pipeline arrivals as demand estimate
    if len(pipeline_orders) > 0:
        recent_arrivals = pipeline_orders[:min(forecast_horizon, len(pipeline_orders))]
        demand_estimate = sum(recent_arrivals) / len(recent_arrivals)
    else:
        demand_estimate = 0

    # Adjust base stock based on demand variability
    adjusted_base_stock = base_stock + safety_stock * demand_estimate / 100

    # Calculate order-up-to level
    order_up_to = max(0, adjusted_base_stock - inventory_position)

    # Apply smoothing to avoid extreme order fluctuations
    smoothing_factor = 0.40577661411783583  # OPT_PARAM: {"initial": 0.40577661411783583, "min": 0.1, "max": 1.0, "type": "float"}

    # If we have pipeline orders, consider the next arrival
    if len(pipeline_orders) > 0:
        next_arrival = pipeline_orders[0]
        # Reduce order if next arrival is substantial
        if next_arrival > demand_estimate * 2:
            reduction_factor = 0.8530187250704108  # OPT_PARAM: {"initial": 0.8530187250704108, "min": 0.5, "max": 1.0, "type": "float"}
            order_up_to *= reduction_factor

    # Ensure order is non-negative and integer
    order_amount = max(0, int(order_up_to * smoothing_factor))

    return order_amount
