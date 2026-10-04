# policy_hash: 9c801726e87bab294e208bca2772c8f57c2b3df15134a2230d4813b9470712e6
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L2_c1_5
# matched_train_cells: 30
# source_prompt_files: 1
# best_target_performance: 10478.22
# best_prompt_performance: 10478.0
# best_rel_error_pct: 0.002100
# example_source_txt: examples/inventory/deepseek-chat_exponential_L2_c1_5_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_032217.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 279.2562629539049  # OPT_PARAM: {"initial": 279.2562629539049, "min": 100, "max": 500, "type": "float"}
    safety_stock = 69.25626295390241  # OPT_PARAM: {"initial": 69.25626295390241, "min": 20, "max": 150, "type": "float"}
    demand_smoothing = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 0.9, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Simple demand forecast using pipeline arrivals with smoothing
    if pipeline_orders:
        # Use weighted average of pipeline orders as demand indicator
        # More weight to recent arrivals
        weights = [0.6, 0.4] if len(pipeline_orders) > 1 else [1.0]
        weighted_sum = sum(w * p for w, p in zip(weights, pipeline_orders[:len(weights)]))
        avg_weight = sum(weights[:len(pipeline_orders)])
        forecast_demand = weighted_sum / avg_weight if avg_weight > 0 else 0
    else:
        forecast_demand = 0

    # Apply smoothing to forecast
    smoothed_forecast = forecast_demand * demand_smoothing

    # Adjust base stock level
    adjusted_base_stock = base_stock + safety_stock + smoothed_forecast

    # Calculate order amount
    order_amount = max(0, adjusted_base_stock - inventory_position)

    # Apply order smoothing to prevent extreme fluctuations
    max_order_jump = 129.6814182422074  # OPT_PARAM: {"initial": 129.6814182422074, "min": 50, "max": 300, "type": "float"}
    smoothing_factor = 0.3  # OPT_PARAM: {"initial": 0.3, "min": 0.3, "max": 0.9, "type": "float"}

    if order_amount > max_order_jump:
        order_amount = max_order_jump + (order_amount - max_order_jump) * smoothing_factor

    # Round to nearest integer
    order_amount = int(round(order_amount))

    return order_amount
