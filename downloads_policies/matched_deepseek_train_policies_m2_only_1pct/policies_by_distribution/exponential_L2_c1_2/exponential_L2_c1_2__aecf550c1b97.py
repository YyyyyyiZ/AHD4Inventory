# policy_hash: aecf550c1b97ad402cb8916e7d2030f0cb638f0ebf4f20ab853b1a201a3f7cf1
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L2_c1_2
# matched_train_cells: 11
# source_prompt_files: 1
# best_target_performance: 5926.24
# best_prompt_performance: 5926.54
# best_rel_error_pct: 0.005062
# example_source_txt: examples/inventory/deepseek-chat_exponential_L2_c1_2_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251218_065351.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 213.06959886515898  # OPT_PARAM: {"initial": 213.06959886515898, "min": 100, "max": 300, "type": "float"}
    safety_stock = 53.06959886515772  # OPT_PARAM: {"initial": 53.06959886515772, "min": 10, "max": 80, "type": "float"}
    demand_forecast_factor = 0.5297879690843647  # OPT_PARAM: {"initial": 0.5297879690843647, "min": 0.5, "max": 1.5, "type": "float"}
    pipeline_weight = 0.3  # OPT_PARAM: {"initial": 0.3, "min": 0.0, "max": 0.8, "type": "float"}
    order_smoothing = 0.4313447170407435  # OPT_PARAM: {"initial": 0.4313447170407435, "min": 0.3, "max": 1.0, "type": "float"}
    lost_sales_penalty_factor = 0.9131798382427223  # OPT_PARAM: {"initial": 0.9131798382427223, "min": 0.8, "max": 2.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate demand forecast using weighted average of pipeline arrivals
    if len(pipeline_orders) > 0:
        weights = [pipeline_weight ** i for i in range(len(pipeline_orders))]
        weighted_sum = sum(p * w for p, w in zip(reversed(pipeline_orders), weights))
        total_weight = sum(weights)
        recent_demand_estimate = weighted_sum / total_weight if total_weight > 0 else 0
    else:
        recent_demand_estimate = 0

    # Adjust base stock with asymmetric penalty for lost sales
    adjusted_base_stock = base_stock + safety_stock + demand_forecast_factor * recent_demand_estimate

    # Increase target when facing potential lost sales (p > h)
    if inventory_position < adjusted_base_stock * 0.7:
        adjusted_base_stock *= lost_sales_penalty_factor

    # Calculate raw order
    raw_order = max(0, adjusted_base_stock - inventory_position)

    # Apply stronger smoothing to prevent over-ordering
    smoothed_order = order_smoothing * raw_order

    # Round to nearest integer
    order_amount = int(round(smoothed_order))

    return order_amount
