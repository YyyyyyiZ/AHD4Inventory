# policy_hash: 664de29ebb86b4c01735a223e4e3d281f1013e4419cf09a330c064aa89c3ecde
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std10_L2_c1_2
# matched_train_cells: 33
# source_prompt_files: 1
# best_target_performance: 724.48
# best_prompt_performance: 724.48
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_normal_std10_L2_c1_2_50_plain_processed_scipy_15_default_m2_2_r6/prompt_for_code/m2_20260129_200243.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 182.60778938106398  # OPT_PARAM: {"initial": 182.60778938106398, "min": 100, "max": 300, "type": "float"}
    safety_stock = 17.607789381063828  # OPT_PARAM: {"initial": 17.607789381063828, "min": 0, "max": 50, "type": "float"}
    demand_forecast_factor = 1.0290481353104692  # OPT_PARAM: {"initial": 1.0290481353104692, "min": 0.9, "max": 1.2, "type": "float"}
    pipeline_weight = 0.01596833488919218  # OPT_PARAM: {"initial": 0.01596833488919218, "min": 0.0, "max": 0.3, "type": "float"}
    order_smoothing = 0.04658350582864791  # OPT_PARAM: {"initial": 0.04658350582864791, "min": 0.0, "max": 0.5, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Use historical average demand (calculated from data)
    hist_avg_demand = 100.0

    # Simple demand estimation using pipeline arrivals
    if len(pipeline_orders) > 0:
        recent_arrivals = [p for p in pipeline_orders if p > 0]
        if recent_arrivals:
            avg_pipeline_demand = sum(recent_arrivals) / len(recent_arrivals)
            # Blend with historical average
            demand_estimate = (pipeline_weight * avg_pipeline_demand +
                             (1 - pipeline_weight) * hist_avg_demand)
        else:
            demand_estimate = hist_avg_demand
    else:
        demand_estimate = hist_avg_demand

    # Adjust base stock
    adjusted_base_stock = base_stock * demand_forecast_factor

    # Calculate order-up-to level
    order_up_to = adjusted_base_stock + safety_stock

    # Calculate raw order amount
    raw_order = max(0, order_up_to - inventory_position)

    # Apply smoothing
    smoothed_order = order_smoothing * raw_order + (1 - order_smoothing) * demand_estimate

    # Round to nearest integer
    order_amount = int(round(smoothed_order))

    return order_amount
