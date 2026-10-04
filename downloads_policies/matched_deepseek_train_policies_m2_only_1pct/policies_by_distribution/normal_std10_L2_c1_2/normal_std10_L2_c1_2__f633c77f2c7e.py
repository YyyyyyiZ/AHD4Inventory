# policy_hash: f633c77f2c7e470ae34c65a55efcbdd057a075165a43b30fd6f3f80588552f01
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std10_L2_c1_2
# matched_train_cells: 24
# source_prompt_files: 1
# best_target_performance: 737.3
# best_prompt_performance: 737.3
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_normal_std10_L2_c1_2_50_plain_processed_scipy_15_default_m2_2_r6/prompt_for_code/m2_20260129_195901.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 214.60189036094508  # OPT_PARAM: {"initial": 214.60189036094508, "min": 100, "max": 500, "type": "float"}
    safety_stock = 0.0  # OPT_PARAM: {"initial": 0.0, "min": 0, "max": 100, "type": "float"}
    demand_forecast_factor = 0.8  # OPT_PARAM: {"initial": 0.8, "min": 0.8, "max": 1.3, "type": "float"}
    pipeline_weight = 0.10000000000003632  # OPT_PARAM: {"initial": 0.10000000000003632, "min": 0.0, "max": 0.8, "type": "float"}
    order_smoothing = 0.03385108086965182  # OPT_PARAM: {"initial": 0.03385108086965182, "min": 0.0, "max": 1.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Estimate demand using weighted combination of historical average and pipeline arrivals
    # Historical average demand from the data is around 100
    hist_avg_demand = 100.0

    # Calculate demand from recent pipeline arrivals (if available)
    if len(pipeline_orders) > 0:
        recent_arrivals = [p for p in pipeline_orders if p > 0]
        if recent_arrivals:
            avg_pipeline_demand = sum(recent_arrivals) / len(recent_arrivals)
            # Blend historical average with pipeline-based estimate
            demand_estimate = (pipeline_weight * avg_pipeline_demand +
                             (1 - pipeline_weight) * hist_avg_demand)
        else:
            demand_estimate = hist_avg_demand
    else:
        demand_estimate = hist_avg_demand

    # Adjust base stock based on demand forecast
    adjusted_base_stock = base_stock * demand_forecast_factor * (demand_estimate / hist_avg_demand)

    # Calculate order-up-to level with safety stock
    order_up_to = adjusted_base_stock + safety_stock

    # Calculate raw order amount
    raw_order = max(0, order_up_to - inventory_position)

    # Apply smoothing to reduce order volatility
    smoothed_order = order_smoothing * raw_order + (1 - order_smoothing) * demand_estimate

    # Round to nearest integer
    order_amount = int(round(smoothed_order))

    return order_amount
