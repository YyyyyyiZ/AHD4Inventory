# policy_hash: 4015933e8f47c2f61dff1b7912894878f95d23c4ab9666987c9c030f1778ab2c
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L2_c1_2
# matched_train_cells: 11
# source_prompt_files: 1
# best_target_performance: 6163.34
# best_prompt_performance: 6163.34
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L2_c1_2_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251218_065015.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 206.58028900325795  # OPT_PARAM: {"initial": 206.58028900325795, "min": 100, "max": 400, "type": "float"}
    safety_stock = 9.688754321783899  # OPT_PARAM: {"initial": 9.688754321783899, "min": 0, "max": 100, "type": "float"}
    demand_forecast_factor = 0.0  # OPT_PARAM: {"initial": 0.0, "min": 0.0, "max": 2.0, "type": "float"}
    pipeline_weight = 0.7  # OPT_PARAM: {"initial": 0.7, "min": 0.0, "max": 1.0, "type": "float"}
    order_smoothing = 0.4  # OPT_PARAM: {"initial": 0.4, "min": 0.0, "max": 1.0, "type": "float"}
    lost_sales_penalty_factor = 0.6295072148878043  # OPT_PARAM: {"initial": 0.6295072148878043, "min": 0.5, "max": 2.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate demand forecast using weighted average of pipeline arrivals
    if len(pipeline_orders) > 0:
        # Give more weight to recent pipeline orders
        weights = [pipeline_weight ** i for i in range(len(pipeline_orders))]
        weighted_sum = sum(p * w for p, w in zip(reversed(pipeline_orders), weights))
        total_weight = sum(weights)
        recent_demand_estimate = weighted_sum / total_weight if total_weight > 0 else 0
    else:
        recent_demand_estimate = 0

    # Adjust base stock dynamically based on demand forecast and lost sales penalty
    adjusted_base_stock = base_stock + safety_stock + demand_forecast_factor * recent_demand_estimate

    # Apply lost sales penalty factor to increase base stock when inventory is low
    if on_hand_inventory < safety_stock:
        adjusted_base_stock *= lost_sales_penalty_factor

    # Calculate raw order
    raw_order = max(0, adjusted_base_stock - inventory_position)

    # Apply order smoothing to reduce volatility
    smoothed_order = order_smoothing * raw_order + (1 - order_smoothing) * max(0, adjusted_base_stock - inventory_position)

    # Round to nearest integer
    order_amount = int(round(smoothed_order))

    return order_amount
